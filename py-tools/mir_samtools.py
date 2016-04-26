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
    parser = argparse.ArgumentParser('BAM to SAM conversion',
                                     description = 'Use samtools to convert a SAM to BAM.',
    )

    # Logging flag
    parser.add_argument('-d', '--debug',
                        action = 'store_const',
                        const = logging.DEBUG,
                        dest = 'level',
                        help = 'Enable debug logging.',
    )
    parser.set_defaults(level = logging.INFO)

    # Required flags
    parser.add_argument('-b', '--bam_path',
                        required = True,
                        help = 'Path to BAM file.',
    )
    parser.add_argument('-o', '--output_name',
                        required = True,
                        help = 'Desired name for output SAM.',
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

    bam_path = args.bam_path
    output_name = args.output_name
    uuid = args.uuid
    barcode = args.barcode

    if args.db_cred_s3url:
        db_cred_s3url = args.db_cred_s3url
        s3cfg_path = args.s3cfg_path
    else:
        db_cred_s3url = None

    logger = pipe_util.setup_logging('mir_profiler_samtools', args, uuid)
    
    if db_cred_s3url is not None:
        conn_dict = pipe_util.get_connect_dict(db_cred_s3url, s3cfg_path, logger)
        engine = sqlalchemy.create_engine(sqlalchemy.engine.url.URL(**conn_dict))
    else: #local sqllite case
        sqlite_name = 'mir_profiler_samtools' + uuid + '.db'
        engine_path = 'sqlite:///' + sqlite_name
        engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Convert the BAMs to SAMs if they do not already exist
    logger.info('Beginning: BAM to SAM conversion')
    BAMtoSAM_CMD = ['samtools', 'view', '-h', bam_path, '-o', output_name]
    shell_BtS_CMD = ' '.join(BAMtoSAM_CMD)
    output = pipe_util.do_shell_command(shell_BtS_CMD, logger)
    df = time_util.store_time(uuid, shell_BtS_CMD, output, logger)
    df['bam_name'] = barcode
    unique_key_dict = {'uuid': uuid, 'bam_name': barcode}
    table_name = 'time_mem_mir_samtools_view'
    df_util.save_df_to_sqlalchemy(df, unique_key_dict, table_name, engine, logger)
    logger.info('Completed: BAM to SAM conversion')

if __name__ == '__main__':
    main()
    
