import os
import json
from dotenv import load_dotenv

from document_analyzer import DocumentAnalyzer
from gpt_client import GPTClient, Message, MessageRole, GPTResponseError

# Load environment variables from .env file
load_dotenv(verbose=True)

def main():

    # Initialize analyzer
    analyzer = DocumentAnalyzer(
        api_key=os.getenv("AZURE_DOCUMENT_KEY"),
        endpoint=os.getenv("AZURE_DOCUMENT_ENDPOINT")
    )

    # Example for single document

    # Define base directories relative to the current script's directory
    form_1_pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files", "generated_pdfs", "form_1.pdf")

    # You can use this path to read or write the file
    print(f"Now processing: {form_1_pdf_path}")

    extracted_data = analyzer.analyze_local_document(form_1_pdf_path)
    print(extracted_data)

    extracted_ocr = json.dumps(extracted_data, indent=4)

    prompt = """

        You are a specialized document processor focusing on accurate Hebrew document analysis. Your task is to analyze OCR text 
        from medical forms and map it to a structured JSON format. Follow these strict guidelines:

        1. Field Structure:
        Each section contains:
        - id: section identifier
        - title: section title (if present)
        - fields: array of form fields

        2. Field Types and Handling:
        - text: Regular text fields
        * Preserve Hebrew text exactly as written
        * Maintain special characters (״, ׳, ")
        * Keep abbreviations in original form

        - date: Date fields
        * Preserve exact spacing between digits
        * Support both formats:
            - Spaced digits (e.g., "5  5  3  9  0  9  1  3")
            - Standard date format (e.g., "01.12.2023")

        - time: Time fields
        * Keep 24-hour format (e.g., "16:06")

        - checkbox: Boolean fields
        * Use "V" for selected
        * Use "" (empty string) for unselected
        * Never infer selections

        - phone_number: Phone number fields
        * Maintain exact spacing between digits
        * Preserve leading zeros

        3. Expected Output Format:
        {
        "header": {
            "אל קופ״ח/בי״ח": string,
            "תאריך מילוי הטופס": string,
            "תאריך קבלת הטופס בקופה": string
        },
        "section1": {
            "תאריך הפגיעה": string
        },
        "section2": {
            "שם משפחה": string,
            "שם פרטי": string,
            "ת.ז": string,
            "תאריך לידה": string,
            "מין": {
            "זכר": string,
            "נקבה": string
            },
            "רחוב": string,
            "מס' בית": string,
            "כניסה": string,
            "דירה": string,
            "יישוב": string,
            "מיקוד": string,
            "טלפון קווי": string,
            "טלפון נייד": string
        },
        "section3": {
            "בתאריך": string,
            "בשעה": string,
            "כאשר עבדתי ב": string,
            "מקום התאונה": {
            "מפעל": string,
            "ת. דרכים בעבודה": string,
            "ת. דרכים בדרך לעבודה/מהעבודה": string,
            "תאונה בדרך לא רכב": string,
            "אחר": string
            },
            "כתובת מקום התאונה": string,
            "נסיבות הפגיעה / תיאור התאונה": string,
            "האיבר שנפגע": string
        },
        "section4": {
            "שם המבקש": string,
            "חתימה": string
        },
        "section5": {
            "סטטוס חברות בקופת חולים": {
            "הנפגע חבר בקופת חולים": string,
            "הנפגע אינו חבר בקופת חולים": string
            },
            "קופת חולים": {
            "כללית": string,
            "מאוחדת": string,
            "מכבי": string,
            "לאומית": string
            },
            "אבחנה רפואית": {
            "1": string,
            "2": string
            }
        }
        }

        4. Validation Rules:
        - All fields must be included in output, even if empty
        - Maintain exact field names as specified
        - Preserve all spacing in numeric fields
        - Keep original text formatting
        - Follow type-specific formatting rules
        - Handle sub_fields properly in nested structures
        - Maintain field order as specified in the input JSON

        5. Data Integrity:
        - Never modify or normalize the data
        - Keep all original spacing and formatting
        - Preserve exact coordinate information if present
        - Maintain font sizes and text properties
    """

    client = GPTClient(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    try:
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=prompt
            ),
            Message(
                role=MessageRole.USER,
                content=extracted_ocr
            )
        ]
        
        response = client.chat(messages, json_response=True)
        print("\nChat Response:")
        print(response)
        
    except GPTResponseError as e:
        print(f"GPT Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
