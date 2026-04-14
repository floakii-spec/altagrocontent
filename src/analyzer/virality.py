def calculate_virality_score(likes: int, comments: int, follower_count: int) -> float:
    """Normaliza engajamento pelo número de seguidores. Retorna valor entre 0 e 1."""
    if follower_count == 0:
        return 0.0
    raw = (likes + comments * 2) / follower_count
    return min(raw, 1.0)
