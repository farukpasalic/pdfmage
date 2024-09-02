import fitz  # PyMuPDF

# Open the PDF file
pdf_document = fitz.open("scrum.pdf")

# Iterate through each page
for page_num in range(len(pdf_document)):
    page = pdf_document.load_page(page_num)
    # Get all annotations on the page
    annotations = page.annots()


    for annot in annotations:
        # Check if the annotation is an image
        if annot.type[0] == fitz.PDF_ANNOT_WIDGET:  # Widget annotations (form fields) may contain images
            widget = annot.widget
            if widget and widget.get("image"):
                print(f"Page {page_num + 1} annotation contains an image.")
                img_data = widget.get("image")
                with open(f"page_{page_num + 1}_annotation_image.png", "wb") as img_file:
                    img_file.write(img_data)
        elif annot.type[0] == fitz.PDF_ANNOT_INLINE:  # Inline annotations (e.g., sticky notes) might contain images
            if annot.info.get("image"):
                print(f"Page {page_num + 1} annotation contains an image.")
                img_data = annot.info["image"]
                with open(f"page_{page_num + 1}_inline_annotation_image.png", "wb") as img_file:
                    img_file.write(img_data)

pdf_document.close()
