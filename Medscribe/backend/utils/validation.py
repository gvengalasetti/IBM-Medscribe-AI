from typing import Dict, List, Any
from .text_index import jaccard_similarity


def _best_support_score(text: str, citations: List[int], id_to_sentence: Dict[int, str]) -> float:
    scores = []
    for cid in citations or []:
        src = id_to_sentence.get(int(cid), "")
        if src:
            scores.append(jaccard_similarity(text, src))
    return max(scores) if scores else 0.0


def validate_outputs(
    payload: Dict[str, Any],
    id_to_sentence: Dict[int, str],
    threshold: float = 0.30,
) -> Dict[str, Any]:
    out = {
        "summary_bullets": [],
        "suggested_orders": [],
        "id_to_sentence": id_to_sentence,
        "model_info": payload.get("model_info") or {},
    }

    for b in payload.get("summary_bullets") or []:
        txt = (b or {}).get("text", "")
        cits = (b or {}).get("citations") or []
        score = _best_support_score(txt, cits, id_to_sentence)
        if score >= threshold:
            out["summary_bullets"].append({
                "text": txt,
                "citations": [int(c) for c in cits if int(c) in id_to_sentence],
                "support_score": score,
            })

    for o in payload.get("suggested_orders") or []:
        name = (o or {}).get("name", "")
        reason = (o or {}).get("reason", "")
        cits = (o or {}).get("citations") or []
        score = _best_support_score(f"{name} {reason}".strip(), cits, id_to_sentence)
        if score >= threshold:
            item = {
                "type": (o or {}).get("type"),
                "name": name,
                "reason": reason,
                "citations": [int(c) for c in cits if int(c) in id_to_sentence],
                "support_score": score,
                "confidence": float((o or {}).get("confidence", 0.0)),
            }
            ext = (o or {}).get("external_citations") or []
            if ext:
                item["external_citations"] = ext
            out["suggested_orders"].append(item)

    return out


