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

    args = parser.parse_args()

    bam_path = args.bam_path
    output_name = args.output_name

    # Logging Setup
    logging.basicConfig(
        filename = 'profiling_samtools.log',
        filemode = 'a',
        level = args.level,
        format = '%(asctime)s %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemp.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    hostname = os.uname()[1]
    logger.info('hostname=%s' % hostname)

    engine_path = 'sqlite:///' + 'profiling_samtools.db'
    engine = sqlalchemy.create_engine(engine_path, isolation_level='SERIALIZABLE')

    # Convert the BAMs to SAMs if they do not already exist
    logger.info('Beginning: BAM to SAM conversion')
    BAMtoSAM_CMD = ['samtools', 'view', '-h', bam_path, '-o', output_name]
    shell_BtS_CMD = ' '.join(BAMtoSAM_CMD)
    pipe_util.do_shell_command(shell_BtS_CMD, logger)
    logger.info('Completed: BAM to SAM conversion')

if __name__ == '__main__':
    main()
    
