#!/usr/bin/env python
# encoding: utf-8
"""
File: get_alignment_matrix_estimate.py
Author: Brant Faircloth

Created by Brant Faircloth on 02 May 2013 21:05 PDT (-0700)
Copyright (c) 2013 Brant C. Faircloth. All rights reserved.

Description: Query a probe.matches.sqlite database for
information about the eventual completeness of an alignment
matrix.

"""

import numpy
import sqlite3
import argparse
from collections import defaultdict
from phyluce.helpers import FullPaths, is_file

import pdb

def check_min_value(value):
    value = float(value)
    if value < 0 or value >= 1:
        raise argparse.ArgumentTypeError("The min value must be 0 < value < 1")
    return value

def check_max_value(value):
    value = float(value)
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError("The max value must be 0 <= value <= 1")
    return value

def get_args():
    """Get arguments from CLI"""
    parser = argparse.ArgumentParser(
            description="""Query a probes.matches.sqlite db for matrix completeness""")
    parser.add_argument(
            "db",
            type=is_file,
            action=FullPaths,
            help="""The probe.matches.sqlite database to query"""
        )
    parser.add_argument(
            "--min",
            type=check_min_value,
            default=0,
            help="""The minimum of the range to evaluate"""
        )
    parser.add_argument(
            "--max",
            type=check_max_value,
            default=1,
            help="""The maximum of the range to evaluate"""
        )
    parser.add_argument(
            "--step",
            type=check_max_value,
            default=0.1,
            help="""The step of the range to evaluate"""
        )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--exclude',
        type=str,
        default=None,
        nargs='+',
        help='Taxa to exclude')
    group.add_argument('--include',
        type=str,
        default=None,
        nargs='+',
        help='Taxa to include')
    return parser.parse_args()


def get_number_of_taxa_in_db(args, cur):
    """return the desired taxa in the db"""
    cur.execute("PRAGMA table_info(matches)")
    all_columns = cur.fetchall()
    if args.exclude is not None:
        excludes = set(args.exclude)
        taxa = [i[1] for i in all_columns[1:] if i[1] not in excludes]
    elif args.include is not None:
        includes = set(args.include)
        taxa = [i[1] for i in all_columns[1:] if i[1] in includes]
    else:
        taxa = [i[1] for i in all_columns[1:]]
    return taxa


def get_counts_of_hits_by_locus(cur, taxa):
    locus_counts = {}
    query = "SELECT uce,{} FROM matches".format(','.join(taxa))
    for row in cur.execute(query):
        locus = row[0]
        counts = [int(i) if i=='1' else 0 for i in row[1:]]
        locus_counts[locus] = sum(counts)
    return locus_counts


def get_cut_points(args, taxa):
    """docstring for get_cut_points"""
    fracs = numpy.arange(args.min, args.max, args.step)
    return fracs, numpy.around(taxa * fracs, decimals=0)


def get_bins_of_counts(args, num_taxa, locus_counts):
    """docstring for get_bins_of_counts"""
    # get cut points
    fracs, cuts = get_cut_points(args, num_taxa)
    frac_dict = defaultdict(list)
    for k, v in locus_counts.iteritems():
        bool_test = v < cuts
        positions = numpy.where(bool_test == True)[0]
        if positions.size == 0:
            frac_dict["{},{}".format(fracs[-1], cuts[-1])].append(1)
        else:
            # position is first hit - 1
            idx = positions[0] - 1
            frac_dict["{},{}".format(fracs[idx], cuts[idx])].append(1)
    return frac_dict


def main():
    """docstring for main"""
    args = get_args()
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    taxa = get_number_of_taxa_in_db(args, cur)
    print "There are {} taxa.".format(len(taxa))
    locus_counts = get_counts_of_hits_by_locus(cur, taxa)
    frac_dict = get_bins_of_counts(args, len(taxa), locus_counts)
    print "Freq(taxa present),Cut point,Loci"
    for k in sorted(frac_dict.keys()):
        print "{},{}".format(k, sum(frac_dict[k]))


if __name__ == '__main__':
    main()
