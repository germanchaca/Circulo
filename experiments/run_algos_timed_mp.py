import importlib
import igraph
import time
import pickle
from functools import partial
from circulo import metrics
from circulo.wrappers import community
import argparse
import os
from circulo.algorithms.overlap import CrispOverlap
import datetime
import multiprocessing

OUTPUT_DIR = "outputs"

def to_cover(result):
    cover = None
    if isinstance(result, igraph.VertexClustering):
        cover = result.as_cover()
    elif isinstance(result, igraph.VertexDendrogram):
        cover = result.as_clustering().as_cover()
    elif isinstance(result,CrispOverlap):
        cover = result.as_cover()
    elif isinstance(result, igraph.VertexCover):
        cover = result
    else:
        raise Exception("Algorithm output type not recognized")
    return cover



#def run_single(algo, dataset, output_dir, iterations):
def run_single(parameters):

    algo = parameters[1][0]
    dataset = parameters[1][1]
    output_dir = parameters[1][2]
    iterations = parameters[1][3]

    # Get dataset and run cd algorithm
    data_mod = importlib.import_module('data.'+dataset+'.run')

    # Get community covers
    cc, stochastic = getattr(community, 'comm_'+algo)(data_mod)

    vc_name = dataset + '-' + algo
    vc = []
    elapsed = []

    for i in range(iterations*stochastic + 1):
        t0 = time.time()
        vc += [to_cover(cc())]
        t_diff = time.time() - t0
        elapsed = [t_diff]
        #print('size of clusters = {0}'.format(sorted(vc[i].sizes(),reverse=True)))

    # Save results
    results = {}
    results['vc_name'] = vc_name
    results['elapsed'] = elapsed
    results['vc'] = vc

    with open(os.path.join(output_dir, vc_name + '.pickle'), 'wb') as f:
        pickle.dump(results, f)

    print("Finished", algo, "algorithm with", dataset, "dataset at", datetime.datetime.now())
    


def run(algos, datasets, output_dir, iterations):

    #create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    mp_data = ()
    for algo in algos:
        for dataset in datasets:
            mp_data = mp_data + ([algo + ' - ' + dataset, [algo, dataset, output_dir, iterations]], )
    p = multiprocessing.Pool(2)
    p.map(run_single, mp_data)
    p.close()
    p.join()

def main():

    comm_choices = [ a.replace('comm_', '') for a in dir(community) if a.startswith('comm_')]
    comm_choices.append('ALL')
    data_choices = ['football', 'congress_voting', 'karate', 'malaria', 'nba_schedule', 'netscience', 'flights', 'ALL']

    # Parse user input
    parser = argparse.ArgumentParser(description='Run community detection on a dataset.')
    parser.add_argument('dataset', nargs=1,choices=data_choices,help='dataset name. ALL will use all datasets')
    parser.add_argument('algo', nargs=1,choices=comm_choices,help='Which community detection to run.')
    parser.add_argument('--output', type=str, nargs=1, default=[OUTPUT_DIR], help='Base output directory')
    parser.add_argument('--samples', type=int, nargs=1, default=[10], help='Number of samples for stochastic algos')

    args = parser.parse_args()

    if 'ALL' in args.algo[0]:
        algos = ['infomap', 'fastgreedy']
    else:
        algos = args.algo[0]


    if 'ALL' in args.dataset[0]:
        data_choices.remove('ALL')
        datasets = data_choices
    else:
        datasets = args.dataset[0]

    overall_start_time = datetime.datetime.now()
    run(algos, datasets, args.output[0], args.samples[0]) 
    overall_end_time = datetime.datetime.now()
    print("Time elapsed:", (overall_end_time - overall_start_time))

if __name__ == "__main__":
    main()