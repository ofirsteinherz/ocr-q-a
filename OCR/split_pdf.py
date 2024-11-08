import fitz  # PyMuPDF
from PIL import Image  # Import Image from Pillow
import os

def split_pdf_page_custom(pdf_path, output_dir, sections_config, dpi=300):
    """
    Split the first page of a PDF into sections based on custom configuration.

    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Directory to save the output images
        sections_config (list): List of dictionaries with section configurations
            Each dict should have:
            - name: section name
            - y_start: starting Y coordinate
        dpi (int): Resolution for the image rendering, default is 300 for high quality.

    Returns:
        list: List of dictionaries containing section info
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    page = pdf_document[0]  # Access the first page
    
    # Render the page to an image with the specified dpi
    zoom = dpi / 72  # Standard DPI is 72, so we zoom by dpi/72
    mat = fitz.Matrix(zoom, zoom)  # Scale the image for higher resolution
    pix = page.get_pixmap(matrix=mat)  # Render page to a high-resolution image
    
    # Convert the pixmap to a Pillow Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    width, height = img.size

    # Sort sections by y_start to process them in order
    sections_config = sorted(sections_config, key=lambda x: x['y_start'])

    # Add y_end to each section based on next section's y_start
    sections_info = []
    for i, section in enumerate(sections_config):
        # For all sections except the last one
        if i < len(sections_config) - 1:
            y_end = sections_config[i + 1]['y_start']
        else:
            y_end = height

        # Ensure that y_start is less than y_end to avoid cropping errors
        y_start = section['y_start']
        if y_start >= y_end:
            print(f"Skipping section '{section['name']}' due to invalid coordinates: y_start={y_start}, y_end={y_end}")
            continue

        # Crop and save the section
        section_img = img.crop((0, y_start, width, y_end))
        output_path = os.path.join(output_dir, f"{section['name']}.png")
        section_img.save(output_path)

        # Store section information
        section_info = {
            "name": section['name'],
            "y_start": y_start,
            "y_end": y_end,
            "path": output_path
        }
        sections_info.append(section_info)

    pdf_document.close()  # Close the PDF document
    return sections_info

# Example usage
def main():
    pdf_path = "files/generated_pdfs/form_1.pdf"  # Replace with your PDF path
    output_dir = "files/sections"

    # Define your sections with custom names and Y-coordinates
    sections_config = [
        {"name": "header", "y_start": 0},
        {"name": "section1", "y_start": 400},
        {"name": "section2", "y_start": 600},
        {"name": "section3", "y_start": 1200},
        {"name": "section4", "y_start": 1750},
        {"name": "section5", "y_start": 2050}
    ]

    try:
        sections = split_pdf_page_custom(pdf_path, output_dir, sections_config, dpi=300)

        # Print information about each section
        for section in sections:
            print(f"Section: {section['name']}")
            print(f"Y-coordinates: {section['y_start']} to {section['y_end']}")
            print(f"Saved to: {section['path']}\n")

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    main()
