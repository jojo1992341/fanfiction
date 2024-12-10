"""Utility functions for input validation."""
import os
import logging
from typing import List
from .content_processor import ContentProcessor

logger = logging.getLogger(__name__)
content_processor = ContentProcessor()

def validate_epub_file(file_path: str) -> bool:
    """
    Validate if a file is a valid EPUB file.
    
    Args:
        file_path: Path to the EPUB file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
        
    if not file_path.lower().endswith('.epub'):
        logger.error(f"Not an EPUB file: {file_path}")
        return False
        
    if os.path.getsize(file_path) == 0:
        logger.error(f"Empty file: {file_path}")
        return False
        
    # Check file size is reasonable (between 10KB and 2GB)
    size = os.path.getsize(file_path)
    if size < 10 * 1024 or size > 2 * 1024 * 1024 * 1024:
        logger.error(f"Invalid file size: {size} bytes")
        return False
        
    return True

def validate_html_content(content: str) -> bool:
    """
    Validate if HTML content is not empty and well-formed.
    
    Args:
        content: HTML content string
        
    Returns:
        bool: True if valid, False otherwise
    """
    return content_processor.is_valid_content(content)

def validate_translation(original: str, translated: str) -> bool:
    """
    Validate if translation appears reasonable.
    
    Args:
        original: Original text
        translated: Translated text
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not original or not translated:
        return False
        
    # Check if lengths are reasonably proportional
    orig_len = len(original)
    trans_len = len(translated)
    ratio = trans_len / orig_len if orig_len > 0 else 0
    
    if ratio < 0.3 or ratio > 3.0:
        logger.warning(f"Suspicious translation length ratio: {ratio:.2f}")
        return False
        
    # Check if both have some common structure
    orig_blocks = content_processor.extract_text_blocks(original)
    trans_blocks = content_processor.extract_text_blocks(translated)
    
    if len(orig_blocks) != len(trans_blocks):
        logger.warning("Mismatch in number of text blocks")
        return False
        
    return True
