import logging
from pathlib import Path
from typing import List, Dict
import json
import pandas as pd

from ocr_project.config.settings import settings
from ocr_project.core.form_processor import FormProcessor
from ocr_project.core.document_analyzer import DocumentAnalyzer
from ocr_project.core.gpt_client import GPTClient

class OCRProcessor:
    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger('OCRProcessor')
        
        # Initialize processors and clients
        self.form_processor = FormProcessor()
        self.document_analyzer = DocumentAnalyzer()
        self.gpt_client = GPTClient()
        
        # Ensure all required directories exist
        self._setup_directories()

    def _setup_logging(self):
        """Configure logging for the OCR processor"""
        # Create logs directory
        settings.LOGS_DIR.mkdir(exist_ok=True)
        
        # Configure logging format
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(settings.LOGS_DIR / 'ocr_processing.log'),
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

    def process_pdf_batch(self, pdf_files: List[Path]) -> Dict:
        """Process a batch of PDF files and return analysis results"""
        self.logger.info(f"Starting batch processing of {len(pdf_files)} PDF files")
        
        results = {}
        for pdf_file in pdf_files:
            try:
                self.logger.info(f"Processing {pdf_file.name}")
                
                # Process the form using FormProcessor
                form_data = self.form_processor.process_form(
                    pdf_path=str(pdf_file),
                    output_dir=str(settings.ANALYZED_FORMS_DIR)
                )
                
                # Save individual form results
                output_path = settings.ANALYZED_FORMS_DIR / f"{pdf_file.stem}_analysis.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(form_data, f, ensure_ascii=False, indent=2)
                
                results[pdf_file.name] = form_data
                self.logger.info(f"✓ Successfully processed {pdf_file.name}")
                
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