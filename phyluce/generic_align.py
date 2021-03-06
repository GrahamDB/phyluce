#!/usr/bin/env python
# encoding: utf-8
"""
File: generic_align.py
Author: Brant Faircloth

Created by Brant Faircloth on 08 March 2012 12:03 PST (-0800)
Copyright (c) 2012 Brant C. Faircloth. All rights reserved.

Description: 

"""

import os
import re
import numpy
from collections import Counter
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import AlignIO
from Bio.Align import AlignInfo
from Bio.Alphabet import IUPAC, Gapped
from Bio.Align import MultipleSeqAlignment


class GenericAlign(object):
    """docstring for Align"""
    def __init__(self, input):
        self.input = input
        self.alignment = None
        self.trimmed = None

    def _clean(self, outtemp):
        if type(outtemp) is list:
            for f in outtemp:
                os.remove(f)
        else:
            os.remove(outtemp)
        # cleanup temp file
        try:
            os.remove(self.input)
        except:
            pass
    
    def _get_ends(self, seq):
        """find the start and end of sequence data for a given alignment row"""
        f = re.compile("^([-]+)")
        result = f.search(seq.seq.tostring())
        if result:
            start_gap = len(result.groups()[0])
        else:
            start_gap = 0
        r = re.compile("([-]+)$")
        result = r.search(seq.seq.tostring())
        if result:
            end_gap = len(result.groups()[0])
        else:
            end_gap = 0
        return start_gap, len(seq.seq) - end_gap

    def _gap_replacement(self, match, r='?'):
        """function called by replace_ends to add group of (missing data) characters"""
        if match.groups():
            return r * len(match.groups()[0])
        else:
            pass
    
    def _replace_ends(self, seq):
        """replace the ends of a given alignment with a character (usually gap/missing data)"""
        seq = re.sub('^([-]+)', self._gap_replacement, seq)
        seq = re.sub('([-]+)$', self._gap_replacement, seq)
        return seq

    def _alignment_consensus(self, alignment):
        """return consensus for an alignment object using BioPython"""
        consensus = AlignInfo.SummaryInfo(alignment).dumb_consensus()
        return consensus.tostring().replace('X', '-')

    def _read(self, format):
        """read an alignment from the CLI - largely for testing purposes"""
        self.alignment = AlignIO.read(open(self.input, 'rU'), format)

    def _record_formatter(self, trim, name):
        """return a string formatted as a biopython sequence record"""
        return SeqRecord(Seq(trim, Gapped(IUPAC.ambiguous_dna, "-?")),
            id=name,
            name=name,
            description=name)
    
    def running_average(self, alignment, window_size, threshold, proportion):
        """
        compute the running average of base differences on a column-by-column
        basis across and alignment.  only count those bases where there is
        sufficient data, determined by `proportion`. Filter out columns
        having sufficient data where running average is > `threshold`
        """
        # iterate across the columns of the alignment and determine presence
        # or absence of base-identity in the column
        good_alignment = []
        # get count of taxa in alignment
        taxa = len(alignment)
        # get what constitutes the count of characters we need to
        # make a "majority" (this could be < 50% by changing
        # proportion
        majority_of_characters = int(round(proportion * taxa, 0))
        for column in xrange(alignment.get_alignment_length()):
            # get the count of different bases in a column
            column_count = Counter(alignment[:, column])
            # don't start considering base differences until we
            # have data from > required_characters (meaning we've
            # past the gappy parts of a given alignment)
            if column_count['-'] <= majority_of_characters:
                # remove the insertion marker
                del column_count['-']
                # alignment is "good" where the count of identities
                # at a given base is >= 50% across all taxa
                if column_count.most_common(1)[0][1] >= majority_of_characters:
                    good_alignment.append(True)
                # alignment is "bad" when we have < majority_of_characters
                # identities at a given base.
                else:
                    good_alignment.append(False)
            # alignment is also "bad" when we have > majority_of_characters
            # gaps in a column
            else:
                good_alignment.append(False)
        # convert good_alignment to array
        good_alignment = numpy.array(good_alignment)
        # setup weights for running average
        weight = numpy.repeat(1.0, window_size) / window_size
        # compute running average - will have edge effect
        running_average = numpy.convolve(good_alignment, weight, 'same')
        # get all positions where identity == 1 - we'll need the first
        # and last
        good = numpy.where(running_average >= threshold)[0]
        try:
            start_clip = good[0]
            end_clip = good[-1]
        except IndexError:
            start_clip = None
            end_clip = None
        return start_clip, end_clip
    
    def stage_one_trimming(self, alignment, window_size, threshold, proportion):
        """
        First stage (of 3) alignment trimming to find and trim edges of a given
        alignment.  Calls running_average function above to determine reasonable
        alignment start and end trimming for the entire alignment block.
        """
        # get the trim positions that we determine begin and end "good"
        # alignments
        start, end = self.running_average(alignment, window_size, threshold, proportion)
        # create a new alignment object to hold our alignment
        s1_trimmed = MultipleSeqAlignment([], Gapped(IUPAC.ambiguous_dna, "-"))
        for sequence in alignment:
            if start >= 0 and end:
                trim = sequence[start:end]
                # ensure we don't just add a taxon with only gaps/missing
                # data
                if set(trim) != set(['-']) and set(trim) != (['?']):
                    s1_trimmed.append(sequence[start:end])
                else:
                    s1_trimmed = None
                    break
            else:
                s1_trimmed = None
                break
        return s1_trimmed
    
    def stage_two_trimming(self, s1_trimmed, window_size=5):
        """
        Alignment row-by-row trimming.  After stage one trimming, iterate
        over rows of alignment to find differences between the alignment
        consensus and the row of data.  Trim those ends coming before
        (or after at 3' end) a block of 5 contiguous highly conserved
        positions.  Goes to third round of filtering to remove edges that
        end up with only '----' characters to start or end alignment block.
        """
        # create new alignment object to hold trimmed alignment
        s2_trimmed = MultipleSeqAlignment([], Gapped(IUPAC.ambiguous_dna, "-?"))
        # get consensus of alignment in array form
        consensus_array = numpy.array(list(self._alignment_consensus(s1_trimmed)))
        # iterate over each alignment sequence
        for sequence in s1_trimmed:
            #if sequence.id == 'phaenicophaeus_curvirostris2':
            #    pdb.set_trace()
            start, end = self._get_ends(sequence)
            # convert sequence to array
            orig_seq_array = numpy.array(list(sequence))
            # trim down edge gaps so they do not exert undue influence
            # on the running average
            seq_array = orig_seq_array[start:end]
            compare = (seq_array == consensus_array[start:end])
            weight = numpy.repeat(1.0, window_size) / window_size
            # compute running average across window size
            running_average = numpy.convolve(compare, weight, 'same')
            # get first 5' and 3' positions where quality > 1 over
            # 5 positions ([True, True, True, True, True]). This helps
            # us find the ends of the alignment where there are likely
            # problems)
            gm = (running_average > 0.99)
            for i in xrange(gm.size):
                # get 5 value slices
                if numpy.all(gm[i:i+5] == True):
                    bad_start = i
                    break
            reversed_gm = gm[::-1]
            for i in xrange(reversed_gm.size):
                # get 5 value slices
                if numpy.all(reversed_gm[i:i+5] == True):
                    bad_end = reversed_gm.size - i
                    break
            orig_seq_array[:start + bad_start] = '-'
            orig_seq_array[start + bad_end:] = '-'
            trim = ''.join(orig_seq_array)
            # feed those up to replacement engine to set all
            # missing/trimmed data at edges to "?" which is
            # missing data designator
            #trim = self._replace_ends(trim)
            if set(trim) != set(['-']) and set(trim) != (['?']):
                s2_trimmed.append(self._record_formatter(trim, sequence.id))
            else:
                s2_trimmed = None
                break
        return s2_trimmed

    def trim_alignment(self, method='running', window_size=20, threshold=0.75, proportion=0.65):
        """
        Trim a given alignment from one of the alignment engines.  Uses three-pass
        approach - one to trim alignment block ends, one to trim row data, and a
        third to re-trim alignment block ends after trimming row data.
        
        Returns self.trimmed
        """
        if method == 'notrim':
            self.trimmed = self.alignment
        else:
            s1_trimmed = self.stage_one_trimming(self.alignment, window_size, threshold, proportion)
            s2_trimmed = self.stage_two_trimming(s1_trimmed)
            # cleanup any edges on which we've masked the data
            self.trimmed = self.stage_one_trimming(s2_trimmed, window_size, threshold, proportion)
        # report failed (complete) trimming
        if not self.trimmed:
            print "\tAlignment {0} dropped due to trimming".format(self.alignment._records[0].description)

if __name__ == '__main__':
    aln = GenericAlign('../test-data/uce-7117.nex')
    aln._read('nexus')
    aln.trim_alignment()
    outf = open('alignment-test.nex', 'w')
    outf.write(aln.trimmed.format('nexus'))
    outf.close()
    #pdb.set_trace()
