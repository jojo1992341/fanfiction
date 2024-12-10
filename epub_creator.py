"""Service for creating new EPUB files with translated content."""
import logging
from typing import List, Tuple, Optional
import ebooklib
from ebooklib import epub
from utils.validation import validate_html_content
from utils.html_cleaner import HTMLCleaner

logger = logging.getLogger(__name__)

class EPUBCreator:
    def __init__(self, original_book: epub.EpubBook):
        self.original_book = original_book
        self.html_cleaner = HTMLCleaner()
        
    def create_translated_epub(
        self,
        translated_contents: List[Tuple[str, str]],
        output_path: str
    ) -> None:
        """
        Create a new EPUB with translated content.
        
        Args:
            translated_contents: List of (file_name, content) tuples
            output_path: Path where to save the new EPUB
            
        Raises:
            ValueError: If translated_contents is empty
            RuntimeError: If EPUB creation fails
        """
        if not translated_contents:
            raise ValueError("No translated content provided")
            
        try:
            new_book = epub.EpubBook()
            self._copy_metadata(new_book)
            self._copy_resources(new_book)
            
            chapters = self._create_chapters(translated_contents)
            if not chapters:
                raise RuntimeError("Failed to create any valid chapters")
                
            self._setup_navigation(new_book, chapters)
            self._write_epub(new_book, output_path)
            
        except Exception as e:
            logger.error(f"Failed to create EPUB: {str(e)}")
            raise RuntimeError(f"EPUB creation failed: {str(e)}")
            
    def _copy_metadata(self, new_book: epub.EpubBook) -> None:
        """Copy metadata from original book to new book."""
        try:
            if hasattr(self.original_book, 'title'):
                new_book.set_title(f"{self.original_book.title} (Traduit)")
            
            if hasattr(self.original_book, 'language'):
                new_book.set_language('fr')
            
            authors = self.original_book.get_metadata('DC', 'creator')
            if authors:
                for author in authors:
                    new_book.add_author(author[0])
                    
            self._copy_dc_metadata(new_book)
            
        except Exception as e:
            logger.error(f"Error copying metadata: {str(e)}")
            
    def _copy_dc_metadata(self, new_book: epub.EpubBook) -> None:
        """Copy Dublin Core metadata."""
        dc_items = ['publisher', 'identifier', 'source', 'rights', 'coverage', 'date']
        for item in dc_items:
            values = self.original_book.get_metadata('DC', item)
            if values:
                for value in values:
                    new_book.add_metadata('DC', item, value[0])
                    
    def _copy_resources(self, new_book: epub.EpubBook) -> None:
        """Copy all non-HTML resources from original book."""
        for item in self.original_book.get_items():
            if item.get_type() not in [ebooklib.ITEM_DOCUMENT, ebooklib.ITEM_NAVIGATION]:
                new_book.add_item(item)
                
    def _create_chapters(
        self,
        translated_contents: List[Tuple[str, str]]
    ) -> List[epub.EpubHtml]:
        """Create chapters from translated content."""
        chapters = []
        for file_name, content in translated_contents:
            if not validate_html_content(content):
                logger.warning(f"Skipping empty content in {file_name}")
                continue
                
            cleaned_content = self.html_cleaner.clean_for_kindle(content)
            if not cleaned_content:
                continue
                
            chapter = self._create_chapter(file_name, cleaned_content)
            if chapter:
                chapters.append(chapter)
                
        return chapters
        
    def _create_chapter(
        self,
        file_name: str,
        content: str
    ) -> Optional[epub.EpubHtml]:
        """Create a single chapter."""
        try:
            chapter = epub.EpubHtml(
                title=file_name,
                file_name=file_name,
                content=content,
                lang='fr'
            )
            
            original_item = self._find_original_item(file_name)
            if original_item:
                chapter.properties = original_item.properties
                chapter.media_type = original_item.media_type
                chapter.id = original_item.get_id()
                
            return chapter
            
        except Exception as e:
            logger.error(f"Error creating chapter {file_name}: {str(e)}")
            return None
            
    def _find_original_item(self, file_name: str) -> Optional[epub.EpubItem]:
        """Find original item by file name."""
        return next(
            (item for item in self.original_book.get_items() 
             if item.get_name() == file_name),
            None
        )
        
    def _setup_navigation(
        self,
        new_book: epub.EpubBook,
        chapters: List[epub.EpubHtml]
    ) -> None:
        """Setup navigation for the new book."""
        for chapter in chapters:
            new_book.add_item(chapter)
            
        nav = epub.EpubNav()
        nav.content = self.html_cleaner.clean_for_kindle(nav.content)
        new_book.add_item(nav)
        new_book.add_item(epub.EpubNcx())
        
        new_book.spine = ['nav'] + [(chapter.id, True) for chapter in chapters]
        
        if self.original_book.toc:
            new_book.toc = self.original_book.toc
            
    def _write_epub(self, new_book: epub.EpubBook, output_path: str) -> None:
        """Write the EPUB file."""
        try:
            epub.write_epub(output_path, new_book, {})
            logger.info(f"Successfully wrote EPUB to {output_path}")
        except Exception as e:
            logger.error(f"Error writing EPUB: {str(e)}")
            raise
