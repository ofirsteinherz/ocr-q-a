import os
import json
import fitz
from PIL import Image
from typing import List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
import logging
from datetime import datetime

from document_analyzer import DocumentAnalyzer
from gpt_client import GPTClient, Message, MessageRole, GPTResponseError

@dataclass
class Section:
    name: str
    y_start: int
    y_end: int = None
    path: str = None

class FormProcessor:
    def __init__(self, config_path: str = "config"):
        """Initialize the form processor with configurations."""
        self._setup_logging()
        self.logger = logging.getLogger('FormProcessor')
        
        self.logger.info("Initializing Form Processor...")
        self.logger.info(f"Using config path: {config_path}")
        
        load_dotenv(verbose=True)
        
        # Load configurations
        self.logger.info("Loading configuration files...")
        try:
            self.prompt = self._load_file(os.path.join(config_path, "prompt.txt"))
            self.post_process_prompt = self._load_file(os.path.join(config_path, "post_process_prompt.txt"))
            self.logger.info("✓ Prompts loaded successfully")
            
            self.schema = self._load_json(os.path.join(config_path, "schema.json"))
            self.logger.info("✓ Schema loaded successfully")
            
            sections_config = self._load_json(os.path.join(config_path, "sections.json"))
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
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create a formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Set up file handler with timestamp in filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(f'logs/form_processor_{timestamp}.log')
        file_handler.setFormatter(formatter)
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure logger
        logger = logging.getLogger('FormProcessor')
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    def process_form(self, pdf_path: str, output_dir: str = "output", dpi: int = 300) -> Dict:
        """Process a single form and return structured data."""
        self.logger.info(f"\n{'='*50}\nStarting form processing")
        self.logger.info(f"Processing PDF: {pdf_path}")
        
        # First pass - process sections
        first_pass_results = self._process_sections(pdf_path, output_dir, dpi)
        
        # Second pass - post-process entire form
        self.logger.info("\nStarting second pass - post-processing form data...")
        try:
            final_results = self._post_process_form(first_pass_results)
            self.logger.info("✓ Post-processing completed successfully")
        except Exception as e:
            self.logger.error(f"Error in post-processing: {str(e)}")
            final_results = first_pass_results

        self.logger.info("\nForm processing completed successfully")
        return final_results

    def _process_sections(self, pdf_path: str, output_dir: str, dpi: int) -> Dict:
        """Process individual sections of the form."""
        sections_dir = os.path.join(output_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
        # Split PDF into sections
        sections = self._split_pdf_sections(pdf_path, sections_dir, dpi)
        
        # Process each section
        results = {}
        for i, section in enumerate(sections, 1):
            self.logger.info(f"\nProcessing section {i}/{len(sections)}: {section.name}")
            try:
                ocr_data = self.document_analyzer.analyze_local_document(section.path)
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

    def _split_pdf_sections(self, pdf_path: str, output_dir: str, dpi: int) -> List[Section]:
        """Split PDF into sections based on configuration."""
        self.logger.info("Starting PDF splitting process...")
        
        try:
            self.logger.info("Opening PDF document...")
            pdf_document = fitz.open(pdf_path)
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
                self.logger.info(f"\nProcessing section {i}/{len(sorted_configs)}: {config['name']}")
                y_start = config['y_start']
                y_end = sorted_configs[i]['y_start'] if i < len(sorted_configs) else height
                
                self.logger.info(f"Section coordinates - y_start: {y_start}, y_end: {y_end}")
                
                if y_start >= y_end:
                    self.logger.warning(f"Skipping section '{config['name']}' due to invalid coordinates")
                    continue
                    
                section = Section(
                    name=config['name'],
                    y_start=y_start,
                    y_end=y_end,
                    path=os.path.join(output_dir, f"{config['name']}.png")
                )
                
                # Crop and save section
                self.logger.info(f"Cropping and saving section to: {section.path}")
                section_img = img.crop((0, y_start, width, y_end))
                section_img.save(section.path)
                sections.append(section)
                self.logger.info(f"✓ Section {config['name']} processed successfully")

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
        # Using ensure_ascii=False to properly handle Hebrew characters
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

            print("cleaned_ocr:")
            print(cleaned_ocr)
            print()
            
            # Create messages with proper encoding
            messages = [
                Message(
                    role=MessageRole.SYSTEM,
                    content=prompt
                ),
                Message(
                    role=MessageRole.USER,
                    # Using ensure_ascii=False to properly handle Hebrew characters
                    content=f"Here is the scanned text:\n {json.dumps(cleaned_ocr, ensure_ascii=False)}"
                )
            ]

            print("messages")
            print(messages)
            print()

            self.logger.info("Sending request to GPT...")
            self.logger.debug(f"System message length: {len(messages[0].content)}")
            self.logger.debug(f"User message length: {len(messages[1].content)}")

            # Process with GPT
            response = self.gpt_client.chat(messages, json_response=True)

            print("response")
            print(response)
            print()
            
            self.logger.info("✓ GPT processing completed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Error in GPT processing: {str(e)}")
            return {}

    @staticmethod
    def _load_file(path: str) -> str:
        """Load text file content."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()  # Strip to remove any extra whitespace

    @staticmethod
    def _load_json(path: str) -> Dict:
        """Load JSON file content."""
        with open(path, 'r', encoding='utf-8') as f:
            # Using ensure_ascii=False when loading to properly handle Hebrew characters
            return json.load(f)


def main():
    logger = logging.getLogger('FormProcessor')
    logger.info("\nStarting form processing application...")
    
    try:
        processor = FormProcessor()
        form_path = os.path.join("files", "generated_pdfs", "form_1.pdf")
        
        # Process form with both passes
        results = processor.process_form(form_path)
        
        # Save results
        output_dir = os.path.join("files", "output")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "processed_form.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Processing complete. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()

