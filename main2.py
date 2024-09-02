import sys
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
from sklearn.cluster import DBSCAN
import numpy as np

def extract_words_with_coordinates(page):
    result = []
    words = page.get_text()
    for word in words:
        word_info = {
            'text': word[4],
            'size': word[2] - word[0],
            'coordinates': {
                'x0': word[0],
                'y0': word[1],
                'x1': word[2],
                'y1': word[3]
            }
        }
        result.append(word_info)
    return result

def create_image_from_page(page, words, clusters,  page_number, dpi=72):
    # Convert the PDF page to an image
    pix = page.getPixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Create a drawing context
    draw = ImageDraw.Draw(img)

    # Draw a green bounding box for each cluster
    for cluster in clusters:
        coordinates = cluster['coordinates']
        draw.rectangle([(coordinates['x0'], coordinates['y0']), (coordinates['x1'], coordinates['y1'])], outline='green', width=1)

    # Save the image
    img.save(f'page_{page_number}.png')

def check_word_image_overlap(page, words):
    # Extract the images from the page
    images = page.get_images(full=True)

    for word in words:
        word_coords = word['coordinates']
        for image in images:
            # Check if the word's bounding box overlaps with the image's bounding box
            overlap = not (word_coords['x1'] < image[0] or
                           word_coords['x0'] > image[0] or
                           word_coords['y1'] < image[1] or
                           word_coords['y0'] > image[1])
            if overlap:
                print(f"The word '{word['text']}' overlaps with an image.")

# The rest of the functions (weighted_metric, cluster_words, extend_coordinates, merge_intersecting_clusters) remain the same

def extend_coordinates(words):
    extended_words = []
    for word in words:
        # Calculate the width and height of the bounding box
        width = word['coordinates']['x1'] - word['coordinates']['x0']
        height = word['coordinates']['y1'] - word['coordinates']['y0']

        # Increase the dimensions by 15%
        width *= 1.2
        height *= 1.2

        # Calculate the new coordinates
        x0 = word['coordinates']['x0'] - width * 0.075
        y0 = word['coordinates']['y0'] - height * 0.075
        x1 = word['coordinates']['x1'] + width * 0.075
        y1 = word['coordinates']['y1'] + height * 0.075

        # Update the coordinates in the word dictionary
        word['coordinates'] = {
            'x0': x0,
            'y0': y0,
            'x1': x1,
            'y1': y1
        }

        extended_words.append(word)
    return extended_words

def weighted_metric(x, y):
    dx = x[0] - y[0]  # difference in x-coordinates
    dy = x[1] - y[1]  # difference in y-coordinates
    return np.sqrt(2*dx ** 2 + 4*dy ** 2)  # weight of 2 for x, 1 for y

def cluster_words(words, eps=50):
    # Prepare the data for clustering
    coords = [list(word['coordinates'].values()) for word in words]
    ws = [word for word in words]
    coords = np.array(coords)
    ws = np.array(ws)

    # Perform DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=1, metric=weighted_metric).fit(coords)

    # Calculate the bounding boxes for each cluster
    clusters = []
    for label in set(clustering.labels_):
        if label == -1:
            continue  # Ignore noise
        cluster_coords = coords[clustering.labels_ == label]
        cluster_words = ws[clustering.labels_ == label]
        x0, y0, _, _ = np.min(cluster_coords, axis=0)
        _, _, x1, y1 = np.max(cluster_coords, axis=0)
        clusters.append({'coordinates': {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}})
    return clusters

def merge_intersecting_clusters(clusters):
    merged_clusters = []

    for cluster in clusters:
        intersecting_cluster = None
        for merged_cluster in merged_clusters:
            if not (cluster['coordinates']['x1'] < merged_cluster['coordinates']['x0'] or
                    cluster['coordinates']['x0'] > merged_cluster['coordinates']['x1'] or
                    cluster['coordinates']['y1'] < merged_cluster['coordinates']['y0'] or
                    cluster['coordinates']['y0'] > merged_cluster['coordinates']['y1']):
                intersecting_cluster = merged_cluster
                break

        if intersecting_cluster is not None:
            intersecting_cluster['coordinates']['x0'] = min(intersecting_cluster['coordinates']['x0'], cluster['coordinates']['x0'])
            intersecting_cluster['coordinates']['y0'] = min(intersecting_cluster['coordinates']['y0'], cluster['coordinates']['y0'])
            intersecting_cluster['coordinates']['x1'] = max(intersecting_cluster['coordinates']['x1'], cluster['coordinates']['x1'])
            intersecting_cluster['coordinates']['y1'] = max(intersecting_cluster['coordinates']['y1'], cluster['coordinates']['y1'])
        else:
            merged_clusters.append(cluster)

    return merged_clusters

cnt = 1
file_path = "test.pdf"
doc = fitz.open(file_path)
for page_number in range(20, min(25, len(doc))):
    page = doc[page_number]
    words = extract_words_with_coordinates(page)
    words = extend_coordinates(words)
    clusters = cluster_words(words, 40)
    clusters = merge_intersecting_clusters(clusters)
    create_image_from_page(page, words, clusters, page.number + 1, dpi=72)
    print(len(words))
    if cnt == 5:
        sys.exit()
    cnt += 1