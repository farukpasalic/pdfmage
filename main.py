import sys

import pdfplumber
from PIL import Image, ImageDraw
from pdf2image import convert_from_path
from sklearn.cluster import DBSCAN
import numpy as np
import fitz


FILE_NAME = 'kanban.pdf'


def euclidean_distance(point1, point2, wcoef=1, hcoef=1):
    return np.sqrt(wcoef*(point1[0] - point2[0]) ** 2 + hcoef*(point1[1] - point2[1]) ** 2)


def bbox_corners(bbox):
    x_min, y_min, x_max, y_max = bbox
    return [
        (x_min, y_min),  # top-left
        (x_max, y_min),  # top-right
        (x_min, y_max),  # bottom-left
        (x_max, y_max)  # bottom-right
    ]


def min_bbox_distance(bbox1, bbox2):
    corners1 = bbox_corners(bbox1)
    corners2 = bbox_corners(bbox2)

    min_distance = float('inf')

    for corner1 in corners1:
        for corner2 in corners2:
            distance = euclidean_distance(corner1, corner2, wcoef=1, hcoef=1)
            if distance < min_distance:
                min_distance = distance

    return min_distance


def weighted_metric(x, y):
    dx = x[0] - y[0]  # difference in x-coordinates
    dy = x[1] - y[1]  # difference in y-coordinates
    return np.sqrt(dx ** 2 + 3*dy ** 2)


def bbox_distance(bbox1, bbox2):
    # Extract coordinates of the bounding boxes
    x1, y1, x1_max, y1_max = bbox1
    x2, y2, x2_max, y2_max = bbox2

    # Calculate centroids of the bounding boxes
    centroid1 = ((x1 + x1_max) / 2, (y1 + y1_max) / 2)
    centroid2 = ((x2 + x2_max) / 2, (y2 + y2_max) / 2)

    # Calculate Euclidean distance between centroids
    distance = ((centroid1[0] - centroid2[0]) ** 2 + (centroid1[1] - centroid2[1]) ** 2) ** 0.5
    return distance

def cluster_words(words, eps=50):
    coords = [tuple(word['coordinates'].values()) for word in words]
    ws = [word for word in words]
    coords = np.array(coords)
    ws = np.array(ws)

    clustering = DBSCAN(eps=eps, min_samples=1, metric=min_bbox_distance).fit(coords)

    clusters = []
    for label in set(clustering.labels_):
        if label == -1:
            continue  # Ignore noise
        cluster_coords = coords[clustering.labels_ == label]
        cluster_words = ws[clustering.labels_ == label]
        x0, y0, _, _ = np.min(cluster_coords, axis=0)
        _, _, x1, y1 = np.max(cluster_coords, axis=0)
        cluster = {
            'coordinates': {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1},
            'words': []
        }
        for word in words:
            word_coords = word['coordinates']
            if (word_coords['x0'] >= x0 and word_coords['x1'] <= x1 and
                word_coords['y0'] >= y0 and word_coords['y1'] <= y1):
                cluster['words'].append(word)
        clusters.append(cluster)
    return clusters

def get_clusters_bounding_box(clusters):
    x0 = min(cluster['coordinates']['x0'] for cluster in clusters)
    y0 = min(cluster['coordinates']['y0'] for cluster in clusters)
    x1 = max(cluster['coordinates']['x1'] for cluster in clusters)
    y1 = max(cluster['coordinates']['y1'] for cluster in clusters)
    return {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}


def create_image_from_page(page, words, clusters, columns,  page_number, dpi=72):
    # Convert the PDF page to an image
    images = convert_from_path(FILE_NAME, dpi=dpi)
    image = images[page_number-1]

    # Create a drawing context
    draw = ImageDraw.Draw(image)

    # Draw a red bounding box for each word
    # for word in words:
    #    coordinates = word['coordinates']
    #    draw.rectangle([(coordinates['x0'], coordinates['y0']), (coordinates['x1'], coordinates['y1'])], outline='red')

    # Draw a green bounding box for each cluster
    for cluster in clusters:
        coordinates = cluster['coordinates']
        draw.rectangle([(coordinates['x0'], coordinates['y0']), (coordinates['x1'], coordinates['y1'])], outline='green', width=1)

    for column in columns:
        coordinates = get_clusters_bounding_box(column['clusters'])
        draw.rectangle([(coordinates['x0'], coordinates['y0']), (coordinates['x1'], coordinates['y1'])], outline='blue', width=1)


    # Save the image
    image.save(f'output/page_{page_number}.png')

