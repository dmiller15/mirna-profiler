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
    parser = argparse.ArgumentParser('miRNA adapter report', description = 'Generate adapter report for alignments that did not have adapter trimming done',)

    # Logging flag
    parser.add_argument('-d', '--debug',
                        action = 'store_const',
                        const = logging.DEBUG,
                        dest = 'level',
                        help = 'Enable debug logging.',
    )
    parser.set_defaults(level = logging.INFO)

    parser.add_argument('-s', '--sam_path',
                        required = True,
                        help = 'Path to sam file.',
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
    uuid = args.uuid
    barcode = args.barcode

    if args.db_cred_s3url:
        db_cred_s3url = args.db_cred_s3url
        s3cfg_path = args.s3cfg_path
    else:
        db_cred_s3url = None

    logger = pipe_util.setup_logging('mir_profiler_adapter_report', args, uuid)

    if db_cred_s3url is not None:
        conn_dict = pipe_util.get_connect_dict(db_cred_s3url, s3cfg_path, logger)
        engine = sqlalchemy.create_engine(sqlalchemy.engine.url.URL(**conn_dict))
    else: #local sqllite case
        sqlite_name = 'mir_profiler_adapter_report' + uuid + '.db'
        engine_path = 'sqlite:///' + sqlite_name
        engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    logger.info('Beginning: Adapter report generation')
    sam_name = os.path.basename(sam_path)
    sam_base, sam_ext = os.path.splitext(sam_name)
    adapter_name = sam_base + "_adapter.report"
    adapter_CMD = ["cat", sam_path, "|", "awk '{arr[length($10)]+=1} END {for (i in arr) {print i\" \"arr[i]}}'", "|", "sort -t \" \" -k1n >", adapter_name]
    shell_adapter_CMD = ' '.join(adapter_CMD)
    output = pipe_util.do_shell_command(shell_adapter_CMD, logger)
    df = time_util.store_time(uuid, shell_adapter_CMD, output, logger)
    df['bam_name'] = barcode
    unique_key_dict = {'uuid': uuid, 'bam_name': barcode}
    table_name = 'time_mem_mir_test'
    df_util.save_df_to_sqlalchemy(df, unique_key_dict, table_name, engine, logger)
    logger.info('Completed: Adapter report generation')

if __name__ == '__main__':
    main()

