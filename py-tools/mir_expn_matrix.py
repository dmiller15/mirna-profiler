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
    parser.add_argument('-w', '--db_connect',
                        required = True,
                        help = 'Name of desired miRbase.',
    )
    parser.add_argument('-e', '--species_code',
                        required = True,
                        choices = ['hsa'],
                        help = 'Organism species code.',
    )
    parser.add_argument('-s', '--sam_path',
                        required = True,
                        help = 'Path to SAM file',
    )
    parser.add_argument('-p', '--mirna_species',
                        required = True,
                        help = 'Path to mirna_species file',
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

    connect_path = args.db_connect
    species_code = args.species_code
    sam_path = args.sam_path
    mirna_species = args.mirna_species
    uuid = args.uuid
    barcode = args.barcode

    if args.db_cred_s3url:
        db_cred_s3url = args.db_cred_s3url
        s3cfg_path = args.s3cfg_path
    else:
        db_cred_s3url = None

    logger = pipe_util.setup_logging('mir_profiler_matrix', args, uuid)
    
    if db_cred_s3url is not None:
        conn_dict = pipe_util.get_connect_dict(db_cred_s3url, s3cfg_path, logger)
        engine = sqlalchemy.create_engine(sqlalchemy.engine.url.URL(**conn_dict))
    else: #local sqllite case
        sqlite_name = 'mir_profiler_matrix' + uuid + '.db'
        engine_path = 'sqlite:///' + sqlite_name
        engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Generate the expression matrices for pre-miRNA
    logger.info('Beginning: Pre-miRNA gene expression matrix generation')
    matrix_CMD = ['perl', '/home/ubuntu/bin/mirna-profiler/v0.2.7/code/library_stats/expression_matrix.pl', '-d', connect_path, '-o', species_code, '-s', sam_path, '-r', mirna_species]
    output = pipe_util.do_command(matrix_CMD, logger)
    df = time_util.store_time(uuid, matrix_CMD, output, logger)
    df['bam_name'] = barcode
    unique_key_dict = {'uuid': uuid, 'bam_name': barcode}
    table_name = 'time_mem_mir_expn_matrix'
    df_util.save_df_to_sqlalchemy(df, unique_key_dict, table_name, engine, logger)
    logger.info('Completed: Pre-miRNA gene expression matrix generation')

if __name__ == '__main__':
    main()
