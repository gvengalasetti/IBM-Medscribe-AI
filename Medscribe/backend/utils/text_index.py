import re
from typing import Dict, List, Tuple

_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')
_TOKEN = re.compile(r"[a-z0-9]+")


def split_into_sentences(text: str) -> List[Tuple[int, str]]:
    raw = [s.strip() for s in _SENT_SPLIT.split(text or "") if s.strip()]
    return [(i + 1, s) for i, s in enumerate(raw)]


def index_sentences(pairs: List[Tuple[int, str]]) -> Dict[int, str]:
    return {i: s for i, s in pairs}


def _tokenize(text: str) -> set:
    return set(_TOKEN.findall((text or "").lower()))


def jaccard_similarity(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


