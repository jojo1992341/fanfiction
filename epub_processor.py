import logging
from typing import List, Tuple
from services.epub_service import EPUBService
from services.translation_service import TranslationService
from services.email_service import EmailService

logger = logging.getLogger(__name__)

def process_epub(input_file: str, input_dir: str, output_dir: str) -> None:
    """Process a single EPUB file: extract content, translate, and create new EPUB."""
    logger.info(f"Starting to process: {input_file}")
    
    input_path = f"{input_dir}/{input_file}"
    epub_service = EPUBService(input_path)
    translator = TranslationService()
    
    # Extract content with all metadata
    contents = epub_service.extract_content()
    total = len(contents)
    logger.info(f"Extracted {total} items to translate")
    
    # Prepare translated contents maintaining the original structure
    translated_contents = []
    for i, (file_name, content, spine_pos, item_id) in enumerate(contents, 1):
        logger.info(f"Translating item {i}/{total}: {file_name}")
        translated_text = translator.translate_html_content(content)
        translated_contents.append((file_name, translated_text))
    
    # Generate output path
    output_path = f"{output_dir}/{input_file.replace('.epub', '_translated.epub')}"
    
    # Create new EPUB with translated content
    epub_service.create_translated_epub(translated_contents, output_path)
    logger.info(f"Created translated EPUB: {output_path}")
    
    return output_path
