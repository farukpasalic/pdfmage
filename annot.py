import fitz  # PyMuPDF

# Open the PDF file
doc = fitz.open("zakon.pdf")

# Select the page to add the annotation to
page = doc[0]

# Define the position and size of the rectangle
rect = fitz.Rect(100, 100, 300, 200)

# Add the rectangle annotation
rect_annot = page.add_rect_annot(rect)

# Set the stroke color (RGB)
rect_annot.set_colors(stroke=(1, 0, 0))  # Red color

# Set the border width
rect_annot.set_border(width=2)

# Update the annotation to apply changes
rect_annot.update()

# Define the position for the text in the upper right corner of the rectangle
text_position = fitz.Rect(rect.x1 - 80, rect.y0 - 20, rect.x1, rect.y0)

# Add the text annotation
text_annot = page.add_freetext_annot(text_position, "Title", fontsize=12, fontname="helv")

# Set the border color of the text annotation (optional)
text_annot.set_colors(stroke=(0, 0, 1))  # Blue border for the text

# Set the border width of the text annotation (optional)
text_annot.set_border(width=1)

# Update the text annotation to apply changes
text_annot.update()

# Save the modified PDF
doc.save("annotated_example.pdf")

# Close the document
doc.close()
