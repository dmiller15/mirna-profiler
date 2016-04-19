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
    parser = argparse.ArgumentParser('SAM Annotator', description = 'Annotates the SAM files with miRNA hits',)

    # Logging flag
    parser.add_argument('-d', '--debug',
                        action = 'store_const',
                        const = logging.DEBUG,
                        dest = 'level',
                        help = 'Enable debug logging.',
    )
    parser.set_defaults(level = logging.INFO)

    # Required flags
    parser.add_argument('-o', '--species_code',
                        required = True,
                        choices = ['hsa'],
                        help = 'Organism species code.',
    )
    parser.add_argument('-s', '--sam_path',
                        required = True,
                        help = 'Path to directory containing bams.',
    )
    parser.add_argument('-c', '--db_connect',                  
                        required = True,
                        help = 'Path to db_connection file',                  
    )
    args = parser.parse_args()

    species_code = args.species_code
    sam_path = args.sam_path
    connect_path = args.db_connect    

    # Logging Setup
    logging.basicConfig(
        filename = 'profiling_annotation.log',
        filemode = 'a',
        level = args.level,
        format = '%(asctime)s %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemp.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    hostname = os.uname()[1]
    logger.info('hostname=%s' % hostname)

    engine_path = 'sqlite:///' + 'profiling_annotation.db'
    engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Annotate the SAM files
    logger.info('Beginning: SAM file annotation')
    annotate_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/annotation/annotate.pl', '-d', connect_path, '-o', species_code, '-s', sam_path]
    pipe_util.do_command(annotate_CMD, logger)
    # Store time command will go here
    logger.info('Completed: SAM file annotation')

if __name__ == '__main__':
    main()
