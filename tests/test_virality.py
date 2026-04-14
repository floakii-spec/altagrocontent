import pytest
from src.analyzer.virality import calculate_virality_score


def test_basic_score():
    score = calculate_virality_score(likes=1000, comments=50, follower_count=10000)
    # (1000 + 50*2) / 10000 = 1100/10000 = 0.11
    assert round(score, 4) == 0.11


def test_score_clamped_to_one():
    score = calculate_virality_score(likes=9999, comments=9999, follower_count=100)
    assert score == 1.0


def test_zero_followers_returns_zero():
    score = calculate_virality_score(likes=100, comments=10, follower_count=0)
    assert score == 0.0


def test_zero_engagement_returns_zero():
    score = calculate_virality_score(likes=0, comments=0, follower_count=5000)
    assert score == 0.0
