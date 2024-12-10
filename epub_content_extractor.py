"""Service for extracting content from EPUB files."""
import logging
from typing import List, Tuple, Optional
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from utils.validation import validate_html_content

logger = logging.getLogger(__name__)

class EPUBContentExtractor:
    def __init__(self, book: epub.EpubBook):
        self.book = book
        
    def extract_content(self) -> List[Tuple[str, str, int, str]]:
        """
        Extract text content, metadata and spine order from EPUB file.
        
        Returns:
            List of tuples containing (file_name, content, spine_position, item_id)
        """
        contents = []
        spine_order = self._create_spine_mapping()
        
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content_tuple = self._process_item(item, spine_order)
                if content_tuple:
                    contents.append(content_tuple)
                    
        # Sort contents by spine position
        contents.sort(key=lambda x: x[2])
        
        if not contents:
            logger.warning("No valid content found in EPUB")
            
        return contents
        
    def _create_spine_mapping(self) -> dict:
        """Create a mapping of item IDs to spine positions."""
        spine_order = {}
        for pos, (item_id, linear) in enumerate(self.book.spine):
            spine_order[item_id] = pos
            logger.debug(f"Mapped item {item_id} to spine position {pos}")
        return spine_order
        
    def _process_item(
        self, 
        item: epub.EpubItem, 
        spine_order: dict
    ) -> Optional[Tuple[str, str, int, str]]:
        """Process a single EPUB item and extract its content."""
        try:
            content = item.get_content().decode('utf-8')
            if not validate_html_content(content):
                logger.warning(f"Empty content in {item.get_name()}")
                return None
                
            file_name = item.get_name()
            item_id = item.get_id()
            spine_pos = spine_order.get(item_id, -1)
            
            logger.debug(f"Processed {file_name} (ID: {item_id}, Spine: {spine_pos})")
            return (file_name, content, spine_pos, item_id)
            
        except Exception as e:
            logger.error(f"Error processing {item.get_name()}: {str(e)}")
            return None
