from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch

# Define a function to create headers and footers
def header_footer(canvas, doc):
    # Header
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 12)
    canvas.drawString(inch, 10.5 * inch, "Document Title")

    # Footer
    canvas.setFont('Helvetica', 10)
    canvas.drawString(inch, 0.75 * inch, f"Page {doc.page}")
    canvas.restoreState()

# Create a PDF document
pdf = SimpleDocTemplate("controlled_pages.pdf", pagesize=letter)

# Define a stylesheet
styles = getSampleStyleSheet()
style = styles["BodyText"]

# Content list
content = []

# Add some paragraphs
for i in range(1, 6):
    content.append(Paragraph(f"This is paragraph {i} on the first page.", style))
    content.append(Spacer(1, 12))

# Force a page break
content.append(PageBreak())

# Add content to the second page
for i in range(6, 11):
    content.append(Paragraph(f"This is paragraph {i} on the second page.", style))
    content.append(Spacer(1, 12))

# Build the PDF with the header and footer functions
pdf.build(content, onFirstPage=header_footer, onLaterPages=header_footer)
