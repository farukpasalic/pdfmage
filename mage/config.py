from dataclasses import dataclass
@dataclass
class Config:
    output: str = '../output'
    extend_word_coordinates: tuple = (1.0, 1.0)
    cluster_words_eps: int = 12
    cluster_columns_eps: int = 200
    debug_images: bool = True
    debug_words: bool = False
    debug_clusters: bool = True
    debug_columns: bool = False
    debug: bool = True
    word_color: str = 'orange'
    cluster_color: str = 'green'
    column_color: str = 'blue'