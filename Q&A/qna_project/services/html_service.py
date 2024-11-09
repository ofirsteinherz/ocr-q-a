import logging

from qna_project.processors.html_processor import HTMLProcessor
from qna_project.config.settings import settings

class HTMLService:
    def __init__(self):
        """Initialize the HTML service with processor and logger."""
        self.processor = HTMLProcessor()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the service."""
        logger = logging.getLogger('html_service')
        logger.setLevel(logging.INFO)
        
        # Create handlers
        log_file = settings.LOGS_DIR / 'html_service.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        console_handler = logging.StreamHandler()
        
        # Create formatters and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def process_all_files(self) -> dict:
        try:
            # Validate required files first
            is_valid, missing_files = settings.validate_required_files()
            if not is_valid:
                self.logger.error("Missing required files:")
                for file in missing_files:
                    self.logger.error(f"- {file}")
                return {}
            
            self.logger.info("Starting batch processing of HTML files")
            results = self.processor.process_all_files()
            self.logger.info(f"Successfully processed {len(results)} files")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing files: {str(e)}")
            return {}

# Example usage:
if __name__ == "__main__":
    service = HTMLService()
    
    # Process all files
    results = service.process_all_files()
    print(f"Processed {len(results)} files")

    settings.clean_pycache()