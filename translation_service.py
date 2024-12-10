from typing import List, Optional
import requests
import time
import logging
from bs4 import BeautifulSoup
from config.settings import (
    DEFAULT_SOURCE_LANG,
    DEFAULT_TARGET_LANG,
    BATCH_SIZE,
    RATE_LIMIT_DELAY
)

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

    def extract_text_from_html(self, html_content: str) -> List[tuple[str, str]]:
        """Extract translatable text from HTML while preserving structure."""
        soup = BeautifulSoup(html_content, 'html.parser')
        translatable_elements = []
        
        # Define tags whose content should be translated
        translatable_tags = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'div', 'span'}
        
        for tag in soup.find_all():
            if tag.name in translatable_tags and tag.string:
                text = tag.string.strip()
                if text:
                    translatable_elements.append((str(tag), text))
                    
        return translatable_elements

    def translate_text(self, text: str) -> str:
        """Translate a single text using Google Translate API."""
        if not text.strip():
            return text

        params = {
            'client': 'gtx',
            'sl': self.source_lang,
            'tl': self.target_lang,
            'dt': 't',
            'q': text
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            result = response.json()
            translated_text = ''.join(x[0] for x in result[0] if x[0])
            logger.debug(f"Translated: {text[:50]}... -> {translated_text[:50]}...")
            return translated_text
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text

    def translate_html_content(self, html_content: str) -> str:
        """Translate HTML content while preserving structure."""
        if not html_content.strip():
            return html_content
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            translatable_elements = self.extract_text_from_html(html_content)
            
            for original_tag, text in translatable_elements:
                translated_text = self.translate_text(text)
                if translated_text != text:
                    # Create a new tag with translated content
                    new_tag = BeautifulSoup(original_tag, 'html.parser')
                    new_tag.string = translated_text
                    # Replace the original tag in the soup
                    old_tag = soup.find(string=text)
                    if old_tag:
                        old_tag.replace_with(translated_text)
                        
            return str(soup)
            
        except Exception as e:
            logger.error(f"HTML translation error: {str(e)}")
            return html_content

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
                if self.is_html_content(text):
                    translated_text = self.translate_html_content(text)
                else:
                    translated_text = self.translate_text(text)
                translated_batch.append(translated_text)
                
            translated_texts.extend(translated_batch)

            if progress_callback:
                progress = min(100, (i + batch_size) * 100 // total_texts)
                progress_callback(progress)

            time.sleep(RATE_LIMIT_DELAY)

        return translated_texts

    @staticmethod
    def is_html_content(text: str) -> bool:
        """Check if the text contains HTML markup."""
        return bool(BeautifulSoup(text, 'html.parser').find())
