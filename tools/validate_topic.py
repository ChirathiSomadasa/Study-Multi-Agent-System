"""
tools/validate_topic.py — Custom Python tool for the Coordinator Agent.

Author: Member 1

Purpose:
    Perform lightweight pre-validation of a study topic BEFORE calling the LLM.
    This prevents wasting inference calls on nonsense input and provides
    the LLM with a useful `category` hint to improve syllabus quality.

Design decisions:
    - Pure Python, no external API calls (offline-first per assignment constraints).
    - Category detection uses a keyword map rather than an LLM to keep this tool
      fast and deterministic — it must not depend on the LLM it feeds into.
    - Grade-level bounds are enforced here, not in the agent prompt, so the
      constraint is always applied regardless of prompt drift.
"""

import re
from typing import TypedDict


# Category keyword map
# Maps a broad academic category to trigger keywords.
# A topic is matched to the FIRST category whose keywords appear in the topic.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "biology": [
        "cell biology", "photosynthesis", "dna", "genetics", " evolution",
        "organism", "ecosystem", "respiration", "mitosis", "enzyme",
        "chloroplast", "chromosome", "natural selection",
    ],
    "chemistry": [
        "atom", "molecule", "reaction", "periodic", "bond", "acid",
        "base", "element", "compound", "oxidation",
    ],
    "physics": [
        "force", "motion", "energy", "wave", "light", "electric",
        "gravity", "momentum", "velocity", "thermodynamics",
    ],
    "mathematics": [
        "algebra", "geometry", "calculus", "trigonometry", "statistics",
        "probability", "matrix", "number", "equation", "function",
    ],
    "history": [
        "war", "revolution", "empire", "dynasty", "civilization",
        "colonial", "independence", "ancient", "medieval", "modern",
    ],
    "computer_science": [
        "algorithm", "data structure", "programming", "network",
        "database", "machine learning", "operating system", "binary",
        "recursion", "complexity",
    ],
    "literature": [
        "poem", "novel", "drama", "shakespeare", "prose", "metaphor",
        "narrative", "character", "theme", "symbolism",
    ],
    "geography": [
        "climate", "continent", "country", "map", "population",
        "migration", "landform", "weather", "biome", "urbanization",
    ],
}

# Topics that are clearly nonsensical or too vague
BLOCKED_PATTERNS: list[str] = [
    r"^\s*$",           # empty
    r"^[^a-zA-Z]+$",   # no letters at all
    r"^\W+$",           # only punctuation
]

# Minimum and maximum accepted topic string lengths
MIN_TOPIC_LEN = 3
MAX_TOPIC_LEN = 120


class ValidationResult(TypedDict):
    """Return type for validate_topic."""
    is_valid: bool
    reason: str
    category: str
    normalised_topic: str


def validate_topic(topic: str, grade_level: int = 10) -> ValidationResult:
    """
    Validate a study topic string and detect its academic category.

    This tool runs BEFORE the LLM is invoked. It enforces hard constraints so
    the Coordinator agent can fail fast on bad input rather than burning tokens.

    Args:
        topic:       Raw topic string provided by the user.
        grade_level: Target grade level (must be between 1 and 13 inclusive).

    Returns:
        ValidationResult with:
            is_valid (bool):         True if the topic passes all checks.
            reason (str):            Human-readable explanation (pass or fail).
            category (str):          Detected academic category, or "general"
                                     if no specific category is matched.
            normalised_topic (str):  Title-cased, stripped version of the topic.

    Raises:
        TypeError:  If topic is not a string.
        ValueError: If grade_level is outside the range [1, 13].

    Example:
        >>> result = validate_topic("Photosynthesis", grade_level=10)
        >>> result["is_valid"]
        True
        >>> result["category"]
        'biology'

        >>> result = validate_topic("   ", grade_level=10)
        >>> result["is_valid"]
        False
    """
    # Type check
    if not isinstance(topic, str):
        raise TypeError(f"topic must be a str, got {type(topic).__name__}")

    if not isinstance(grade_level, int) or not (1 <= grade_level <= 13):
        raise ValueError(f"grade_level must be an integer between 1 and 13, got {grade_level!r}")

    # Normalise 
    normalised = topic.strip().title()

    # Block-list checks 
    for pattern in BLOCKED_PATTERNS:
        if re.fullmatch(pattern, topic):
            return ValidationResult(
                is_valid=False,
                reason="Topic appears to be empty or contains no readable text.",
                category="unknown",
                normalised_topic=normalised,
            )

    # Length checks 
    if len(normalised) < MIN_TOPIC_LEN:
        return ValidationResult(
            is_valid=False,
            reason=f"Topic is too short (minimum {MIN_TOPIC_LEN} characters).",
            category="unknown",
            normalised_topic=normalised,
        )

    if len(normalised) > MAX_TOPIC_LEN:
        return ValidationResult(
            is_valid=False,
            reason=f"Topic is too long (maximum {MAX_TOPIC_LEN} characters).",
            category="unknown",
            normalised_topic=normalised,
        )

    # Category detection 
    lower = normalised.lower()
    detected_category = "general"
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            detected_category = category
            break

    return ValidationResult(
        is_valid=True,
        reason="Topic passed all validation checks.",
        category=detected_category,
        normalised_topic=normalised,
    )
