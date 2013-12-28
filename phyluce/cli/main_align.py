#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
(c) 2013 Brant Faircloth || http://faircloth-lab.org/
All rights reserved.

This code is distributed under a 3-clause BSD license. Please see
LICENSE.txt for more information.

Created on 27 December 2013 13:12 PST (-0800)
"""

from __future__ import absolute_import
import sys

from phyluce.cli import sub_align_mafft
from phyluce.cli import sub_align_muscle
from phyluce.cli import sub_align_stats


descr = "Alignment routines for UCE (and other) FASTA data."


def configure_parser(sub_parsers):
    if len(sys.argv) == 2:
        sys.argv.append("-h")
    p = sub_parsers.add_parser(
        'align',
        description=descr,
        help=descr
    )

    sub_parsers = p.add_subparsers(
        metavar="command",
        dest="cmd",
    )

    sub_align_mafft.configure_parser(sub_parsers, engine="mafft")
    sub_align_muscle.configure_parser(sub_parsers, engine="muscle")
    sub_align_stats.configure_parser(sub_parsers)