# Healthcare Form Processing and Q&A System

This project consists of two main components:
1. OCR Processing System for Healthcare Forms
2. Healthcare Information Q&A System

## Projects Structure

```
├── ocr_project/        # OCR Form Processing System
│   ├── core/           # Core OCR processing functionality
│   ├── services/       # Service-level implementations
│   ├── web/            # Web interface for OCR processing
│   └── resources/      # Configuration and resource files
│
├── Q&A/                # Healthcare Q&A System
    ├── qna_project/    # Main Q&A implementation
    ├── resources/      # Q&A resources and configurations
    └── web/            # Web interface for Q&A system
```

## Projects Overview

### Generate Synthetic Files

Before creating the OCR process, I focus on creating synthetic PDF files so I would be able to evaluate the OCR pipeline.

#### Stage 1: Cordinates Mapping

First, I mapped for each component in the PDF file the coordinates where everything is located in the PDF. You can take a look in the [form_elements.json](https://github.com/ofirsteinherz/ocr-q-a/blob/main/ocr_project/resources/form_elements.json) file. For each field, we have the coordinates, text, and section. That structure will help us in the upcoming parts, with Microsoft Document Analyzer and GPT services.

![from_doc_to_element](images/from_doc_to_element.png)

#### Stage 2: Fake Data Creation

Created [fake_csv.py](https://github.com/ofirsteinherz/ocr-q-a/blob/main/ocr_project/ocr_project/utils/fake_csv.py) which have these capabilities:

- Generates realistic Hebrew names
- Creates valid ID numbers
- Generates formatted dates
- Produces valid phone numbers
- Creates random addresses
- Handles checkbox selections

#### Stage 3: PDFs Creation 

Given the coordinates and the fake CSV, I created 100 PDFs that would be used as a supervised evaluation of the OCR pipeline.

![synthetic_filles_pipeline](images/synthetic_filles_pipeline.png)

To execute the CLI command, use:

```bash
python -m ocr_project.services.gen_files
```


![synthetic_files_example](images/synthetic_files_example.jpg)

### OCR Processing











python3 -m ocr_project.services.run_ocr

3. Evaluate Results

4. Run Web Interface









## Prerequisites

- Python 3.8 or higher
- Azure Cognitive Services subscription (for OCR and GPT services)
- Azure Form Recognizer service
- Azure OpenAI service

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ofirsteinherz/ocr-q-a
cd ocr-q-a
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install requirements for both projects:
```bash
pip install -r ocr_project/requirements.txt
pip install -r Q&A/requirements.txt
```

I didn't have sufficient time to set up a new VM to verify if the required files are compatible with the codebase.

4. Set up environment variables:
    Create a `.env` file in the root directory with:

```
AZURE_DOCUMENT_ENDPOINT=your_form_recognizer_endpoint
AZURE_DOCUMENT_KEY=your_form_recognizer_key
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
```

## OCR Project Usage

### 1. Generate Synthetic Files
Generate synthetic PDF files for testing:
```bash
python -m ocr_project.services.gen_files
```

### 2. Run OCR Processing
Process the generated PDF files:
```bash
python -m ocr_project.services.run_ocr
```

### 3. Evaluate Results
Compare OCR results with expected values:
```bash
python -m ocr_project.services.compare_service
```

### 4. Run Web Interface
Start the OCR web interface:
```bash
python -m ocr_project.web.app
```

## Q&A System Usage

### 1. Process HTML Resources
Process the HTML files containing healthcare information:
```bash
python -m qna_project.services.html_service
```

### 2. Search Customer Information
Test customer information search functionality:
```bash
python -m qna_project.services.search_customer
```

### 3. Run Q&A Interface
Start the Q&A web interface:
```bash
streamlit run qna_project/web/streamlit/main.py
```

## Project Components

### OCR Project
- Form Processing: Extracts information from healthcare forms using Azure Form Recognizer
- Field Validation: Validates extracted data against expected formats
- Web Interface: Flask-based interface for uploading and processing forms
- Evaluation: Compares extracted data with expected values

### Q&A System
- Healthcare Information Processing: Processes structured healthcare information from HTML
- Customer Service Integration: Manages customer data and service queries
- Interactive Interface: Streamlit-based chat interface for healthcare inquiries
- Dynamic Response Generation: Uses Azure OpenAI for natural language interaction

## Directory Structure Details

### OCR Project
```
ocr_project/
├── core/
│   ├── document_analyzer.py    # Azure Form Recognizer integration 
│   ├── extract_form_fields.py  # Field extraction logic
│   ├── form_processor.py       # Form processing utilities
│   └── gpt_client.py           # GPT integration
├── services/
│   ├── run_ocr.py              # OCR service runner
│   ├── gen_files.py            # Synthetic file generator
│   └── compare_service.py      # Results evaluation
└── web/
    ├── app.py                  # Web interface
    └── templates/              # HTML templates
```

### Q&A Project
```
Q&A/
├── qna_project/
│   ├── clients/              # API clients
│   ├── config/               # Configuration
│   ├── processors/           # Data processors
│   ├── services/             # Business logic
│   └── web/                  # Web interface
└── resources/
    ├── prompts/              # System prompts
    └── raw_html/             # Healthcare information
```

## Configuration

### OCR Configuration
- Form templates in `ocr_project/resources/`
- OCR settings in `ocr_project/config/settings.py`
- Web interface configuration in `ocr_project/web/app.py`

### Q&A Configuration
- Healthcare data in `Q&A/resources/raw_html/`
- Q&A prompts in `Q&A/resources/prompts/`
- System settings in `Q&A/qna_project/config/settings.py`

## Error Handling

Both systems include comprehensive error handling:
- Input validation
- Service connection errors
- Processing failures
- Data validation errors

Logs are stored in the respective `logs` directories of each project.
