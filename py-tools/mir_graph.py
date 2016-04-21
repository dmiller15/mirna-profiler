#!/usr/bin/env python

import argparse
import logging
import os
import sys
import sqlalchemy
import subprocess
import pandas as pd
#
import pipe_util
import df_util
import time_util
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
    parser.add_argument('-v', '--softclip_taglen',
                        required = True,
                        help = 'Path to softclip_taglength.csv',
    )
    parser.add_argument('-a', '--adapter_report',
                        required = True,
                        help = 'Path to adapter report',
    )
    parser.add_argument('-c', '--chastity_taglen',
                        required = True,
                        help = 'Path to chastity_taglength.csv',
    )
    parser.add_argument('-l', '--alignment_stats',
                        required = True,
                        help = 'Path to alignment_stats.csv',
    )
    parser.add_argument('-u', '--uuid',
                        required = True,
                        help = 'UUID/GDC_ID for the harmonized BAM.',
    )
    parser.add_argument('-r', '--barcode',
                        required = True,
                        help = 'BAM barcode',
    )
    

    # Optional DB Flags
    parser.add_argument('-y', '--db_cred_s3url',
                        required = False,
                        help = 'String s3url of the postgres db_cred file',
    )
    parser.add_argument('-z', '--s3cfg_path',
                        required = False,
                        help = 'Path to the s3cfg file.',
    )
    
    args = parser.parse_args()                   

    sam_path = args.sam_path
    filtered_taglen = args.filtered_taglen
    softclip_taglen = args.softclip_taglen
    adapter_report = args.adapter_report
    chastity_taglen = args.chastity_taglen
    alignment_stats = args.alignment_stats
    uuid = args.uuid
    barcode = args.barcode

    if args.db_cred_s3url:
        db_cred_s3url = args.db_cred_s3url
        s3cfg_path = args.s3cfg_path
    else:
        db_cred_s3url = None

    logger = pipe_util.setup_logging('mir_profiler_graph', args, uuid)
    
    if db_cred_s3url is not None:
        conn_dict = pipe_util.get_connect_dict(db_cred_s3url, s3cfg_path, logger)
        engine = sqlalchemy.create_engine(sqlalchemy.engine.url.URL(**conn_dict))
    else: #local sqllite case
        sqlite_name = 'mir_profiler_graph' + uuid + '.db'
        engine_path = 'sqlite:///' + sqlite_name
        engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Generate the graphs for the annotation data
    logger.info('Beginning: Annotation graph generation')
    graph_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/library_stats/graph_libs.pl', '-s', sam_path, '-f', filtered_taglen, '-o', softclip_taglen, '-a', adapter_report, '-c', chastity_taglen, '-t', alignment_stats]
    output = pipe_util.do_command(graph_CMD, logger)
    df = time_util.store_time(uuid, graph_CMD, output, logger)
    df['bam_name'] = barcode
    unique_key_dict = {'uuid': uuid, 'bam_name': barcode}
    table_name = 'time_mem_mir_graph'
    df_util.save_df_to_sqlalchemy(df, unique_key_dict, table_name, engine, logger)
    # Store time command will go here
    logger.info('Completed: Annotation graph generation')

if __name__ == '__main__':
    main()
