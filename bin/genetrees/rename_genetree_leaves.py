#!/usr/bin/env python
# encoding: utf-8
"""
File: rename_genetree_leaves.py
Author: Brant Faircloth

Created by Brant Faircloth on 21 April 2012 15:04 PDT (-0700)
Copyright (c) 2012 Brant C. Faircloth. All rights reserved.

Description: Given an input genetree file, rename the leaves according
to values in a configuration file

"""

import os
import sys
import dendropy
import argparse
import ConfigParser

import pdb


def get_args():
    """Get arguments from CLI"""
    parser = argparse.ArgumentParser(
            description="""Rename the leaves of an input tree""")
    parser.add_argument(
            "input",
            help="""The input tree file"""
        )
    parser.add_argument(
            "config",
            help="""A python config file mapping one name to another"""
        )
    parser.add_argument(
            "output",
            help="""The output tree file"""
        )
    parser.add_argument(
            "--input-format",
            dest='input_format',
            choices=['nexus', 'newick', 'fasta', 'phylip'],
            default='nexus',
            help="""The tree file format"""
        )
    parser.add_argument(
            "--output-format",
            dest='output_format',
            choices=['nexus', 'newick', 'fasta', 'phylip'],
            default='nexus',
            help="""The tree file format"""
        )
    parser.add_argument(
            "--longnames",
            action="store_true",
            default=False,
            help="""Convert full species names on tips""",
        )
    return parser.parse_args()


def main():
    args = get_args()
    conf = ConfigParser.ConfigParser()
    conf.read(args.config)
    if not args.longnames:
        names = conf.items('map')
    else:
        names = conf.items('longnames')
    names = dict([(name[0].upper(), name[1]) for name in names])
    trees = dendropy.TreeList(stream=open(args.input), schema=args.input_format)
    new_labels = []
    for tree in trees:
        for leaf in tree.leaf_nodes():
            if leaf.taxon.label in new_labels:
                pass
            else:
                new_label = names[leaf.taxon.label.upper()] + " - " + leaf.taxon.label
                new_labels.append(new_label)
                leaf.taxon.label = new_label
    trees.write_to_path(args.output, args.output_format)


if __name__ == '__main__':
    main()
