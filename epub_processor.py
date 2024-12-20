"""EPUB processing service."""
import logging
from typing import List, Tuple, Dict
from services.epub_service import EPUBService
from services.parallel_translation_service import ParallelTranslationService
from utils.validation import validate_epub_file, validate_translation
from utils.content_processor import ContentProcessor

logger = logging.getLogger(__name__)

def process_epub(input_file: str, input_dir: str, output_dir: str) -> str:
    """
    Process a single EPUB file: extract content, translate, and create new EPUB.
    
    Args:
        input_file: Name of the input EPUB file
        input_dir: Directory containing the input file
        output_dir: Directory for the output file
        
    Returns:
        str: Path to the translated EPUB file
        
    Raises:
        ValueError: If input file is invalid
        RuntimeError: If processing fails
    """
    logger.info(f"Starting to process: {input_file}")
    
    input_path = f"{input_dir}/{input_file}"
    if not validate_epub_file(input_path):
        raise ValueError(f"Invalid EPUB file: {input_file}")
    
    try:
        epub_service = EPUBService(input_path)
        translator = ParallelTranslationService()
        content_processor = ContentProcessor()
        
        # Extract content with all metadata
        contents = epub_service.extract_content()
        if not contents:
            raise RuntimeError("No content extracted from EPUB")
            
        total = len(contents)
        logger.info(f"Extracted {total} items to translate")
        
        # Prepare content map for parallel translation
        content_map = {}
        for file_name, content, spine_pos, item_id in contents:
            cleaned_content = content_processor.clean_content(content)
            if cleaned_content:
                content_map[file_name] = cleaned_content
        
        if not content_map:
            raise RuntimeError("No valid content to translate")
        
        # Translate content in parallel
        logger.info("Starting parallel translation")
        translated_map = translator.translate_content(content_map)
        
        # Prepare translated contents maintaining the original structure
        translated_contents = []
        for file_name, translated_text in translated_map.items():
            if not translated_text:
                logger.warning(f"Empty translation for {file_name}")
                continue
                
            # Validate translation
            if not validate_translation(content_map[file_name], translated_text):
                logger.warning(f"Invalid translation for {file_name}")
                continue
                
            translated_contents.append((file_name, translated_text))
        
        if not translated_contents:
            raise RuntimeError("No content was successfully translated")
        
        # Generate output path
        output_path = f"{output_dir}/{input_file.replace('.epub', '_translated.epub')}"
        
        # Create new EPUB with translated content
        epub_service.create_translated_epub(translated_contents, output_path)
        logger.info(f"Created translated EPUB: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error processing {input_file}: {str(e)}")
        raise RuntimeError(f"Failed to process EPUB: {str(e)}")
