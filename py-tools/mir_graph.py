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
    parser = argparse.ArgumentParser('Graph generation', description = 'Generate graphs for different miRNA stats',)

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
    parser.add_argument('-f', '--filtered_taglen',
                        required = True,
                        help = 'Path to filtered_taglength.csv',
    )
    parser.add_argument('-o', '--softclip_taglen',
                        required = True,
                        help = 'Path to softclip_taglength.csv',
    )
    parser.add_argument('-a', '--adapter_taglen',
                        required = True,
                        help = 'Path to adapter report',
    )
    parser.add_argument('-c', '--chastity_taglen',
                        required = True,
                        help = 'Path to chastity_taglength.csv',
    )
    parser.add_argument('-t', '--alignment_stats',
                        required = True,
                        help = 'Path to alignment_stats.csv',
    )
    args = parser.parse_args()                   

    sam_path = args.sam_path
    filtered_taglen = args.filtered_taglen
    softclip_taglen = args.softclip_taglen
    adapter_taglen = args.adapter_taglen
    chastity_taglen = args.chastity_taglen
    alignment_stats = args.alignment_stats
    
    # Logging Setup
    logging.basicConfig(
        filename = 'profiling_graph.log',
        filemode = 'a',
        level = args.level,
        format = '%(asctime)s %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemp.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    hostname = os.uname()[1]
    logger.info('hostname=%s' % hostname)

    engine_path = 'sqlite:///' + 'profiling_graph.db'
    engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Generate the graphs for the annotation data
    logger.info('Beginning: Annotation graph generation')
    graph_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/library_stats/graph_libs.pl', '-s', sam_path, '-f', filtered_taglen, '-o', softclip_taglen, '-a', adapter_taglen, '-c', chastity_taglen, '-t', alignment_stats]
    pipe_util.do_command(graph_CMD, logger)
    # Store time command will go here
    logger.info('Completed: Annotation graph generation')

if __name__ == '__main__':
    main()
