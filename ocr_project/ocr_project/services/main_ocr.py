import json
from pathlib import Path
from dotenv import load_dotenv
import os

from ocr_project.core.document_analyzer import DocumentAnalyzer
from ocr_project.core.gpt_client import GPTClient, Message, MessageRole, GPTResponseError
from ocr_project.config.settings import settings

def process_document(form_path: Path, analyzer: DocumentAnalyzer, client: GPTClient) -> dict:
    """Process a single document through OCR and GPT analysis"""
    try:
        # Extract text from document
        print(f"Processing document: {form_path}")
        extracted_data = analyzer.analyze_local_document(str(form_path))
        extracted_ocr = json.dumps(extracted_data, indent=4)

        # Get the OCR analysis prompt
        try:
            prompt = settings.get_prompt("ocr_analysis")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Make sure the prompt file exists at:", settings.PROMPTS_DIR / "ocr_analysis.txt")
            return None
        except Exception as e:
            print(f"Error reading prompt: {e}")
            return None

        # Process with GPT
        messages = [
            Message(role=MessageRole.SYSTEM, content=prompt),
            Message(role=MessageRole.USER, content=extracted_ocr)
        ]
        
        response = client.chat(messages, json_response=True)
        print(f"Successfully processed: {form_path.name}")
        return response
        
    except Exception as e:
        print(f"Error processing {form_path.name}: {str(e)}")
        return None

def validate_environment() -> bool:
    """Validate all required environment variables exist"""
    required_env_vars = [
        "AZURE_DOCUMENT_KEY",
        "AZURE_DOCUMENT_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        return False
    return True

def main():
    # Load environment variables from project root
    env_path = settings.PROJECT_ROOT / ".env"
    load_dotenv(env_path, verbose=True)
    
    if not validate_environment():
        return

    try:
        # Initialize services
        analyzer = DocumentAnalyzer(
            api_key=os.getenv("AZURE_DOCUMENT_KEY"),
            endpoint=os.getenv("AZURE_DOCUMENT_ENDPOINT")
        )

        client = GPTClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # Process first generated form
        form_1_path = settings.GENERATED_PDFS_DIR / "form_1.pdf"
        if not form_1_path.exists():
            print(f"Form not found: {form_1_path}")
            print("Please run the form generation script first (main.py)")
            return

        # Process the document
        result = process_document(form_1_path, analyzer, client)
        
        if result:
            # Save the result
            output_json_path = settings.ANALYZED_FORMS_DIR / "form_1_analysis.json"
            output_json_path.parent.mkdir(exist_ok=True)
            
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
                
            print(f"\nAnalysis saved to: {output_json_path}")
        
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()