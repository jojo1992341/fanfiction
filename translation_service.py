"""Service for translating content."""
import logging
import requests
import time
from typing import List, Optional
from bs4 import BeautifulSoup
from config.settings import (
    DEFAULT_SOURCE_LANG,
    DEFAULT_TARGET_LANG,
    BATCH_SIZE,
    RATE_LIMIT_DELAY
)
from .translation_validator import TranslationValidator
from .translation_retry_handler import TranslationRetryHandler
from utils.content_processor import ContentProcessor

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(
        self,
        source_lang: str = DEFAULT_SOURCE_LANG,
        target_lang: str = DEFAULT_TARGET_LANG
    ):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.base_url = 'https://translate.googleapis.com/translate_a/single'
        self.validator = TranslationValidator()
        self.content_processor = ContentProcessor()
        self.retry_handler = TranslationRetryHandler()

    def translate_html_content(self, html_content: str) -> Optional[str]:
        """Translate HTML content while preserving structure."""
        if not html_content.strip():
            return None

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            translatable_elements = self._extract_translatable_elements(soup)
            
            for element, text in translatable_elements:
                translated_text = self.retry_handler.with_retry(self._translate_text)(text)
                if translated_text and translated_text != text:
                    element.string = translated_text

            translated_content = str(soup)
            
            # Validate translation
            if not self.validator.validate_translation(html_content, translated_content):
                logger.warning("Translation validation failed")
                return None

            return translated_content

        except Exception as e:
            logger.error(f"HTML translation error: {str(e)}")
            return None

    def _extract_translatable_elements(self, soup: BeautifulSoup) -> List[tuple]:
        """Extract elements that need translation."""
        translatable_tags = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'div', 'span'}
        elements = []

        for tag in soup.find_all():
            if tag.name in translatable_tags and tag.string:
                text = tag.string.strip()
                if text:
                    elements.append((tag, text))

        return elements

    def _translate_text(self, text: str) -> Optional[str]:
        """Translate a single text using Google Translate API."""
        if not text.strip():
            return None

        try:
            params = {
                'client': 'gtx',
                'sl': self.source_lang,
                'tl': self.target_lang,
                'dt': 't',
                'q': text
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            translated_text = ''.join(x[0] for x in result[0] if x[0])
            
            logger.debug(f"Translated: {text[:50]}... -> {translated_text[:50]}...")
            return translated_text

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise  # Re-raise for retry handler

    def translate_batch(
        self,
        texts: List[str],
        batch_size: int = BATCH_SIZE,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """Translate a batch of texts with rate limiting and progress tracking."""
        translated_texts = []
        total_texts = len(texts)

        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            translated_batch = []

            for text in batch:
                translated_text = (
                    self.translate_html_content(text)
                    if self._is_html_content(text)
                    else self.retry_handler.with_retry(self._translate_text)(text)
                )
                translated_batch.append(translated_text or text)

            translated_texts.extend(translated_batch)

            if progress_callback:
                progress = min(100, (i + batch_size) * 100 // total_texts)
                progress_callback(progress)

            time.sleep(RATE_LIMIT_DELAY)

        return translated_texts

    @staticmethod
    def _is_html_content(text: str) -> bool:
        """Check if the text contains HTML markup."""
        return bool(BeautifulSoup(text, 'html.parser').find())
