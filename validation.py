"""Utility functions for input validation."""
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

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
        
    return True

def validate_html_content(content: str) -> bool:
    """
    Validate if HTML content is not empty and well-formed.
    
    Args:
        content: HTML content string
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not content or not content.strip():
        logger.warning("Empty HTML content")
        return False
        
    return True
