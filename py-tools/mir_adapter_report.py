#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import sqlalchemy
import subprocess
import pandas as pd
#
import pipe_util


#

def main():
    parser = argparse.ArgumentParser('miRNA adapter report', description = 'Generate adapter report for alignments that did not have adapter trimming done',)

    # Logging flag
    parser.add_argument('-d', '--debug',
                        action = 'store_const',
                        const = logging.DEBUG,
                        dest = 'level',
                        help = 'Enable debug logging.',
    )
    parser.set_defaults(level = logging.INFO)

    parser.add_argument('-s', '--sam_path',
                        required = True,
                        help = 'Path to sam file.',
    )
    args = parser.parse_args()

    sam_path = args.sam_path

    # Logging Setup
    logging.basicConfig(
        filename = 'profiling_adapter.log',
        filemode = 'a',
        level = args.level,
        format = '%(asctime)s %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemp.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    hostname = os.uname()[1]
    logger.info('hostname=%s' % hostname)

    engine_path = 'sqlite:///' + 'profiling_adapter.db'
    engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    sam_name = os.path.basename(sam_path)
    sam_base, sam_ext = os.path.splitext(sam_name)
    adapter_name = sam_base + "_adapter.report"
    adapter_CMD = ["cat", sam_path, "|", "awk '{arr[length($10)]+=1} END {for (i in arr) {print i\" \"arr[i]}}'", "|", "sort -t \" \" -k1n >", adapter_name]
    shell_adapter_CMD = ' '.join(adapter_CMD)
    pipe_util.do_shell_command(shell_adapter_CMD, logger)
    logger.info('Adapter report: %s created for BAM file: %s' % (adapter_name, sam_path))

if __name__ == '__main__':
    main()

