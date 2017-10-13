#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import argparse
import logging
import os
import re
import time
from datetime import datetime, timedelta

from browser.evaluator import BrowserBisector
from core.bisect import Bisector

log = logging.getLogger('autobisect')


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Autobisection tool for Mozilla Firefox and Spidermonkey',
        usage='%(prog)s <command> [options]')

    global_args = argparse.ArgumentParser(add_help=False)
    global_args.add_argument('repo_dir', help='Path of repository')
    global_args.add_argument('build_dir', help='Path to store build')
    global_args.add_argument('testcase', help='Path to testcase')
    global_args.add_argument('-start', help='Known good revision (default: earliest known working)')
    global_args.add_argument('-end', default='tip', help='Known bad revision (default: tip')
    global_args.add_argument('-skip', nargs='+', action='store',
                             help='A revset expression representing the revisions to skip (example: (x::y)')

    subparsers = parser.add_subparsers(dest='target')

    firefox_sub = subparsers.add_parser('firefox', parents=[global_args], help='Perform bisection for Firefox builds')
    general_args = firefox_sub.add_argument_group('build arguments')
    general_args.add_argument('--asan', action='store_true', help='Test asan builds')
    general_args.add_argument('--debug', action='store_true', help='Test debug builds')

    ffp_args = firefox_sub.add_argument_group('launcher arguments')
    ffp_args.add_argument('--extension',
                          help='Install the fuzzPriv extension (specify path to funfuzz/dom/extension)')
    ffp_args.add_argument('--timeout', type=int, default=60,
                          help='Iteration timeout in seconds (default: %(default)s)')
    ffp_args.add_argument('--launch-timeout', type=int, default=300,
                          help='Number of seconds to wait for firefox to become responsive after launching. '
                               '(default: %(default)s)')
    ffp_args.add_argument('--prefs', help='prefs.js file to use')
    ffp_args.add_argument('--profile', help='Profile to use. (default: a temporary profile is created)')
    ffp_args.add_argument('--memory', type=int, help='Process memory limit in MBs (Requires psutil)')
    ffp_args.add_argument('--gdb', action='store_true', help='Use GDB')
    ffp_args.add_argument('--valgrind', action='store_true', help='Use valgrind')
    ffp_args.add_argument('--windbg', action='store_true', help='Use WinDBG (Windows only)')
    ffp_args.add_argument('--xvfb', action='store_true', help='Use xvfb (Linux only)')

    js_args = subparsers.add_parser('js', parents=[global_args], help='Perform bisection for SpiderMonkey builds')
    js_args.add_argument('--foo', required=True, help='Foo')

    args = parser.parse_args()

    if not re.match(r'^[0-9[a-f]{12,40}$|^[0-9]{4}-[0-9]{2}-[0-9]{2}$', args.start):
        parser.error('Invalid start value supplied')
    if not re.match(r'^[0-9[a-f]{12,40}$|^[0-9]{4}-[0-9]{2}-[0-9]{2}$', args.end):
        parser.error('Invalid end value supplied')

    return args


def main(args):
    bisector = Bisector(args)
    if args.target == 'firefox':
        bisector.evaluator = BrowserBisector(args)

    start_time = time.time()
    bisector.bisect()
    end_time = time.time()
    elapsed = timedelta(seconds=(int(end_time - start_time)))
    log.info('Bisection completed in: %s' % elapsed)


if __name__ == '__main__':
    log_level = logging.INFO
    log_fmt = "[%(asctime)s] %(levelname).4s: %(message)s"
    if bool(os.getenv("DEBUG")):
        log_level = logging.DEBUG
        log_fmt = "%(levelname)s %(name)s [%(asctime)s] %(message)s"
    logging.basicConfig(format=log_fmt, datefmt="%Y-%m-%d %H:%M:%S", level=log_level)

    main(parse_arguments())
