def confidence_from_scores(scores: list[float]) -> str:
    if not scores:
        return "Low"
    best = max(scores)
    # Inner product over normalized vectors ~ cosine sim
    if best >= 0.55:
        return "High"
    if best >= 0.40:
        return "Medium"
    return "Low"
