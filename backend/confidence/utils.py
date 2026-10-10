"""Shared utilities for confidence scoring."""

from __future__ import annotations

import re

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return {token for token in tokens if token not in _STOP_WORDS}


def jaccard_similarity(left: str, right: str) -> float:
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def extract_years(text: str) -> set[str]:
    return set(re.findall(r"\b(?:1[0-9]{3}|20[0-9]{2})\b", text))


def extract_creator_names(text: str) -> set[str]:
    names: set[str] = set()
    for match in re.finditer(r"created by ([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})", text):
        names.add(match.group(1).strip().lower())
    for match in re.finditer(r"invented by ([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})", text):
        names.add(match.group(1).strip().lower())
    return names

