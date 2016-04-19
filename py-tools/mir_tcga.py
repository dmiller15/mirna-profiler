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
    parser = argparse.ArgumentParser('TCGA', description = 'TCGA formatted results generation',)

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
    parser.add_argument('-g', '--genome_version',
                        required = True,
                        choices = ['hg38'],
                        help = 'Genome Version of Annotation.',
    )
    parser.add_argument('-o', '--species_code',
                        required = True,
                        choices = ['hsa'],
                        help = 'Organism species code.',
    )
    parser.add_argument('-s', '--sam_path',
                        required = True,
                        help = 'Path to directory containing bams.',
    )
    parser.add_argument('-r', '--mirna_species',
                        required = True,
                        help = 'Path to mirna_species.txt',
    )
    parser.add_argument('-x', '--crossmapped',
                        required = True,
                        help = 'Path to crossmapped.txt',
    )
    parser.add_argument('-i', '--isoforms',
                        required = True,
                        help = 'Path to isoforms.txt',
    )
    args = parser.parse_args()

    connect_path = args.db_connect
    genome_version = args.genome_version
    species_code = args.species_code
    sam_path = args.sam_path
    mirna_species = args.mirna_species
    crossmapped = args.crossmapped
    isoforms = args.isoforms

    # Logging Setup
    logging.basicConfig(
        filename = 'profiling_tcga.log',
        filemode = 'a',
        level = args.level,
        format = '%(asctime)s %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemp.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    hostname = os.uname()[1]
    logger.info('hostname=%s' % hostname)

    engine_path = 'sqlite:///' + 'profiling_tcga.db'
    engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Generate TCGA formatted results
    logger.info('Beginning: TCGA formatted results generation')
    tcga_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/custom_output/tcga/tcga.pl', '-d', connect_path, '-o', species_code, '-g', genome_version, '-s', sam_path, '-r', mirna_species, '-c', crossmapped, '-i', isoforms]
    pipe_util.do_command(tcga_CMD, logger)
    # Store time command will go here
    logger.info('Completed: TCGA formatted results generation')

if __name__ == '__main__':
    main()
