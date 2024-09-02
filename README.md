# PDFMage

PDFMage is a Python library designed to extract text from PDF files. It provides a simple and efficient way to parse PDF documents and retrieve their textual content.

## Features

- Extracts text from PDF files with high accuracy.
- Supports extraction from specific pages of a PDF.
- Provides a configurable interface for fine-tuning the extraction process.
- Includes debugging options for visualizing the extraction process.

## Usage

```
from mage import PDFMage
mage = PDFMage.PDFMage('path_to_your_pdf_file')
data = mage.extract_text()
print(data)
```

## Configuration

PDFMage provides a `Config` class to customize the behavior of the text extraction process. Here is an example of how to use it:

```python
from mage import PDFMage

# Create a Config instance
config = PDFMage.Config()

# Set the epsilon parameter for the DBSCAN algorithm when clustering words
config.cluster_words_eps = 12

# Create a PDFMage instance with the path to your PDF file and the configuration
mage = PDFMage.PDFMage('path_to_your_pdf_file', config)

# Extract text from the PDF
data = mage.extract_text()

# Print the extracted text
print(data)


```

## Configuration Options

The `Config` class in PDFMage provides several options to customize the text extraction process. Here is a description of each field:

- `output`: A string that specifies the path where the output will be stored.
- `extend_word_coordinates`: A tuple that specifies how much to extend the coordinates of the bounding boxes of the words.
- `cluster_words_eps`: An integer that sets the epsilon parameter for the DBSCAN algorithm when clustering words.
- `cluster_columns_eps`: An integer that sets the epsilon parameter for the DBSCAN algorithm when clustering columns.
- `debug_images`: A boolean that indicates whether to create debug images.
- `debug_words`: A boolean that indicates whether to draw bounding boxes around words in the debug images.
- `debug_clusters`: A boolean that indicates whether to draw bounding boxes around clusters in the debug images.
- `debug_columns`: A boolean that indicates whether to draw bounding boxes around columns in the debug images.
- `debug`: A boolean that indicates whether to enable debugging.
- `word_color`: A string that sets the color to use for the bounding boxes around words in the debug images.
- `cluster_color`: A string that sets the color to use for the bounding boxes around clusters in the debug images.
- `column_color`: A string that sets the color to use for the bounding boxes around columns in the debug images.

These fields can be set when creating a `Config` instance, which is then passed to the `PDFMage` constructor. This allows you to customize various aspects of the text extraction process.

## Output

Output directory from Config is a directory where debug images are stored. The debug images show the words, clusters, and columns detected during the text extraction process. 
The images can be useful for visualizing the extraction process and debugging any issues that may arise.

img directory includes some examples of extraction process.