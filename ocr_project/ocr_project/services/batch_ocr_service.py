import logging
from pathlib import Path
import pandas as pd
from typing import List, Dict, Optional
import re

from ocr_project.config.settings import settings
from ocr_project.core.ocr_service import OCRService

def get_form_number(filename: str) -> int:
    """Extract form number from filename."""
    match = re.search(r'form_(\d+)\.pdf', filename)
    return int(match.group(1)) if match else 0

class BatchOCRService:
    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger('BatchOCRService')
        self.ocr_service = OCRService()
        
        # Ensure all required directories exist
        self._setup_directories()

    def _setup_logging(self):
        """Configure logging for the batch OCR service"""
        settings.LOGS_DIR.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(settings.LOGS_DIR / 'batch_ocr_service.log'),
                logging.StreamHandler()
            ]
        )

    def _setup_directories(self):
        """Ensure all required directories exist"""
        for directory in [
            settings.GENERATED_PDFS_DIR,
            settings.ANALYZED_FORMS_DIR,
            settings.TEMP_DIR
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def process_pdf_batch(self, pdf_files: List[Path], output_dir: Optional[Path] = None) -> Dict:
        """
        Process a batch of PDF files and return analysis results
        
        Args:
            pdf_files: List of paths to PDF files
            output_dir: Optional directory to save outputs. If not provided, uses default from settings
            
        Returns:
            Dict containing results for all processed files
        """
        self.logger.info(f"Starting batch processing of {len(pdf_files)} PDF files")
        output_dir = output_dir or settings.ANALYZED_FORMS_DIR
        
        results = {}
        for pdf_file in pdf_files:
            try:
                results[pdf_file.name] = self.ocr_service.process_pdf(pdf_file, output_dir)
            except Exception as e:
                self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")
                results[pdf_file.name] = {"error": str(e)}
        
        return results

    def generate_analysis_report(self, results: Dict):
        """Generate and save analysis report from processed results"""
        self.logger.info("Generating analysis report")
        
        try:
            # Convert results to DataFrame for analysis
            df = pd.DataFrame.from_dict(results, orient='index')
            
            # Save detailed results
            report_path = settings.OUTPUT_DIR / "analysis_report.xlsx"
            df.to_excel(report_path)
            
            self.logger.info(f"Analysis report saved to {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating analysis report: {str(e)}")
            raise

    def process_directory(self, input_dir: Optional[Path] = None) -> Dict:
        """
        Process all PDF files in a directory
        
        Args:
            input_dir: Directory containing PDF files. If not provided, uses default from settings
            
        Returns:
            Dict containing results for all processed files
        """
        input_dir = input_dir or settings.GENERATED_PDFS_DIR
        
        # Get all PDF files and sort them by form number
        pdf_files = list(input_dir.glob("form_*.pdf"))
        pdf_files.sort(key=lambda x: get_form_number(x.name))
        
        if not pdf_files:
            self.logger.error(f"No PDF files found in directory: {input_dir}")
            return {}
            
        return self.process_pdf_batch(pdf_files)

# if __name__ == "__main__": 
#     # For single file processing:
#     from ocr_project.core.ocr_service import OCRService

#     service = OCRService()
#     result = service.process_pdf(pdf_path)

#     # For batch processing:
#     from ocr_project.services.batch_ocr_service import BatchOCRService

#     batch_service = BatchOCRService()
#     results = batch_service.process_directory()  # Process all PDFs in default directory
#     # or
#     results = batch_service.process_pdf_batch(pdf_files)  # Process specific PDF files