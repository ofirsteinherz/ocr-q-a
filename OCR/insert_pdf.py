import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import json

def flatten_json_elements(json_data):
    """Flatten nested JSON structure into a list of elements with x,y coordinates"""
    flattened_elements = []
    
    # Process each section
    for section in json_data.get("sections", []):
        # Process each field in the section
        for field in section.get("fields", []):
            # Check if field has sub_fields
            if "sub_fields" in field:
                for sub_field in field["sub_fields"]:
                    if sub_field.get("x", 0) != 0 or sub_field.get("y", 0) != 0:
                        flattened_elements.append({
                            "text": sub_field.get("value", ""),
                            "x": sub_field.get("x", 0),
                            "y": sub_field.get("y", 0),
                            "font_size": sub_field.get("font_size", 12),
                            "label": sub_field.get("label", "")
                        })
            else:
                # Process regular field
                if field.get("x", 0) != 0 or field.get("y", 0) != 0:
                    flattened_elements.append({
                        "text": field.get("value", ""),
                        "x": field.get("x", 0),
                        "y": field.get("y", 0),
                        "font_size": field.get("font_size", 12),
                        "label": field.get("label", "")
                    })
    
    return flattened_elements

def add_text_to_pdf(input_pdf, output_pdf, form_elements_path, zoom=2):
    try:
        # Read form elements from file
        with open(form_elements_path, 'r', encoding='utf-8') as f:
            form_data = json.load(f)
        
        # Flatten the nested JSON structure
        flattened_elements = flatten_json_elements(form_data)
        
        # Create text_data in the format expected by the PDF processing
        text_data = {"0": flattened_elements}  # Assuming all elements go on first page
        
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
                        # Skip items with x=0 and y=0
                        if text_item["x"] == 0 and text_item["y"] == 0:
                            continue
                            
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

script_dir = os.path.dirname(os.path.abspath(__file__))

# Correct paths - looking in the 'files' subfolder
input_pdf = os.path.join(script_dir, "files", "283_raw.pdf")
output_pdf = os.path.join(script_dir, "files", "output_high_res.pdf")
form_elements_path = os.path.join(script_dir, "form_elements.json")

try:
    add_text_to_pdf(input_pdf, output_pdf, form_elements_path, zoom=3)
except Exception as e:
    print(f"Error: {str(e)}")