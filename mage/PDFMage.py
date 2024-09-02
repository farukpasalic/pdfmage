import json
from typing import List
from mage.config import Config
import pdfplumber
import time
from pdf2image import convert_from_path
from PIL import ImageDraw
import numpy as np
from sklearn.cluster import DBSCAN
from mage.functions import min_bbox_distance, custom_metric
import os





class WordInfo:
    def __init__(self, text: str, size: int, x0: int, y0: int, x1: int, y1: int):
        self.text = text
        self.size = size
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1


class WordsCluster:
    def __init__(self, words: List[WordInfo], x0: int, y0: int, x1: int, y1: int):
        self.words = words
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.type = self.analyze_words()

    def analyze_words(self):
        cluster_type = 0
        for word in self.words:
            if word.text.isnumeric():
                cluster_type |= 1  # Set 1st bit
            elif word.text.isalpha():
                cluster_type |= 2  # Set 2nd bit
            elif not word.text.isalnum():
                cluster_type |= 4  # Set 3rd bit
        return cluster_type

    def add_words(self, words: List[WordInfo]):
        for word in words:
            if not any(existing_word.text == word.text and
                       existing_word.x0 == word.x0 and
                       existing_word.y0 == word.y0 and
                       existing_word.x1 == word.x1 and
                       existing_word.y1 == word.y1 for existing_word in self.words):
                self.words.append(word)
        self.type = self.analyze_words()

    def get_type(self):
        if self.type == 1:
            return "Numeric"
        elif self.type == 2:
            return "Alpha"
        elif self.type == 4:
            return "Special Characters"
        elif self.type == 3:
            return "Alpha and Numeric"
        elif self.type == 5:
            return "Numeric and Special Characters"
        elif self.type == 6:
            return "Alpha and Special Characters"
        elif self.type == 7:
            return "Alpha, Numeric and Special Characters"
        else:
            return "Unknown"

    def remove_duplicate_words(self):
        unique_words = []
        for word in self.words:
            if not any(existing_word.text == word.text and
                       existing_word.x0 == word.x0 and
                       existing_word.y0 == word.y0 and
                       existing_word.x1 == word.x1 and
                       existing_word.y1 == word.y1 for existing_word in unique_words):
                unique_words.append(word)
        self.words = unique_words

class WordsColumn:
    def __init__(self, clusters: List[WordsCluster], x0: int, y0: int, x1: int, y1: int):
        self.clusters = clusters
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def collect_text(self):
        text = []
        for cluster in self.clusters:
            for word in cluster.words:
                text.append(word.text)
            text.append('\n')
        return ' '.join(text)

