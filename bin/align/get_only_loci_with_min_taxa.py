#!/usr/bin/env python
# encoding: utf-8

"""
get_counts_of_taxa_in_align.py

Created by Brant Faircloth on 16 August 2011.
Copyright 2011 Brant C. Faircloth. All rights reserved.

The program iterates through a folder of nexus files and returns the count
of alignments having more than "--percent" of "--taxa" taxa.
"""


import os
import math
import shutil
import argparse
import multiprocessing
from Bio import AlignIO
from phyluce.helpers import FullPaths, CreateDir, is_dir, get_alignment_files
from phyluce.log import setup_logging

#import pdb

def get_args():
    parser = argparse.ArgumentParser(
        description="Screen a directory of alignments, only returning those containing >= --percent of taxa",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--alignments",
        required=True,
        type=is_dir,
        action=FullPaths,
        help="The directory containing the nexus files"
    )
    parser.add_argument(
        "--taxa",
        required=True,
        type=int,
        help="The number of taxa expected"
    )
    parser.add_argument(
        "--output",
        action=CreateDir,
        help="The output dir in which to store copies of the alignments"
    )
    parser.add_argument(
        "--percent",
        type=float,
        default=0.75,
        help="The percent of taxa to require"
    )
    parser.add_argument(
        "--input-format",
        dest="input_format",
        choices=["fasta", "nexus", "phylip", "clustal", "emboss", "stockholm"],
        default="nexus",
        help="""The input alignment format.""",
    )
    parser.add_argument(
        "--verbosity",
        type=str,
        choices=["INFO", "WARN", "CRITICAL"],
        default="INFO",
        help="""The logging level to use."""
    )
    parser.add_argument(
        "--log-path",
        action=FullPaths,
        type=is_dir,
        default=None,
        help="""The path to a directory to hold logs."""
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=1,
        help="""Process alignments in parallel using --cores for alignment. """ +
        """This is the number of PHYSICAL CPUs."""
    )
    return parser.parse_args()

def copy_over_files(work):
    file, format, min_count, output = work
    aln = AlignIO.read(file, format)
    if len(aln) >= min_count:
        shutil.copyfile(file, os.path.join(output, os.path.basename(file)))
        return 1
    else:
        return 0

def main():
    args = get_args()
    # setup logging
    log, my_name = setup_logging(args)
    # find all alignments
    files = get_alignment_files(log, args.alignments, args.input_format)
    # determine the minimum count of taxa needed in each alignment, given --percent
    min_count = int(math.floor(args.percent * args.taxa))
    work = [[file, args.input_format, min_count, args.output] for file in files]
    if args.cores > 1:
        assert args.cores <= multiprocessing.cpu_count(), "You've specified more cores than you have"
        pool = multiprocessing.Pool(args.cores)
        results = pool.map(copy_over_files, work)
    else:
        results = map(copy_over_files, work)
    log.info("Copied {0} alignments of {1} total containing ≥ {2} proportion of taxa (n = {3})".format(
        sum(results),
        len(results),
        args.percent,
        min_count
    ))

if __name__ == '__main__':
    main()
