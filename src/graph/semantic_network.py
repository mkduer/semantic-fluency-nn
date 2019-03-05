import numpy as np

from src.graph.Graph import UndirectedGraph
from sklearn.metrics.pairwise import cosine_similarity


class SemanticNetwork:
    def __init__(self, model):
        self.embedding_matrix = model.wv.vectors
        self.vocab = model.wv.vocab
        self.key_to_index = {}
        self.index_to_key = {}
        self.graph = UndirectedGraph()

        self._init_maps()
        self._init_graph()

    def update_semantic_network(self, em_proportion=0.1, g_proportion=0.1, stop_set=set(), thresh=0.7, verbose=False):
        em_subset = np.array(
            [idx for idx in _select_subset(
                self.embedding_matrix, self.embedding_matrix.shape[0], subset_proportion=em_proportion
            ) if self.index_to_key[idx] not in stop_set]
        )
        g_subset = np.array(
            [idx for idx in _select_subset(
                self.graph.adjacency_matrix, len(self.graph.nodes), subset_proportion=g_proportion
            ) if self.index_to_key[idx] not in stop_set]
        )
        em_vectors = self.embedding_matrix[em_subset,]
        g_vectors = self.embedding_matrix[g_subset,]
        cos_sims = cosine_similarity(em_vectors, g_vectors)

        updated = 0
        for i, em_i in enumerate(em_subset):
            for j, g_j in enumerate(g_subset):
                if cos_sims[i, j] >= thresh:
                    self.graph.add_edge(self.index_to_key[em_i], self.index_to_key[g_j], cos_sims[i, j])
                    updated += 1
        if verbose:
            print("Updated {} edges".format(updated))

    def _init_maps(self):
        for k, v in self.vocab.items():
            self.key_to_index[k] = v.index
            self.index_to_key[v.index] = k

    def _init_graph(self):
        for i in range(self.embedding_matrix.shape[0]):
            self.graph.add_node(self.index_to_key[i])


def _select_subset(matrix, matrix_height, subset_proportion=0.1):
    subset_size = int(matrix_height * subset_proportion)
    sample_indices = np.random.choice(matrix_height, size=subset_size, replace=False)
    return sample_indices