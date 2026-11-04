from types import SimpleNamespace

import yuxi.modules.models.embed as embed_module
from yuxi.modules.knowledge.chunking.ragflow_like.parsers import semantic
from yuxi.modules.models.embed import BaseEmbeddingModel


class _RecordingEmbedding(BaseEmbeddingModel):
    """记录每次编码请求的输入条数，用于验证批量入口被使用。"""

    def __init__(self, batch_size: int):
        super().__init__(model="fake", batch_size=batch_size)
        self.requests: list[list[str]] = []

    def encode(self, message):
        messages = [message] if isinstance(message, str) else message
        self.requests.append(messages)
        return [[float(len(item)), 1.0] for item in messages]

    async def aencode(self, message):
        raise AssertionError("同步语义切分不应调用异步编码")


def test_empty_heading_preserves_current_title_context():
    markdown_content = """
## Parent Section

### Child Section

Content before empty heading.

###

Content after empty heading.
"""

    chunks = semantic.chunk_markdown(
        markdown_content,
        parser_config={"chunk_token_num": 512},
        embed_fn=lambda texts: texts,
    )

    assert len(chunks) == 1
    assert chunks[0].splitlines()[0] == "### Parent Section|Child Section"
    assert "Content before empty heading." in chunks[0]
    assert "Content after empty heading." in chunks[0]


def test_truncated_heading_token_stream_is_ignored(monkeypatch):
    markdown_parser = semantic.MarkdownIt("commonmark")
    monkeypatch.setattr(markdown_parser, "parse", lambda _: [SimpleNamespace(type="heading_open")])
    monkeypatch.setattr(semantic, "MarkdownIt", lambda _: markdown_parser)

    assert semantic.chunk_markdown("#", embed_fn=lambda texts: texts) == []


def test_semantic_chunking_sends_batches_of_configured_size(monkeypatch):
    """句子条数不受控，语义切分必须按模型 batch_size 分批，而不是整段一次请求。"""
    model = _RecordingEmbedding(batch_size=2)
    monkeypatch.setattr(embed_module, "select_embedding_model", lambda _spec: model)

    content = "".join(f"第{index}句说明这一段的内容。" for index in range(1, 8))
    semantic.chunk_markdown(content, {"chunk_token_num": 10, "embed_model_id": "fake"})

    assert model.requests
    assert [len(request) for request in model.requests] == [2, 2, 2, 1]
    assert sum(len(request) for request in model.requests) == 7
