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
    parser = argparse.ArgumentParser('miRNA matrix', description = 'Pre-miRNA gene expression matrix generation',)

    # Logging flag
    parser.add_argument('-d', '--debug',
                        action = 'store_const',
                        const = logging.DEBUG,
                        dest = 'level',
                        help = 'Enable debug logging.',
    )
    parser.set_defaults(level = logging.INFO)

    # Required flags
    parser.add_argument('-c', '--db_connect',
                        required = True,
                        help = 'Name of desired miRbase.',
    )
    parser.add_argument('-o', '--species_code',
                        required = True,
                        choices = ['hsa'],
                        help = 'Organism species code.',
    )
    parser.add_argument('-s', '--sam_path',
                        required = True,
                        help = 'Path to SAM file',
    )
    parser.add_argument('-r', '--mirna_species',
                        required = True,
                        help = 'Path to mirna_species file',
    )                  
    args = parser.parse_args()                   

    connect_path = args.db_connect
    species_code = args.species_code
    sam_path = args.sam_path
    mirna_species = args.mirna_species

    # Logging Setup
    logging.basicConfig(
        filename = 'profiling_matrix.log',
        filemode = 'a',
        level = args.level,
        format = '%(asctime)s %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemp.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    hostname = os.uname()[1]
    logger.info('hostname=%s' % hostname)

    engine_path = 'sqlite:///' + 'profiling_matrix.db'
    engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Generate the expression matrices for pre-miRNA
    logger.info('Beginning: Pre-miRNA gene expression matrix generation')
    matrix_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/library_stats/expression_matrix.pl', '-d', connect_path, '-o', species_code, '-s', sam_path, '-r', mirna_species]
    pipe_util.do_command(matrix_CMD, logger)
    # Store time commmand will go here
    logger.info('Completed: Pre-miRNA gene expression matrix generation')

if __name__ == '__main__':
    main()
