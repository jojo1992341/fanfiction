import os
import logging
from services.epub_processor import process_epub
from services.email_service import EmailService
from config.settings import INPUT_DIR, OUTPUT_DIR, LOG_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/translation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    # Ensure directories exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Get list of EPUB files to process
    epub_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.epub')]
    
    if not epub_files:
        logger.warning("No EPUB files found in input directory")
        return
    
    email_service = EmailService()
    
    # Process each EPUB file
    for epub_file in epub_files:
        try:
            logger.info(f"Processing {epub_file}")
            output_path = process_epub(epub_file, INPUT_DIR, OUTPUT_DIR)
            
            # Send to Kindle
            logger.info(f"Sending {output_path} to Kindle")
            email_service.send_to_kindle(output_path, f"Translated: {epub_file}")
            logger.info(f"Successfully processed and sent {epub_file}")
            
        except Exception as e:
            logger.error(f"Error processing {epub_file}: {str(e)}")
            continue

if __name__ == "__main__":
    main()
