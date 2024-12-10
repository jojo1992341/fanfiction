"""Main EPUB service coordinating content extraction and creation."""
import logging
from typing import List, Tuple
import ebooklib
from ebooklib import epub
from .epub_content_extractor import EPUBContentExtractor
from .epub_creator import EPUBCreator

logger = logging.getLogger(__name__)

class EPUBService:
    def __init__(self, input_path: str):
        """
        Initialize EPUB service.
        
        Args:
            input_path: Path to input EPUB file
        """
        try:
            self.book = epub.read_epub(input_path)
            self.content_extractor = EPUBContentExtractor(self.book)
            self.creator = EPUBCreator(self.book)
        except Exception as e:
            logger.error(f"Failed to initialize EPUB service: {str(e)}")
            raise RuntimeError(f"EPUB initialization failed: {str(e)}")

    def extract_content(self) -> List[Tuple[str, str, int, str]]:
        """Extract content from EPUB file."""
        return self.content_extractor.extract_content()

    def create_translated_epub(
        self,
        translated_contents: List[Tuple[str, str]],
        output_path: str
    ) -> None:
        """Create new EPUB with translated content."""
        self.creator.create_translated_epub(translated_contents, output_path)
