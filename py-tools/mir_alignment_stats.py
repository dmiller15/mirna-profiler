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
    parser = argparse.ArgumentParser('SAM alignment stats', description = 'Generate alignment stats for the miRNA in the annotated SAM file',)

    # Logging flag
    parser.add_argument('-d', '--debug',
                        action = 'store_const',
                        const = logging.DEBUG,
                        dest = 'level',
                        help = 'Enable debug logging.',
    )
    parser.set_defaults(level = logging.INFO)

    # Required flags
    parser.add_argument('-s', '--sam_path',
                        required = True,
                        help = 'Path to SAM file',
    )
    parser.add_argument('-a', '--adapter_path',
                        required = True,
                        help = 'Path to adapter report',
    )
    args = parser.parse_args()

    sam_path = args.sam_path
    adapter_path = args.adapter_path

    # Logging Setup
    logging.basicConfig(
        filename = 'profiling_stats.log',
        filemode = 'a',
        level = args.level,
        format = '%(asctime)s %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemp.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    hostname = os.uname()[1]
    logger.info('hostname=%s' % hostname)

    engine_path = 'sqlite:///' + 'profiling_stats.db'
    engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Get stats from the alignment annotations
    logger.info('Beginning: Alignment stats generation')
    stats_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/library_stats/alignment_stats.pl', '-s', sam_path, '-a', adapter_path]
    do_command(stats_CMD, logger)
    # Store time command will go here
    logger.info('Completed: Alignment stats generation')

if __name__ == '__main__':
    main()
