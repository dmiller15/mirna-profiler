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
    parser = argparse.ArgumentParser('miRNA matrix mimat development', description = 'Mature miRNA gene expression matrix genreation',)

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
    parser.add_argument('-r', '--mirna_path',
                        required = True,
                        help = 'Path to miRNA.txt file',
    )
    parser.add_argument('-x', '--crossmapped_path',
                        required = True,
                        help = 'Path to crossmapped.txt file',
    )

    args = parser.parse_args()

    db_connect = args.db_connect
    species_code = args.species_code
    sam_path = args.sam_path
    mirna_path = args.mirna_path
    crossmapped_path = args.crossmapped_path
    
    # Logging Setup
    logging.basicConfig(
        filename = 'profiling_mimat.log',
        filemode = 'a',
        level = args.level,
        format = '%(asctime)s %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemp.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    hostname = os.uname()[1]
    logger.info('hostname=%s' % hostname)

    engine_path = 'sqlite:///' + 'profiling_mimat.db'
    engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Get stats from the alignment annotations
    logger.info('Beginning: Mature miRNA gene expression matrix genreation')
    mimat_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/library_stats/expression_matrix_mimat.pl', '-d', db_connect, '-o', species_code, '-s', sam_path, '-r', mirna_path, '-c', crossmapped_path]
    pipe_util.do_command(mimat_CMD, logger)
    # Store time command will go here
    logger.info('Completed: Mature miRNA gene expression matrix genreation')

if __name__ == '__main__':
    main()
