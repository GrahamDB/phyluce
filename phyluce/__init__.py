#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
(c) 2013 Brant Faircloth || http://faircloth-lab.org/
All rights reserved.

This code is distributed under a 3-clause BSD license. Please see
LICENSE.txt for more information.

Created on 26 December 2013 16:12 PST (-0800)
"""


from __future__ import absolute_import
import os
import subprocess

# get a dynamic version number, if possible.  if not running from git
# should default to static version
cwd = os.getcwd()
try:
    location = os.path.split(os.path.abspath(__file__))[0]
    os.chdir(location)
    cmd = [
        "git",
        "rev-parse",
        "--short",
        "HEAD"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = proc.communicate()
    if stdout.startswith("fatal:"):
        raise IOError("{}".format(stdout.strip()))
    else:
        __version__ = "git {}".format(stdout.strip())
    os.chdir(cwd)
except IOError:
    __version__ = "2.0.0"
    if not os.getcwd == cwd:
        os.chdir(cwd)
