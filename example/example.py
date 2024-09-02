from mage import PDFMage

file_name = "../pdf/01-2021 Kanban Guide.pdf"


config = PDFMage.Config()

config.cluster_words_eps = 10
config.debug_words = False
config.debug_clusters = False
config.debug_columns = True


mage = PDFMage.PDFMage(file_name, config)

data = mage.extract_text(pages=[3])
print(f"Parsed: {len(data)} pages")

for p in data.keys():
    for col in data[p]:
        print(col.collect_text())
        print()