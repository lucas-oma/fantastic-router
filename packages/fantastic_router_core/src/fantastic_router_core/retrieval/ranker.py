from typing import Sequence, Mapping

def rerank_candidates(query: str, candidates: Sequence[Mapping], tenant_id: str | None = None):
    # OSS default: no reranking
    return list(candidates)


# TODO: add enterprise-specific reranking