class PDFMage:
    def __init__(self, path: str, config: Config):
        self.path = path
        self.config = config
        self.words = []

    def __debug(self, msg):
        if self.config.debug:
            print(msg)


    def __extract_words(self, page) -> List[WordInfo]:
        result: List[WordInfo] = []
        words = page.extract_words(keep_blank_chars=False, x_tolerance=4, y_tolerance=1)
        for word in words:
            word_info = WordInfo(word['text'], word['x1'] - word['x0'], word['x0'], word['top'], word['x1'], word['bottom'])
            result.append(word_info)
        return result

    def __extend_words_coordinates(self, words: List[WordInfo], x=1.0, y=1.0):
        for word in words:
            # Calculate the width and height of the bounding box
            width = word.x1 - word.x0
            height = word.y1 - word.y0

            new_width = width * x
            new_height = height * y

            # Calculate the new coordinates
            word.x0 = word.x0 - (new_width - width) / 2
            word.y0 = word.y0 - (new_height - height) / 2
            word.x1 = word.x1 + (new_width - width) / 2
            word.y1 = word.y1 + (new_height - height) / 2
        return words

    def __get_clusters_bounding_box(self, clusters: List[WordsCluster]):
        x0 = min(cluster.x0 for cluster in clusters)
        y0 = min(cluster.y0 for cluster in clusters)
        x1 = max(cluster.x1 for cluster in clusters)
        y1 = max(cluster.y1 for cluster in clusters)
        return {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1}

    def __create_image_from_page(self, file_name, page, words, clusters, columns, page_number, dpi=72):
        # Convert the PDF page to an image
        images = convert_from_path(file_name, dpi=dpi)
        image = images[page_number - 1]

        # Create a drawing context
        draw = ImageDraw.Draw(image)

        # Draw a red bounding box for each word
        if self.config.debug_words:
            for word in words:
               draw.rectangle([(word.x0, word.y0), (word.x1, word.y1)], outline=self.config.word_color, width=1)

        if self.config.debug_clusters:
            for cluster in clusters:
                draw.rectangle([(cluster.x0, cluster.y0), (cluster.x1, cluster.y1)],
                               outline=self.config.cluster_color, width=1)

        if self.config.debug_columns:
            for column in columns:
                coordinates = self.__get_clusters_bounding_box(column.clusters)
                draw.rectangle([(coordinates['x0'], coordinates['y0']), (coordinates['x1'], coordinates['y1'])],
                               outline=self.config.column_color, width=1)

        # Save the image
        if os.path.exists(self.config.output) is False:
            os.makedirs(self.config.output)
        image.save(f'{self.config.output}/page_{page_number}.png')

    def __cluster_words(self, words: List[WordInfo], eps: int) -> List[WordsCluster]:
        coords = [(word.x0, word.y0, word.x1, word.y1) for word in words]
        coords = np.array(coords)

        clustering = DBSCAN(eps=eps, min_samples=1, metric=min_bbox_distance).fit(coords)

        clusters = []
        for label in set(clustering.labels_):
            if label == -1:
                continue  # Ignore noise
            cluster_coords = coords[clustering.labels_ == label]
            x0, y0, _, _ = np.min(cluster_coords, axis=0)
            _, _, x1, y1 = np.max(cluster_coords, axis=0)
            cluster_words = [word for word in words if (word.x0 >= x0 and word.x1 <= x1 and
                                                        word.y0 >= y0 and word.y1 <= y1)]
            cluster = WordsCluster(cluster_words, x0, y0, x1, y1)
            clusters.append(cluster)
        return clusters


    def __merge_intersecting_clusters(self, clusters: List[WordsCluster]) -> List[WordsCluster]:
        merged_clusters = []

        while clusters:
            cluster = clusters.pop(0)
            intersecting_clusters = [c for c in clusters if not (cluster.x1 < c.x0 or cluster.x0 > c.x1 or
                                                                 cluster.y1 < c.y0 or cluster.y0 > c.y1)]
            for intersecting_cluster in intersecting_clusters:
                # Check if the x-coordinates of the clusters overlap
                if not (cluster.x1 < intersecting_cluster.x0 or cluster.x0 > intersecting_cluster.x1):
                    clusters.remove(intersecting_cluster)
                    cluster.x0 = min(cluster.x0, intersecting_cluster.x0)
                    cluster.y0 = min(cluster.y0, intersecting_cluster.y0)
                    cluster.x1 = max(cluster.x1, intersecting_cluster.x1)
                    cluster.y1 = max(cluster.y1, intersecting_cluster.y1)
                    cluster.add_words(intersecting_cluster.words)
            merged_clusters.append(cluster)

        return merged_clusters


    def __cluster_columns(self, clusters: List[WordsCluster], eps=200) -> List[WordsColumn]:

        coords = [((cluster.x0 + cluster.x1) / 2,
                   (cluster.y0 + cluster.y1) / 2) for cluster in clusters]

        coords = np.array(coords)

        clustering = DBSCAN(eps=eps, min_samples=1, metric=custom_metric).fit(coords)

        columns: List[WordsColumn] = []
        for label in set(clustering.labels_):
            if label == -1:
                continue  # Ignore noise
            column_clusters = [clusters[i] for i in range(len(clusters)) if clustering.labels_[i] == label]
            x0 = min(cluster.x0 for cluster in column_clusters)
            y0 = min(cluster.y0 for cluster in column_clusters)
            x1 = max(cluster.x1 for cluster in column_clusters)
            y1 = max(cluster.y1 for cluster in column_clusters)
            column = WordsColumn(sorted(column_clusters, key=lambda cluster: cluster.y0), x0, y0, x1, y1)
            columns.append(column)
        return columns

    def extract_text(self, pages=None):
        start_time = time.time()
        ret = {}
        with pdfplumber.open(self.path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):

                if pages and page_number not in pages:
                    continue

                self.__debug(f"Processing page {page_number}")
                words: List[WordInfo] = self.__extract_words(page)
                self.__debug(f"- Extracted {len(words)} words")
                words = self.__extend_words_coordinates(words, x=self.config.extend_word_coordinates[0], y=self.config.extend_word_coordinates[1])
                clusters = self.__cluster_words(words, self.config.cluster_words_eps)
                self.__debug(f"- Found {len(clusters)} clusters")
                clusters = self.__merge_intersecting_clusters(clusters)
                self.__debug(f"- Merged intersecting clusters. {len(clusters)} clusters")
                for cluster in clusters:
                    cluster.remove_duplicate_words()
                columns = self.__cluster_columns(clusters, self.config.cluster_columns_eps)
                self.__debug(f"- Found {len(columns)} columns")
                if self.config.debug_images:
                    self.__create_image_from_page(self.path, page, words, clusters, columns, page_number)

                ret[page_number] = columns

        end_time = time.time()
        self.__debug(f"Extraction took {end_time - start_time} seconds")
        return ret








