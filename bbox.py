import fitz  # PyMuPDF
from PIL import Image, ImageDraw


def draw_bounding_boxes_on_page(pdf_path, page_number, bounding_boxes):
    # Open the PDF file
    document = fitz.open(pdf_path)

    # Get the specified page
    page = document.load_page(page_number)

    # Convert the page to an image
    page_pixmap = page.get_pixmap()

    # Convert the pixmap to a PIL Image
    image = Image.frombytes("RGB", [page_pixmap.width, page_pixmap.height], page_pixmap.samples)

    # Create a draw object
    draw = ImageDraw.Draw(image)

    # Draw the bounding boxes on the image
    for box in bounding_boxes:
        draw.rectangle(box['bbox'], outline='red')

    # Save the image
    image.save(f'{pdf_path}_page_{page_number}_with_boxes.png')

def extract_bounding_boxes(pdf_path, page_number):
    # Open the PDF file
    document = fitz.open(pdf_path)

    # Get the specified page
    page = document.load_page(page_number)

    # Extract text and objects from the page
    page_text = page.get_text("dict")

    # List to store bounding boxes
    bounding_boxes = []

    # Extract bounding boxes of text blocks
    for block in page_text["blocks"]:
        bbox = block["bbox"]
        bounding_boxes.append({"type": "text", "bbox": bbox})

        # If you need to extract bounding boxes of lines or spans within the block
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bbox = span["bbox"]
                bounding_boxes.append({"type": "span", "bbox": bbox})

    # Extract bounding boxes of images
    images = page.get_images(full=True)
    for img_index, img in enumerate(images):
        xref = img[0]
        image_info = document.extract_image(xref)
        bbox = img[2:6]
        bounding_boxes.append({"type": "image", "bbox": bbox})

    return bounding_boxes


# Example usage
pdf_path = "test.pdf"
page_number = 0  # Page numbers start from 0
bounding_boxes = extract_bounding_boxes(pdf_path, page_number)
draw_bounding_boxes_on_page(pdf_path, page_number, bounding_boxes)

# for box in bounding_boxes:
#     print(f"Type: {box['type']}, Bounding Box: {box['bbox']}")
