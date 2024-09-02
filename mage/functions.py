import numpy as np
from sklearn.metrics.pairwise import euclidean_distances

def custom_metric(a, b):
    # `a` and `b` are 1D arrays representing two points
    return np.sqrt((a[0]  - b[0])**2 + (a[1] - b[1])**2)


def euclidean_distance(point1, point2, wcoef=40, hcoef=1):
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
            distance = euclidean_distance(corner1, corner2, wcoef=1, hcoef=30)
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
