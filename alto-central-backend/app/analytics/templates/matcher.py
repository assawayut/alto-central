"""Template matching logic for natural language prompts.

Matches user prompts to available chart templates using
phrase matching and keyword analysis.
"""

import logging
import re
from typing import List, Optional, Tuple

from app.analytics.templates.manager import get_template_manager
from app.analytics.templates.schema import ChartTemplate

logger = logging.getLogger(__name__)


class TemplateMatcher:
    """Match user prompts to chart templates."""

    def __init__(self):
        self._manager = get_template_manager()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        # Lowercase
        text = text.lower()
        # Remove punctuation except hyphens
        text = re.sub(r"[^\w\s-]", "", text)
        # Normalize whitespace
        text = " ".join(text.split())
        return text

    def _calculate_phrase_match(
        self, prompt: str, trigger_phrases: List[str]
    ) -> float:
        """Calculate match score based on trigger phrases.

        Returns score between 0 and 1.
        """
        if not trigger_phrases:
            return 0.0

        prompt_normalized = self._normalize_text(prompt)
        max_score = 0.0

        for phrase in trigger_phrases:
            phrase_normalized = self._normalize_text(phrase)

            # Check for exact substring match
            if phrase_normalized in prompt_normalized:
                # Score based on how much of the prompt the phrase covers
                coverage = len(phrase_normalized) / len(prompt_normalized)
                score = 0.5 + (coverage * 0.5)  # Base 0.5 for match, up to 1.0
                max_score = max(max_score, score)

            # Check for word overlap
            else:
                phrase_words = set(phrase_normalized.split())
                prompt_words = set(prompt_normalized.split())
                overlap = phrase_words & prompt_words

                if overlap:
                    # Score based on percentage of phrase words matched
                    match_ratio = len(overlap) / len(phrase_words)
                    score = match_ratio * 0.6  # Max 0.6 for partial match
                    max_score = max(max_score, score)

        return max_score

    def _check_required_keywords(
        self, prompt: str, required_groups: List[List[str]]
    ) -> bool:
        """Check if prompt contains at least one keyword from each group."""
        if not required_groups:
            return True

        prompt_normalized = self._normalize_text(prompt)
        prompt_words = set(prompt_normalized.split())

        for group in required_groups:
            group_normalized = [self._normalize_text(kw) for kw in group]
            if not any(kw in prompt_words or kw in prompt_normalized for kw in group_normalized):
                return False

        return True

    def _check_excluded_keywords(
        self, prompt: str, excluded: List[str]
    ) -> bool:
        """Check if prompt contains any excluded keywords."""
        if not excluded:
            return False

        prompt_normalized = self._normalize_text(prompt)
        prompt_words = set(prompt_normalized.split())

        for keyword in excluded:
            kw_normalized = self._normalize_text(keyword)
            if kw_normalized in prompt_words or kw_normalized in prompt_normalized:
                return True

        return False

    def find_match(
        self,
        prompt: str,
        site_id: Optional[str] = None,
        min_confidence: float = 0.7,
    ) -> Optional[Tuple[ChartTemplate, float]]:
        """Find the best matching template for a prompt.

        Args:
            prompt: User's natural language prompt
            site_id: Optional site ID for custom templates
            min_confidence: Minimum confidence threshold

        Returns:
            Tuple of (template, confidence) if match found, None otherwise
        """
        logger.info(f"[MATCHER] Finding match for prompt: '{prompt}'")
        logger.info(f"[MATCHER] Site ID: {site_id}, min_confidence: {min_confidence}")

        templates = self._manager.load_all_templates()
        logger.info(f"[MATCHER] Loaded {len(templates)} templates")

        best_match: Optional[ChartTemplate] = None
        best_score = 0.0

        for cache_key, template in templates.items():
            matching = template.matching
            logger.debug(f"[MATCHER] Checking template: {template.template_id}")

            # Skip if excluded keywords are present
            if self._check_excluded_keywords(prompt, matching.excluded_keywords):
                logger.debug(f"[MATCHER] {template.template_id}: excluded by keywords")
                continue

            # Check required keywords
            if not self._check_required_keywords(prompt, matching.required_keywords):
                logger.debug(f"[MATCHER] {template.template_id}: missing required keywords")
                continue

            # Calculate phrase match score
            score = self._calculate_phrase_match(prompt, matching.trigger_phrases)
            logger.info(f"[MATCHER] {template.template_id}: score={score:.2f} (threshold={matching.confidence_threshold})")

            # Apply template-specific threshold
            if score < matching.confidence_threshold:
                logger.debug(f"[MATCHER] {template.template_id}: below threshold")
                continue

            # Prefer site-specific templates
            if ":" in cache_key:
                key_site = cache_key.split(":")[0]
                if key_site == site_id:
                    score += 0.1  # Boost for site-specific match
                    logger.debug(f"[MATCHER] {template.template_id}: site boost applied")

            if score > best_score:
                best_score = score
                best_match = template
                logger.info(f"[MATCHER] New best match: {template.template_id} with score {score:.2f}")

        if best_match and best_score >= min_confidence:
            logger.info(
                f"[MATCHER] Final match: '{best_match.template_id}' "
                f"with confidence {best_score:.2f}"
            )
            return (best_match, best_score)

        logger.info(f"[MATCHER] No template matched (best score: {best_score:.2f})")
        return None

    def find_all_matches(
        self,
        prompt: str,
        site_id: Optional[str] = None,
        min_confidence: float = 0.5,
        max_results: int = 5,
    ) -> List[Tuple[ChartTemplate, float]]:
        """Find all matching templates above threshold.

        Args:
            prompt: User's natural language prompt
            site_id: Optional site ID for custom templates
            min_confidence: Minimum confidence threshold
            max_results: Maximum number of results

        Returns:
            List of (template, confidence) tuples, sorted by confidence
        """
        templates = self._manager.load_all_templates()
        matches = []

        for cache_key, template in templates.items():
            matching = template.matching

            # Skip if excluded keywords are present
            if self._check_excluded_keywords(prompt, matching.excluded_keywords):
                continue

            # Check required keywords
            if not self._check_required_keywords(prompt, matching.required_keywords):
                continue

            # Calculate phrase match score
            score = self._calculate_phrase_match(prompt, matching.trigger_phrases)

            if score >= min_confidence:
                # Prefer site-specific templates
                if ":" in cache_key:
                    key_site = cache_key.split(":")[0]
                    if key_site == site_id:
                        score += 0.1

                matches.append((template, score))

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_results]


# Global singleton
_matcher: Optional[TemplateMatcher] = None


def get_template_matcher() -> TemplateMatcher:
    """Get the global template matcher instance."""
    global _matcher
    if _matcher is None:
        _matcher = TemplateMatcher()
    return _matcher
