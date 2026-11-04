# 语义切分按模型配置批量编码

状态：implemented
类型：bug-fix
Owner：backend/yuxi/modules/knowledge/chunking/ragflow_like/parsers/semantic.py

## 问题

语义切分把模型的裸 `encode` 绑成 `embed_fn`：

```python
embed_fn = select_embedding_model(embed_model_id).encode
```

`semantic_utils.semantic_chunking_with_auto_clusters` 随后执行 `embed_fn(sentences)`，把一段超长正文分出的全部句子放进一次 HTTP 请求。`batch_size` 只在 `batch_encode` / `abatch_encode` 内生效，因此模型配置的批量大小在这条路径上完全不生效。

Alibaba DashScope `text-embedding-v4` 单次最多 10 条输入。文件 `file_7331443764534341b1297b4b16115309` 的语义切分分出 11 句，请求返回 400 `batch size is invalid, it should not be larger than 10`。400 不在模型层重试状态码内，异常直接冒泡为 `ValueError`，文件进入 `ERROR_INDEXING`。同一文件的入库向量化走 `get_embedding_function` → `abatch_encode`，不受影响，说明缺陷只在切分路径。

## 决策

### 实现方案

`semantic.py` 改为绑定 `select_embedding_model(embed_model_id).batch_encode`。`embed_fn` 的契约不变（句子列表 → 每条一个向量），但请求按模型配置的 `batch_size` 分组发出；`batch_encode` 已有的条数与维度校验继续生效。

模型配置仍是批量大小的唯一 Owner，切分路径不重复读取或写死供应商上限。供应商上限（DashScope `text-embedding-v4` 为 10）与部署配置是两个事实：当前部署 `alibaba-cn:text-embedding-v4` 的 `batch_size=2`，由管理员在模型配置中保存。

切分是同步 CPU + 同步 HTTP 的工作，入口 `MilvusKB._index_file` 运行在 worker 事件循环中。分组后每次语义聚类调用的请求数变为 `ceil(句子数 / batch_size)`，阻塞时长随文档长度增长；worker 的 lease 心跳（30 秒租约、10 秒心跳）是同一事件循环上的 `asyncio.Task`，长时间阻塞会导致租约丢失。因此该调用点改为 `await await_io(asyncio.to_thread(self._split_text_into_chunks, ...))`，与同文件创建 Milvus 集合的既有做法一致；代价是取消与超时需要等当前这次切分结束后才生效。

## 替代方案

- 在 `OtherEmbedding` 收到 400 时自动对半拆分重试：把供应商上限探测写进通用模型层，增加重试状态与失败面，且对非批量原因的 400 无效。
- 在切分路径把句子数硬截断到固定上限：又把供应商约束写死在业务代码里，模型配置失去意义。
- 在 `semantic_utils` 内部分批：切分工具只应消费 `embed_fn` 契约，批量策略属于模型层。
- 把切分留在事件循环中、只在记录里声明风险：长文档的批请求会让心跳无法按时续租，修复目标文件（168,754 字符）仍可能以「租约丢失」失败。

## 后果

切分路径的请求次数随句子数增加，单次请求输入条数不超过配置值；超限配置仍会失败，但失败原因从「代码忽略配置」变为「配置超出供应商限制」，属于可观察、可配置的业务事实。

内置供应商模板中 `alibaba-cn` 的 `text-embedding-v4` 未声明 `batch_size`，新建或回填该供应商的部署会回落到默认 40，超过 DashScope 的 10 条上限，仍有同样的 400 风险。本变更不修改内置模板：已有部署需要管理员显式配置，新建部署的默认值属于独立的配置决策。

`embed_fn` 由调用方注入时（单测、外部集成）行为不变，注入方自行负责批量语义。

## 验证

`backend/test/unit/knowledge/chunking/test_semantic_chunking.py::test_semantic_chunking_sends_batches_of_configured_size`：用 `batch_size=2` 的真实 `BaseEmbeddingModel` 子类记录每次编码的输入条数，7 句必须被拆成 `[2, 2, 2, 1]`，总数覆盖全部句子。把绑定改回 `.encode` 时该用例失败（单次 7 条），恢复后通过。

`test_semantic_tables.py` 中两个只暴露 `encode` 的 fake 模型同步改为 `batch_encode`，继续证明表格行不会被送入聚类。

实际执行：

```bash
docker compose exec api uv run --no-sync --group test pytest test/unit -m "not slow"
python3 scripts/ci/verify_engineering_contracts.py
python3 -m unittest scripts.ci.test_verify_engineering_contracts
(cd docs && pnpm build)
```

结果为 3609 passed / 127 skipped、工程契约检查通过、56 项契约测试通过、文档构建成功；后端 ruff check、format 与 import 排序通过。

未验证：真实 DashScope 请求、聚类质量，以及线程卸载后 worker 心跳在超长文档上的实际表现；上述链路由部署方在重启 worker 后对真实文件回读终态确认。
