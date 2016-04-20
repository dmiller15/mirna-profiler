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
import df_util
import time_util
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
    parser.add_argument('-e', '--species_code',
                        required = True,
                        choices = ['hsa'],
                        help = 'Organism species code.',
    )
    parser.add_argument('-s', '--sam_path',
                        required = True,
                        help = 'Path to directory containing bams.',
    )
    parser.add_argument('-w', '--db_connect',                  
                        required = True,
                        help = 'Path to db_connection file',                  
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

    species_code = args.species_code
    sam_path = args.sam_path
    connect_path = args.db_connect
    uuid = args.uuid
    barcode = args.barcode

    if args.db_cred_s3url:
        db_cred_s3url = args.db_cred_s3url
        s3cfg_path = args.s3cfg_path
    else:
        db_cred_s3url = None

    logger = pipe_util.setup_logging('mir_profiler_annotator', args, uuid)

    if db_cred_s3url is not None:
        conn_dict = pipe_util.get_connect_dict(db_cred_s3url, s3cfg_path, logger)
        engine = sqlalchemy.create_engine(sqlalchemy.engine.url.URL(**conn_dict))
    else: #local sqllite case
        sqlite_name = 'mir_profiler_annotator' + uuid + '.db'
        engine_path = 'sqlite:///' + sqlite_name
        engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Annotate the SAM files
    logger.info('Beginning: SAM file annotation')
    annotate_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/annotation/annotate.pl', '-d', connect_path, '-o', species_code, '-s', sam_path]
    output = pipe_util.do_command(annotate_CMD, logger)
    df = time_util.store_time(uuid, annotate_CMD, output, logger)
    df['bam_name'] = barcode
    unique_key_dict = {'uuid': uuid, 'bam_name': barcode}
    table_name = 'time_mem_mir_test'
    df_util.save_df_to_sqlalchemy(df, unique_key_dict, table_name, engine, logger)
    logger.info('Completed: SAM file annotation')

if __name__ == '__main__':
    main()
