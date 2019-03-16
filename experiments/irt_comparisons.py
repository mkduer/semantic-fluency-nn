""" # TODO needed?
import os
os.chdir('..')
"""


from src.text.text_wrangler import Corpus
from gensim.models import Word2Vec
from src.graph.semantic_network import SemanticNetwork

from src.algorithms.simulated_annealing import SimulatedAnnealer
from src.algorithms.random_walk import RandomWalker
from src.algorithms.hill_climbing import HillClimber
from src.algorithms.irt import IRT

from src.visualization.irt_plot import IRTPlot
import numpy as np
import src.visualization.constants as C


def measure_algorithm_irts():
    """
    Runs the different algorithms using the same starting node and total iterations:
    - random walk
    - simulated annealing
    - discrete space random-start hill climbing

    The IRT of each algorithms resulting path is calculated and plotted
    """

    # Clean corpus and run through Word2Vec
    corpus = ['shakespeare.txt', 'fairy_tales.txt']
    clean_corpus = Corpus('docs/' + corpus[1])
    model = Word2Vec(clean_corpus.sentence_matrix, size=120,
                     window=5, min_count=5, workers=8, sg=1)

    # Create semantic network
    network = SemanticNetwork(embeddings=model.wv.vectors, aligned_keys=model.wv.index2word)

    # Train model
    for i in range(C.W2V_ETA):
        model.train(clean_corpus.sentence_matrix, total_examples=len(clean_corpus.sentence_matrix),
                    epochs=1, compute_loss=True)
        network.update(em_proportion=1, g_proportion=1, include_set=clean_corpus.nouns,
                       stop_set=clean_corpus.stopwords, thresh=0.8, verbose=True)

    # Run comparison algorithms
    repeat = True
    times_repeated = 0

    while repeat:
        start_node = None
        irt_totals = [0, 0, 0]
        sa_line, rw_line, hc_line = [], [], []

        if not C.RANDOM_NODE:
            start_node = C.START_NODE

        sim_annealing = SimulatedAnnealer(network.graph, initial_temp=1000, start=start_node)
        sa_path = sim_annealing.run(C.MAX_ITERATIONS)
        sa_irts = IRT.calculate(sa_path)
        print(f'iterate {C.MAX_ITERATIONS} times')
        print(f'simulated annealing_IRTs: {sa_irts}')
        if C.RANDOM_NODE:
            start_node = sa_path[0]

            if times_repeated > 0:
                start_node = sim_annealing.valid_start_node()
                times_repeated = 0

        walker = RandomWalker(network.graph, start_node)
        walker_path = walker.run(C.MAX_ITERATIONS)
        walker_irts = IRT.calculate(walker_path)
        print(f'random walker IRTs: {walker_irts}')

        climber = HillClimber(network.graph, start_node, C.MAX_ITERATIONS, repeat=0)
        climber_path = climber.run()
        climber_irts = IRT.calculate(climber_path)
        print(f'hill climber IRTs: {climber_irts}')

        # Gather IRT data
        for sa, walker, climber in zip(sa_irts, walker_irts, climber_irts):
            sa_line.append(sa[2])
            rw_line.append(walker[2])
            hc_line.append(climber[2])

        irt_totals = [np.sum(sa_line), np.sum(rw_line), np.sum(hc_line)]
        print(f'totals for (simulated annealing, random walker, hill climber): {irt_totals}')

        # make sure the data looks interesting by avoiding standalone start nodes
        for t in irt_totals:
            if not t:
                repeat = True
                times_repeated += 1
                print(f'REPEATING')  # TODO delete
                break
            repeat = False

    # generate plots for IRT representation
    plot = IRTPlot()
    algorithms = ['Simulated Annealing', 'Random Walk', 'Hill Climbing']
    plot.generate_plots(algorithms, 'total_irt', irt_totals,
                        'line_irt', [sa_line, rw_line, hc_line])


if __name__ == '__main__':
    measure_algorithm_irts()
