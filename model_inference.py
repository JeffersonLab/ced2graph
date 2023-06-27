#
# Script that
#  1) loads a pytorch model
#  2) reads a directory containing graph.pkl files
#  3) applies the pytorch model to generate inference embeddings
#  4) writes generated embeddings out to a file

import argparse
import os.path
import sys
import torch
import pickle as pkl
import numpy as np
import glob
from modules.util import progressBar

# The top-level directory from where data will be read
data_dir = None

# The glob pattern to find graph pkl files in data_dir
glob_pattern = "*.pkl"

# The file where embeddings will be written
output_file = "./embs.npy"

# The pytorch model to load and execute
model_file = None

analysis_lib = "../cebaf-graph-analyze"

# Define the program's command line arguments and build a parser to process them
def make_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Command Line Options')
    parser.add_argument("-g", type=str, dest='glob_pattern', default=glob_pattern,
                        help="Glob pattern to find graph pkl files")
    parser.add_argument("-o", type=str, dest='output_file', default=output_file,
                        help="Output file path/name")
    parser.add_argument("-d", type=str, dest='data_dir', required=True,
                        help="Path to directory containing graph pkl files")
    parser.add_argument("-m", type=str, dest='model_file', required=True,
                        help="Path to pytorch model file")
    parser.add_argument("-l", type=str, dest='analysis_lib', default="../cebaf-graph-analyze",
                        help="Path to cebaf-graph-analyze library")
    return parser


# The path and glob pattern for locating graph pickle files
def pickle_path():
    return data_dir + os.path.sep + "**" + os.path.sep + glob_pattern


if __name__ == "__main__":
    try:

        # Access the command line arguments
        args = make_cli_parser().parse_args()

        data_dir = args.data_dir
        glob_pattern = args.glob_pattern
        output_file = args.output_file
        model_file = args.model_file
        analysis_lib = args.analysis_lib

        # Add Song's analysis tools to library path
        sys.path.append('../cebaf-graph-analyze')

        # print("Data will be read from " + data_dir)
        # print("Glob pattern will be " + glob_pattern)
        # print("Model will be read from " + model_file)
        # print("Output will be written to " + output_file)
        # print("Analysis Library at " + analysis_lib)
        # print("Pickle Path is " + pickle_path())

        # load the model
        model = torch.load(model_file, map_location='cpu')
        model.use_cuda = False

        embs = []
        # for file_name in glob.glob(pickle_path(), recursive=True):
        for file_name in progressBar(glob.glob(pickle_path(), recursive=True),
                                     prefix='Processing graphs:', suffix='', length=50):
            graph = pkl.load(open(file_name, 'rb'))
            embs.append(model.encode(graph))         # run inference with model.encode()

        if len(embs) > 0:
            # save the final embeddings (as a matrix)
            struct = torch.stack(embs, 0).detach().cpu().numpy()
            np.save(output_file, struct)
            print('wrote ' + len(embs).__str__() + ' embeddings to ' + output_file)
        else:
            raise RuntimeError("Empty embeddings list.  Check data directory and glob pattern.")

        exit(0)

    except RuntimeError as err:
        print("Exception: ", err)
        exit(1)