def extract_words_with_coordinates(page):
    result = []
    words = page.extract_words(keep_blank_chars=False, x_tolerance=4, y_tolerance=1)
    for word in words:
        word_info = {
            'text': word['text'],
            'size': word['x1'] - word['x0'],
            'coordinates': {
                'x0': word['x0'],
                'y0': word['top'],
                'x1': word['x1'],
                'y1': word['bottom']
            }
        }
        result.append(word_info)
    return result

def extend_coordinates(words, x=1.0, y=1.0):
    extended_words = []
    for word in words:
        # Calculate the width and height of the bounding box
        width = word['coordinates']['x1'] - word['coordinates']['x0']
        height = word['coordinates']['y1'] - word['coordinates']['y0']

        # Increase the dimensions by 15%
        new_width = width * x
        new_height = height * y

        # Calculate the new coordinates
        x0 = word['coordinates']['x0'] - (new_width - width) / 2
        y0 = word['coordinates']['y0'] - (new_height - height) / 2
        x1 = word['coordinates']['x1'] + (new_width - width) / 2
        y1 = word['coordinates']['y1'] + (new_height - height) / 2




        # Update the coordinates in the word dictionary
        word['coordinates'] = {
            'x0': x0,
            'y0': y0,
            'x1': x1,
            'y1': y1
        }

        extended_words.append(word)
    return extended_words

def check_word_image_overlap(page, words):
    # Extract the images from the page
    images = page.rects

    for word in words:
        word_coords = word['coordinates']
        for image in images:
            # Check if the word's bounding box overlaps with the image's bounding box
            overlap = not (word_coords['x1'] < image['x1'] or
                           word_coords['x0'] > image['x0'] or
                           word_coords['y1'] < image['y1'] or
                           word_coords['y0'] > image['y0'])
            if overlap:
                print(f"The word '{word['text']}' overlaps with an image.")

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

            intersecting_cluster['words'].extend(cluster['words'])
        else:
            merged_clusters.append(cluster)

    return merged_clusters

def fitz_extract_image_bounding_boxes(fitz_page):

    image_list = fitz_page.get_images(full=True)
    for image in image_list:
        x0, y0, x1, y1 = image['bbox']
        print(f"Image {image['id']} on page {page_number+1} has bounding box: x0={x0}, y0={y0}, x1={x1}, y1={y1}")



cnt = 1


import fitz

def sort_words_in_clusters(clusters):
    for cluster in clusters:
        cluster['words'].sort(key=lambda word: (word['coordinates']['y0'], word['coordinates']['x0']))
    return clusters

def cluster_columns(clusters, eps=200):
    coords = [((cluster['coordinates']['x0'] + cluster['coordinates']['x1']) / 2,
               (cluster['coordinates']['y0'] + cluster['coordinates']['y1']) / 2) for cluster in clusters]
    #coords = [tuple(cluster['coordinates'].values()) for cluster in clusters]
    coords = np.array(coords)

    clustering = DBSCAN(eps=eps, min_samples=1).fit(coords)

    columns = []
    for label in set(clustering.labels_):
        if label == -1:
            continue  # Ignore noise
        column_clusters = [clusters[i] for i in range(len(clusters)) if clustering.labels_[i] == label]
        x0 = min(cluster['coordinates']['x0'] for cluster in column_clusters)
        y0 = min(cluster['coordinates']['y0'] for cluster in column_clusters)
        x1 = max(cluster['coordinates']['x1'] for cluster in column_clusters)
        y1 = max(cluster['coordinates']['y1'] for cluster in column_clusters)
        column = {
            'coordinates': {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1},
            'clusters': sorted(column_clusters, key=lambda cluster: cluster['coordinates']['y0'])
        }
        columns.append(column)
    return columns

pc = 1
with pdfplumber.open(FILE_NAME) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        print(f"Processing page {page_number}...")
        words = extract_words_with_coordinates(page)
        # words = extend_coordinates(words, x=1.3, y=1.0)
        # clusters = cluster_words(words, eps=8)
        words = extend_coordinates(words, x=1.3, y=1.0)
        clusters = cluster_words(words, eps=8)
        clusters = merge_intersecting_clusters(clusters)
        #clusters = sort_words_in_clusters(clusters)
        columns = cluster_columns(clusters, eps=200)


        for column in columns:
            for cluster in column['clusters']:
                text = [w['text'] for w in cluster['words']]
                print(" ".join(text))

        create_image_from_page(page, words, clusters, columns,  page.page_number, dpi=72)
        # if pc == 3:
        #     break
        # pc += 1
        print(len(words))




