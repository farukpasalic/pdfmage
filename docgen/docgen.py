from dataclasses import dataclass, field
from typing import List
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate


class TextFile:
    def __init__(self, filename):
        with open(filename, 'r') as file:
            self.buffer = file.read().split()
        self.pointer = 0

    def get_words(self, num_words):
        words = []
        for _ in range(num_words):
            words.append(self.buffer[self.pointer])
            self.pointer += 1
            if self.pointer >= len(self.buffer):
                self.pointer = 0
        return ' '.join(words)

@dataclass
class Section:
    id: int
    section_number: str
    subsections: List['Section']
    section_text: str

    def to_dict(self):
        return {
            'id': self.id,
            'section_number': self.section_number,
            'subsections': [sub.to_dict() for sub in self.subsections],
            'section_text': self.section_text
        }

    @classmethod
    def from_dict(cls, data):
        subsections = [cls.from_dict(sub) for sub in data['subsections']]
        return cls(data['id'], data['section_number'], subsections, data['section_text'])




def create_pdf(section, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    add_section_to_elements(section, elements)
    doc.build(elements)



from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)

    def showPage(self):
        self.setFont("Helvetica", 9)
        self.drawString(100, 100, str(self._pageNumber))
        canvas.Canvas.showPage(self)

def create_pdf_with_columns(section, filename, num_columns):
    doc = BaseDocTemplate(filename, pagesize=A4)
    frame_width = doc.width / num_columns
    frame_height = doc.height - 2 * inch  # leave space for the title
    margin = (doc.width - frame_width * num_columns) / 2  # margin on both sides
    frames = [Frame(margin + i * frame_width, 0, frame_width, frame_height) for i in range(num_columns)]
    title_frame = Frame(0, frame_height, doc.width, 2 * inch)  # frame for the title
    doc.addPageTemplates([
        PageTemplate(id='First', frames=[title_frame] + frames),  # first page with title
        PageTemplate(id='Later', frames=frames)  # later pages without title
    ])
    elements = []
    styles = getSampleStyleSheet()
    # Add the document title as a single column
    elements.append(Paragraph(section.section_text, styles["Title"]))
    elements.append(Spacer(1, 0.25 * inch))
    # Add the rest of the sections
    for subsection in section.subsections:
        add_section_to_elements(subsection, elements)
    doc.build(elements, canvasmaker=NumberedCanvas)



def add_section_to_elements(section, elements, depth=0):
    styles = getSampleStyleSheet()
    text = f"<b>{section.section_number}</b> {section.section_text}" if section.section_number else section.section_text
    if not section.section_number and not section.subsections:
        # This is a paragraph
        elements.append(Paragraph(text, styles["BodyText"]))
    elif not section.section_number:
        # This is the document title
        elements.append(Paragraph(text, styles["Title"]))
    else:
        # This is a heading
        heading_level = min(5, depth + 1)  # Heading levels go from 1 to 5
        elements.append(Paragraph(text, styles["Heading" + str(heading_level)]))
    for subsection in section.subsections:
        add_section_to_elements(subsection, elements, depth + 1)


# with open('doc.json', 'r') as f:
#     data = json.load(f)
#
# section = Section.from_dict(data)


#create_pdf(section, 'doc.pdf')
#create_pdf_with_columns(section, 'doc.pdf', 2)


import random

def generate_paragraph(text_file):
    return text_file.get_words(random.randint(30, 60))

def generate_section(text_file, depth, parent=None, sn=None):
    if depth == 0:
        # document title: no section number
        section_text = text_file.get_words(random.randint(3, 8)).upper()
        section = Section(0, '', [], section_text)
        children = [generate_section(text_file, depth + 1, section, sn=sn) for sn, _ in enumerate(range(random.randint(3, 5)), start=1)]
        for no, child in enumerate(children, start=1):
            child.section_number = no
        section.subsections.append(Section(0, '', [], generate_paragraph(text_file)))
        section.subsections.extend(children)
        return section
    elif depth == 1:
        section_text = text_file.get_words(random.randint(3, 5))
        section = Section(0, sn, [], section_text)
        children = [generate_section(text_file, depth + 1, section, sn=sn) for sn, _ in enumerate(range(random.randint(3, 5)), start=1)]
        for no, child in enumerate(children, start=1):
            child.section_number = str(sn) + "." + str(no)
        section.subsections = children
        return section
    elif depth == 2:
        section_text = text_file.get_words(random.randint(3, 5))
        children = [Section(i, '', [], generate_paragraph(text_file)) for i in range(random.randint(2, 6))]
        return Section(0, ':', children, section_text)
    else:
        return Section(0, '', [], '')

text_file = TextFile('words.txt')
root_section = generate_section(text_file, 0)

create_pdf(root_section, 'doc.pdf')

print(json.dumps(root_section.to_dict(), indent=2))