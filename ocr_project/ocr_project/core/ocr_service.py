import logging
from pathlib import Path
import json
from typing import Dict, Optional
import os
from dotenv import load_dotenv

from ocr_project.config.settings import settings
from ocr_project.core.extract_form_fields import ExtractFormFields
from ocr_project.core.document_analyzer import DocumentAnalyzer
from ocr_project.core.gpt_client import GPTClient

class OCRService:
    def __init__(self):
        # Load environment variables
        load_dotenv(verbose=True)
        
        # Validate required environment variables
        self._validate_env_vars()
        
        self._setup_logging()
        self.logger = logging.getLogger('OCRService')
        
        # Initialize processors
        self.form_processor = ExtractFormFields()

    def _validate_env_vars(self):
        """Validate that all required environment variables are set"""
        required_vars = [
            "AZURE_DOCUMENT_ENDPOINT",
            "AZURE_DOCUMENT_KEY",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please ensure these are set in your .env file"
            )

    def _setup_logging(self):
        """Configure logging for the OCR service"""
        settings.LOGS_DIR.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(settings.LOGS_DIR / 'ocr_service.log'),
                logging.StreamHandler()
            ]
        )

    def process_pdf(self, pdf_path: Path, output_dir: Optional[Path] = None) -> Dict:
        """
        Process a single PDF file and return analysis results
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Optional directory to save the output. If not provided, uses default from settings
            
        Returns:
            Dict containing the analysis results
        """
        self.logger.info(f"Processing PDF: {pdf_path}")
        output_dir = output_dir or settings.ANALYZED_FORMS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Process the form using ExtractFormFields
            form_data = self.form_processor.process_form(
                pdf_path=pdf_path,
                output_dir=output_dir
            )
            
            # Save individual form results
            output_path = output_dir / f"{pdf_path.stem}_analysis.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(form_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✓ Successfully processed {pdf_path.name}")
            return form_data
            
        except Exception as e:
            self.logger.error(f"Error processing {pdf_path.name}: {str(e)}")
            raise