import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import json

def add_text_to_pdf(input_pdf, output_pdf, text_data_json, zoom=2):
    # Rest of the function remains the same as before
    if isinstance(text_data_json, str):
        text_data = json.loads(text_data_json)
    else:
        text_data = text_data_json

    try:
        # Create a single font instance that will be reused
        font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", int(12 * zoom))
        
        print(f"Attempting to open PDF at: {input_pdf}")
        pdf_document = fitz.open(input_pdf)
        pdf_bytes = []

        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            draw = ImageDraw.Draw(img)

            if str(page_num) in text_data:
                for text_item in text_data[str(page_num)]:
                    try:
                        x = text_item["x"] * zoom
                        y = text_item["y"] * zoom
                        
                        if "font_size" in text_item and text_item["font_size"] != 12:
                            item_font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", 
                                                         int(text_item["font_size"] * zoom))
                        else:
                            item_font = font
                        
                        draw.text((x, y), text_item["text"], fill="black", font=item_font, anchor="ls")
                        
                    except Exception as e:
                        print(f"Warning: Error processing text item on page {page_num + 1}: {str(e)}")
                        continue

            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format="PDF", resolution=300)
            pdf_bytes.append(img_byte_arr.getvalue())

        with open(output_pdf, "wb") as f:
            pdf_writer = fitz.open()
            for page_data in pdf_bytes:
                pdf_writer.insert_pdf(fitz.open("pdf", page_data))
            pdf_writer.save(f)

    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

# Your text data remains the same
text_data = {
    "0": [
        {
            "text": "1  2  2  2  2  2  2  2",
            "x": 65,
            "y": 95,
            "font_size": 12,
            "label": "Data filling form" 
        },
        {
            "text": "1  2  2  2  2  2  2  2",
            "x": 213,
            "y": 100,
            "font_size": 12,
            "label": "invoice_number"
        }
    ],
    "1": [
        {
            "text": "Another Text",
            "x": 150,
            "y": 350,
            "font_size": 14,
            "label": "total_amount"
        }
    ]
}

# Debug prints
script_dir = os.path.dirname(os.path.abspath(__file__))

# Correct paths - looking in the 'files' subfolder
input_pdf = os.path.join(script_dir, "files", "283_raw.pdf")
output_pdf = os.path.join(script_dir, "files", "output_high_res.pdf")

try:
    json_string = json.dumps(text_data, indent=2)
    add_text_to_pdf(input_pdf, output_pdf, json_string, zoom=3)
except Exception as e:
    print(f"Error: {str(e)}")

# Example usage
text_data = {
    "0": [
        {
            "text": "1  2  2  2  2  2  2  2",
            "x": 65,
            "y": 95,
            "font_size": 12,
            "label": "Data filling form" 
        },
        {
            "text": "1  2  2  2  2  2  2  2",
            "x": 213,
            "y": 100,
            "font_size": 12,
            "label": "invoice_number"
        }
    ],
    "1": [
        {
            "text": "Another Text",
            "x": 150,
            "y": 350,
            "font_size": 14,
            "label": "total_amount"
        }
    ]
}

try:
    json_string = json.dumps(text_data, indent=2)
    add_text_to_pdf(input_pdf, output_pdf, json_string, zoom=3)
except Exception as e:
    print(f"Error: {str(e)}")