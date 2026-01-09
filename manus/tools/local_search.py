"""Simple local search tool built from bundled snippets."""

from __future__ import annotations

import json
import math
from collections import Counter
from importlib import resources
from pathlib import Path
from typing import Any, Dict

from .base import Tool, ToolInput, ToolOutput

class LocalSearchTool:
    name = "search"
    description = "基于 seed_documents.json 的关键字检索工具"

    def __init__(self, *, data_path: Path | None = None, top_k: int = 3):
        if data_path:
            with open(data_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        else:
            with resources.files("manus.data").joinpath("seed_documents.json").open(
                "r", encoding="utf-8"
            ) as f:
                raw = json.load(f)
        self.documents: list[Dict[str, Any]] = raw
        self.top_k = top_k

    async def arun(self, tool_input: ToolInput) -> ToolOutput:
        query_terms = _normalize(tool_input.task)
        scored = []
        for doc in self.documents:
            text = doc["text"]
            terms = _normalize(text)
            score = _score(query_terms, terms)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        top_docs = scored[: self.top_k]
        if not top_docs:
            return ToolOutput(content="未找到匹配结果", metadata={"results": []})
        summary_lines = []
        payload = []
        for score, doc in top_docs:
            summary_lines.append(f"- ({score:.2f}) {doc['title']}: {doc['text'][:160]}...")
            payload.append({"title": doc["title"], "score": score, "source": doc.get("source")})
        return ToolOutput(content="\n".join(summary_lines), metadata={"results": payload})

def _normalize(text: str) -> Counter:
    tokens = [token.lower() for token in text.split() if token]
    return Counter(tokens)

def _score(query_terms: Counter, doc_terms: Counter) -> float:
    score = 0.0
    for term, weight in query_terms.items():
        freq = doc_terms.get(term, 0)
        if freq:
            score += (1 + math.log(freq)) * weight
    return score
