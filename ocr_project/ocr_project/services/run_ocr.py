from pathlib import Path
import sys
import logging
from datetime import datetime
import os

from ocr_project.config.settings import settings
from ocr_project.core.batch_ocr_service import BatchOCRService

def setup_logging():
    """Configure logging for the OCR runner"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = settings.LOGS_DIR / f'ocr_run_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('OCR_Runner')

def main():
    logger = setup_logging()
    logger.info("Starting OCR processing")
    
    try:
        # Check environment variables first
        is_valid, missing_vars = settings.validate_environment(logger)
        if not is_valid:
            return
        
        # Verify the generated PDFs directory exists and has files
        if not settings.GENERATED_PDFS_DIR.exists():
            logger.error(f"Generated PDFs directory not found: {settings.GENERATED_PDFS_DIR}")
            return
            
        pdf_files = list(settings.GENERATED_PDFS_DIR.glob("form_*.pdf"))
        if not pdf_files:
            logger.error("No PDF files found in the generated PDFs directory")
            logger.info("Please run gen_files.py first to generate the PDFs")
            return
            
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Initialize and run batch service
        batch_service = BatchOCRService()
        results = batch_service.process_directory()
        
        # Generate analysis report
        batch_service.generate_analysis_report(results)
        
        # Print summary
        successful = sum(1 for result in results.values() if "error" not in result)
        failed = len(results) - successful
        
        logger.info("\n=== Processing Summary ===")
        logger.info(f"Total files processed: {len(results)}")
        logger.info(f"Successfully processed: {successful}")
        logger.info(f"Failed to process: {failed}")
        logger.info(f"\nResults saved in: {settings.ANALYZED_FORMS_DIR}")
        logger.info(f"Analysis report saved in: {settings.OUTPUT_DIR}/analysis_report.xlsx")
        
    except Exception as e:
        logger.error(f"Error during OCR processing: {str(e)}")
        raise
    finally:
        settings.clean_pycache()

if __name__ == "__main__":
    main()