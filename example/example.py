from mage import PDFMage

file_name = "../kanban.pdf"
config = PDFMage.Config()
mage = PDFMage.PDFMage(file_name, config)

data = mage.extract_text(pages=[1, 2, 3])
print(f"Parsed: {len(data)} pages")

for p in data.keys():
    for col in data[p]:
        print(col.collect_text())
        print()