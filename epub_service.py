import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Optional
import logging
from utils.html_cleaner import HTMLCleaner

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EPUBService:
    def __init__(self, input_path: str):
        self.book = epub.read_epub(input_path)
        self.html_cleaner = HTMLCleaner()
        self.spine = []
        self.toc = []

    def extract_content(self) -> List[Tuple[str, str, int, str]]:
        """Extract text content, metadata and spine order from EPUB file."""
        contents = []
        
        # Create a mapping of item IDs to spine positions
        spine_order = {}
        for pos, (item_id, linear) in enumerate(self.book.spine):
            spine_order[item_id] = pos
        
        logger.debug(f"Spine order mapping: {spine_order}")
        
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    content = item.get_content().decode('utf-8')
                    file_name = item.get_name()
                    item_id = item.get_id()
                    
                    logger.debug(f"Processing file: {file_name}")
                    logger.debug(f"Content length: {len(content)}")
                    logger.debug(f"Item ID: {item_id}")
                    
                    # Store the spine position if available
                    spine_pos = spine_order.get(item_id, -1)
                    logger.debug(f"Spine position: {spine_pos}")
                    
                    contents.append((file_name, content, spine_pos, item_id))
                    
                except Exception as e:
                    logger.error(f"Error processing {item.get_name()}: {str(e)}")
                
        # Sort contents by spine position
        contents.sort(key=lambda x: x[2])
        return contents

    def copy_resources(self, new_book: epub.EpubBook):
        """Copy all non-HTML resources from original book to new book."""
        for item in self.book.get_items():
            if item.get_type() not in [ebooklib.ITEM_DOCUMENT, ebooklib.ITEM_NAVIGATION]:
                new_book.add_item(item)

    def copy_metadata(self, new_book: epub.EpubBook):
        """Copy metadata from original book to new book."""
        try:
            # Copy basic metadata
            if hasattr(self.book, 'title'):
                new_book.set_title(f"{self.book.title} (Traduit)")
            
            if hasattr(self.book, 'language'):
                new_book.set_language('fr')  # Set to French for translated version
            
            # Copy author information if available
            authors = self.book.get_metadata('DC', 'creator')
            if authors:
                for author in authors:
                    new_book.add_author(author[0])

            # Copy other DC metadata
            dc_items = ['publisher', 'identifier', 'source', 'rights', 'coverage', 'date']
            for item in dc_items:
                values = self.book.get_metadata('DC', item)
                if values:
                    for value in values:
                        new_book.add_metadata('DC', item, value[0])

            logger.debug("Metadata copied successfully")
        except Exception as e:
            logger.error(f"Error copying metadata: {str(e)}")

    def create_translated_epub(
        self,
        translated_contents: List[Tuple[str, str]],
        output_path: str
    ):
        """Create a new EPUB with translated content while preserving structure."""
        new_book = epub.EpubBook()
        logger.debug(f"Creating new EPUB at: {output_path}")

        # Copy metadata
        self.copy_metadata(new_book)

        # Copy resources (CSS, images, etc.)
        self.copy_resources(new_book)

        # Create spine and chapters
        chapters = []
        for file_name, content in translated_contents:
            logger.debug(f"Processing translated content for: {file_name}")
            logger.debug(f"Content length before cleaning: {len(content)}")
            
            # Clean and prepare content
            cleaned_content = self.html_cleaner.clean_for_kindle(content)
            logger.debug(f"Content length after cleaning: {len(cleaned_content)}")
            
            if not cleaned_content.strip():
                logger.warning(f"Empty content detected for {file_name}")
                continue

            # Create chapter
            chapter = epub.EpubHtml(
                title=file_name,
                file_name=file_name,
                content=cleaned_content,
                lang='fr'
            )
            
            # Copy properties from original item if they exist
            original_item = next(
                (item for item in self.book.get_items() 
                 if item.get_name() == file_name), None
            )
            
            if original_item:
                chapter.properties = original_item.properties
                chapter.media_type = original_item.media_type
                chapter.id = original_item.get_id()
                
            new_book.add_item(chapter)
            chapters.append(chapter)
            logger.debug(f"Added chapter: {file_name}")

        # Add default NCX and Nav file
        nav = epub.EpubNav()
        nav.content = self.html_cleaner.clean_for_kindle(nav.content)
        new_book.add_item(nav)
        new_book.add_item(epub.EpubNcx())

        # Recreate spine
        new_book.spine = ['nav'] + [(chapter.id, True) for chapter in chapters]
        logger.debug(f"Spine length: {len(new_book.spine)}")

        # Create table of contents
        original_toc = self.book.toc
        if original_toc:
            new_book.toc = original_toc
            logger.debug(f"TOC length: {len(new_book.toc)}")

        # Write the EPUB file
        try:
            epub.write_epub(output_path, new_book, {})
            logger.debug("Successfully wrote EPUB file")
        except Exception as e:
            logger.error(f"Error writing EPUB: {str(e)}")
            raise
