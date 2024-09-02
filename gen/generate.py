from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

# Create a PDF document
pdf = SimpleDocTemplate("complex_document.pdf", pagesize=A4)

# Define styles
styles = getSampleStyleSheet()
title_style = styles['Title']
section_style = styles['Heading1']
subsection_style = styles['Heading2']
paragraph_style = styles['BodyText']

# Create content
content = []

# Add a title
title = Paragraph("Document Title", title_style)
content.append(title)
content.append(Spacer(1, 12))

# Add a section
section = Paragraph("Section 1", section_style)
content.append(section)
content.append(Spacer(1, 12))

# Add a subsection
subsection = Paragraph("Subsection 1.1", subsection_style)
content.append(subsection)
content.append(Spacer(1, 12))

# Add a paragraph
paragraph = Paragraph("This is a sample paragraph under subsection 1.1.", paragraph_style)
content.append(paragraph)
content.append(Spacer(1, 12))

# Add a page break
content.append(PageBreak())

# Add footer with page number
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman', 9)
    canvas.drawString(100, 20, "This is a footer")
    canvas.drawRightString(550, 20, f"Page {doc.page}")
    canvas.restoreState()

# Build PDF
pdf.build(content, onFirstPage=footer, onLaterPages=footer)
