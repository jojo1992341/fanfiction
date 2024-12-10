"""Utilities for processing and validating EPUB content."""
import logging
from typing import Optional
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class ContentProcessor:
    def __init__(self):
        self.min_content_length = 50  # Minimum characters for valid content
        self.min_text_ratio = 0.1     # Minimum ratio of text to HTML

    def is_valid_content(self, content: str) -> bool:
        """
        Check if content is valid and contains meaningful text.
        
        Args:
            content: HTML content string
            
        Returns:
            bool: True if content is valid, False otherwise
        """
        if not content or not content.strip():
            logger.debug("Content is empty")
            return False

        # Check content length
        if len(content) < self.min_content_length:
            logger.debug(f"Content too short: {len(content)} chars")
            return False

        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Get text content
            text = soup.get_text(strip=True)
            if not text:
                logger.debug("No text content found")
                return False

            # Check text to HTML ratio
            text_ratio = len(text) / len(content)
            if text_ratio < self.min_text_ratio:
                logger.debug(f"Text ratio too low: {text_ratio:.2f}")
                return False

            # Check for basic HTML structure
            if not soup.find(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                logger.debug("No content structure found")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating content: {str(e)}")
            return False

    def clean_content(self, content: str) -> Optional[str]:
        """
        Clean and normalize HTML content.
        
        Args:
            content: HTML content string
            
        Returns:
            Optional[str]: Cleaned content or None if invalid
        """
        if not content or not content.strip():
            return None

        try:
            # Remove excessive whitespace
            content = re.sub(r'\s+', ' ', content)
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove empty tags
            for tag in soup.find_all():
                if len(tag.get_text(strip=True)) == 0:
                    tag.decompose()

            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text):
                comment.extract()

            # Remove script and style tags
            for tag in soup.find_all(['script', 'style']):
                tag.decompose()

            cleaned = str(soup)
            return cleaned if self.is_valid_content(cleaned) else None

        except Exception as e:
            logger.error(f"Error cleaning content: {str(e)}")
            return None

    def extract_text_blocks(self, content: str) -> list[str]:
        """
        Extract meaningful text blocks from HTML content.
        
        Args:
            content: HTML content string
            
        Returns:
            list[str]: List of text blocks
        """
        if not content:
            return []

        try:
            soup = BeautifulSoup(content, 'html.parser')
            blocks = []

            for tag in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = tag.get_text(strip=True)
                if text and len(text) > 10:  # Minimum length for a text block
                    blocks.append(text)

            return blocks

        except Exception as e:
            logger.error(f"Error extracting text blocks: {str(e)}")
            return []
