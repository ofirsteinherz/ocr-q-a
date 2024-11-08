import os
import json
import fitz
from PIL import Image
from typing import List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
import logging
from datetime import datetime
from pathlib import Path

from ocr_project.config.settings import settings
from ocr_project.core.document_analyzer import DocumentAnalyzer
from ocr_project.core.gpt_client import GPTClient, Message, MessageRole

@dataclass
class Section:
    name: str
    y_start: int
    y_end: int = None
    path: str = None
    
class ExtractFormFields:
    def __init__(self):
        """Initialize the form fields extractor with configurations."""
        self.current_file = None
        self._setup_logging()
        self.logger = logging.getLogger('ExtractFormFields')
        
        self.logger.info("Initializing Form Fields Extractor...")
        
        load_dotenv(verbose=True)
        
        # Load configurations
        self.logger.info("Loading configuration files...")
        try:
            self.prompt = settings.get_prompt("prompt")
            self.post_process_prompt = settings.get_prompt("post_process_prompt")
            self.logger.info("✓ Prompts loaded successfully")
            
            self.schema = self._load_json(settings.SCHEMA_FILE)
            self.logger.info("✓ Schema loaded successfully")
            
            sections_config = self._load_json(settings.SECTIONS_FILE)
            self.sections_config = sections_config["sections"]
            self.logger.info("✓ Sections config loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configurations: {str(e)}")
            raise
        
        # Initialize clients
        self.logger.info("Initializing document analyzer and GPT client...")
        try:
            self.document_analyzer = DocumentAnalyzer(
                api_key=os.getenv("AZURE_DOCUMENT_KEY"),
                endpoint=os.getenv("AZURE_DOCUMENT_ENDPOINT")
            )
            self.logger.info("✓ Document analyzer initialized")
            
            self.gpt_client = GPTClient(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            self.logger.info("✓ GPT client initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize clients: {str(e)}")
            raise

    def _setup_logging(self):
        """Set up logging configuration."""
        settings.LOGS_DIR.mkdir(exist_ok=True)
        
        # Get the root logger and remove all handlers
        root_logger = logging.getLogger()
        if root_logger.hasHandlers():
            root_logger.handlers.clear()
        
        # Create a formatter that includes the current file
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(current_file)s] - %(levelname)s - %(message)s'
        )
        
        # Set up file handler with timestamp in filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(settings.LOGS_DIR / f'extract_form_fields_{timestamp}.log')
        file_handler.setFormatter(formatter)
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure logger
        logger = logging.getLogger('ExtractFormFields')
        
        # Remove any existing handlers to prevent duplication
        if logger.hasHandlers():
            logger.handlers.clear()
            
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

        # Add filter to include current file in log records
        class ContextFilter(logging.Filter):
            def __init__(self, extract_form_fields):
                super().__init__()
                self.extract_form_fields = extract_form_fields

            def filter(self, record):
                record.current_file = self.extract_form_fields.current_file or 'NO_FILE'
                return True

        logger.addFilter(ContextFilter(self))

    def process_form(self, pdf_path: Path, output_dir: Path = None, dpi: int = None) -> Dict:
        """Process a single form and return structured data."""
        self.current_file = pdf_path.name  # Set current file being processed
        output_dir = output_dir or settings.ANALYZED_FORMS_DIR
        dpi = dpi or settings.DEFAULT_DPI
        
        self.logger.info("="*50)
        self.logger.info("Starting form processing")
        
        try:
            # First pass - process sections
            first_pass_results = self._process_sections(pdf_path, output_dir, dpi)
            
            # Second pass - post-process entire form
            self.logger.info("Starting second pass - post-processing form data...")
            try:
                final_results = self._post_process_form(first_pass_results)
                self.logger.info("✓ Post-processing completed successfully")
            except Exception as e:
                self.logger.error(f"Error in post-processing: {str(e)}")
                final_results = first_pass_results

            self.logger.info("Form processing completed successfully")
            return final_results
            
        finally:
            self.current_file = None  # Clear current file when done

    def _process_sections(self, pdf_path: Path, output_dir: Path, dpi: int) -> Dict:
        """Process individual sections of the form."""
        sections_dir = output_dir / "sections"
        sections_dir.mkdir(exist_ok=True)
        
        # Split PDF into sections
        sections = self._split_pdf_sections(pdf_path, sections_dir, dpi)
        
        # Process each section
        results = {}
        for i, section in enumerate(sections, 1):
            self.logger.info(f"Processing section {i}/{len(sections)}: {section.name}")
            try:
                # Get OCR data
                self.logger.info("Sending request to Document Analyzer...")
                ocr_data = self.document_analyzer.analyze_local_document(section.path)
                
                # Log OCR results
                cleaned_ocr = {
                    "text": ocr_data.get("paragraphs", []),
                    "fields": ocr_data.get("form_fields", []),
                    "key_value_pairs": ocr_data.get("key_value_pairs", {})
                }
                self.logger.info("OCR Results:")
                self.logger.info(f"Text found: {json.dumps(cleaned_ocr['text'], ensure_ascii=False, indent=2)}")
                self.logger.info(f"Fields found: {json.dumps(cleaned_ocr['fields'], ensure_ascii=False, indent=2)}")
                self.logger.info(f"Key-Value pairs: {json.dumps(cleaned_ocr['key_value_pairs'], ensure_ascii=False, indent=2)}")
                self.logger.info("✓ Document analysis completed")
                
                # Prepare prompt and process with GPT
                section_prompt = self._prepare_section_prompt(section.name)
                section_data = self._process_with_gpt(section_prompt, ocr_data)
                results[section.name] = section_data
                
            except Exception as e:
                self.logger.error(f"Error processing section {section.name}: {str(e)}")
                results[section.name] = {}
        
        return results

    def _post_process_form(self, first_pass_results: Dict) -> Dict:
        """Perform second pass processing on the entire form data."""
        self.logger.info("Starting form post-processing...")
        
        try:
            messages = [
                Message(
                    role=MessageRole.SYSTEM,
                    content=self.post_process_prompt
                ),
                Message(
                    role=MessageRole.USER,
                    content=f"Here is the processed form data from the first pass:\n{json.dumps(first_pass_results, ensure_ascii=False, indent=2)}"
                )
            ]

            self.logger.info("Sending request to GPT for post-processing...")
            final_results = self.gpt_client.chat(messages, json_response=True)
            self.logger.info("✓ Post-processing completed")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Error in post-processing: {str(e)}")
            return first_pass_results

    def _split_pdf_sections(self, pdf_path: Path, output_dir: Path, dpi: int) -> List[Section]:
        """Split PDF into sections based on configuration."""
        self.logger.info("Starting PDF splitting process...")
        
        try:
            self.logger.info("Opening PDF document...")
            pdf_document = fitz.open(str(pdf_path))
            page = pdf_document[0]  # First page only
            self.logger.info("✓ PDF opened successfully")
            
            # Render high-res image
            self.logger.info(f"Rendering PDF page at {dpi} DPI...")
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            width, height = img.size
            self.logger.info(f"✓ Page rendered successfully (size: {width}x{height})")

            # Process sections
            sections = []
            sorted_configs = sorted(self.sections_config, key=lambda x: x['y_start'])
            self.logger.info(f"Processing {len(sorted_configs)} sections...")
            
            for i, config in enumerate(sorted_configs, 1):
                section_name = config['name']
                self.logger.info(f"Processing section {i}/{len(sorted_configs)}: {section_name}")
                y_start = config['y_start']
                y_end = sorted_configs[i]['y_start'] if i < len(sorted_configs) else height
                
                self.logger.info(f"Section coordinates - y_start: {y_start}, y_end: {y_end}")
                
                if y_start >= y_end:
                    self.logger.warning(f"Skipping section '{section_name}' due to invalid coordinates")
                    continue
                    
                section = Section(
                    name=section_name,
                    y_start=y_start,
                    y_end=y_end,
                    path=str(output_dir / f"{section_name}.png")
                )
                
                # Crop and save section
                self.logger.info(f"Cropping and saving section to: {section.path}")
                section_img = img.crop((0, y_start, width, y_end))
                section_img.save(section.path)
                sections.append(section)
                self.logger.info(f"✓ Section {section_name} processed successfully")

            pdf_document.close()
            self.logger.info(f"PDF splitting completed. Generated {len(sections)} section images.")
            return sections
            
        except Exception as e:
            self.logger.error(f"Error in PDF splitting: {str(e)}")
            raise

    def _prepare_section_prompt(self, section_name: str) -> str:
        """Prepare GPT prompt for specific section."""
        self.logger.info(f"Preparing prompt for section: {section_name}")
        
        # Get the schema for this section
        section_schema = self.schema.get(section_name, {})
        
        # Create a clean, formatted schema string
        schema_str = json.dumps(section_schema, ensure_ascii=False, indent=2)
        
        # Load the base prompt and add the section-specific information
        prompt = (
            f"{self.prompt}\n\n"
            f"Current section: {section_name}\n"
            f"Schema for this section:\n{schema_str}"
        )
        
        self.logger.info("✓ Section prompt prepared successfully")
        return prompt

    def _process_with_gpt(self, prompt: str, ocr_data: Dict) -> Dict:
        """Process section data with GPT."""
        self.logger.info("Preparing GPT request...")
        try:
            # Clean up OCR data for better processing
            cleaned_ocr = {
                "text": ocr_data.get("paragraphs", []),
                "fields": ocr_data.get("form_fields", []),
                "key_value_pairs": ocr_data.get("key_value_pairs", {})
            }
            
            # Create messages with proper encoding
            messages = [
                Message(
                    role=MessageRole.SYSTEM,
                    content=prompt
                ),
                Message(
                    role=MessageRole.USER,
                    content=f"Here is the scanned text:\n {json.dumps(cleaned_ocr, ensure_ascii=False)}"
                )
            ]

            self.logger.info("Sending request to GPT...")
            
            # Process with GPT
            response = self.gpt_client.chat(messages, json_response=True)
            
            self.logger.info("✓ GPT processing completed successfully")
            self.logger.info("GPT Response:")
            self.logger.info(json.dumps(response, ensure_ascii=False, indent=2))
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in GPT processing: {str(e)}")
            return {}

    @staticmethod
    def _load_json(path: Path) -> Dict:
        """Load JSON file content."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)