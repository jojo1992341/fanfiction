"""Service for validating translations."""
import logging
from typing import List, Optional
from bs4 import BeautifulSoup
import re
from utils.content_processor import ContentProcessor

logger = logging.getLogger(__name__)

class TranslationValidator:
    def __init__(self):
        self.content_processor = ContentProcessor()
        self.min_ratio = 0.3
        self.max_ratio = 3.0
        self.min_block_similarity = 0.5

    def validate_translation(self, original: str, translated: str) -> bool:
        """
        Validate if translation appears reasonable.
        
        Args:
            original: Original HTML content
            translated: Translated HTML content
            
        Returns:
            bool: True if translation appears valid
        """
        if not self._validate_basic_requirements(original, translated):
            return False

        if not self._validate_length_ratio(original, translated):
            return False

        if not self._validate_structure(original, translated):
            return False

        if not self._validate_content_blocks(original, translated):
            return False

        return True

    def _validate_basic_requirements(self, original: str, translated: str) -> bool:
        """Check basic content requirements."""
        if not original or not translated:
            logger.warning("Empty content in translation validation")
            return False

        if not self.content_processor.is_valid_content(original):
            logger.warning("Invalid original content")
            return False

        if not self.content_processor.is_valid_content(translated):
            logger.warning("Invalid translated content")
            return False

        return True

    def _validate_length_ratio(self, original: str, translated: str) -> bool:
        """Validate the length ratio between original and translated text."""
        orig_text = BeautifulSoup(original, 'html.parser').get_text(strip=True)
        trans_text = BeautifulSoup(translated, 'html.parser').get_text(strip=True)

        if not orig_text or not trans_text:
            return False

        ratio = len(trans_text) / len(orig_text)
        if ratio < self.min_ratio or ratio > self.max_ratio:
            logger.warning(f"Translation length ratio ({ratio:.2f}) outside acceptable range")
            return False

        return True

    def _validate_structure(self, original: str, translated: str) -> bool:
        """Validate HTML structure similarity."""
        orig_soup = BeautifulSoup(original, 'html.parser')
        trans_soup = BeautifulSoup(translated, 'html.parser')

        orig_tags = [tag.name for tag in orig_soup.find_all()]
        trans_tags = [tag.name for tag in trans_soup.find_all()]

        if len(orig_tags) == 0 or len(trans_tags) == 0:
            logger.warning("Missing HTML structure in content")
            return False

        # Allow some flexibility in structure
        orig_count = len(orig_tags)
        trans_count = len(trans_tags)
        ratio = min(orig_count, trans_count) / max(orig_count, trans_count)

        if ratio < self.min_block_similarity:
            logger.warning(f"Structure similarity too low: {ratio:.2f}")
            return False

        return True

    def _validate_content_blocks(self, original: str, translated: str) -> bool:
        """Validate content blocks between original and translation."""
        orig_blocks = self.content_processor.extract_text_blocks(original)
        trans_blocks = self.content_processor.extract_text_blocks(translated)

        if not orig_blocks or not trans_blocks:
            logger.warning("No content blocks found")
            return False

        # Compare number of blocks with some flexibility
        orig_count = len(orig_blocks)
        trans_count = len(trans_blocks)
        ratio = min(orig_count, trans_count) / max(orig_count, trans_count)

        if ratio < self.min_block_similarity:
            logger.warning(f"Content block count mismatch: {orig_count} vs {trans_count}")
            return False

        return True
