#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import sqlalchemy
import subprocess
import pandas as pd
#



#

def is_dir(d):
    if os.path.isdir(d):
        return d
    raise argparse.ArgumentTypeError('%s is not a directory' %d)


def do_command(cmd, logger, stdout=subprocess.STDOUT, stderr=subprocess.PIPE, allow_fail=False):
    #env = update_env(logger)
    timecmd = cmd
    timecmd.insert(0, '/usr/bin/time')
    timecmd.insert(1, '-v')
    logger.info('running cmd: %s' % timecmd)
    try:
        output = subprocess.check_output(timecmd, stderr=subprocess.STDOUT)
        logger.info('contents of output(s)=%s' % output.decode().format())
    except Exception as e:
        logger.debug('failed cmd: %s' % str(timecmd))
        logger.debug('exception: %s' % e)
        if allow_fail:
            return e.output
        else:
            sys.exit('failed cmd: %s' % str(timecmd))
    logger.info('completed cmd: %s' % str(timecmd))
    return output


def do_shell_command(cmd, logger, stdout=subprocess.STDOUT, stderr=subprocess.PIPE):
    timecmd = '/usr/bin/time -v ' + cmd
    logger.info('running cmd: %s' % timecmd)
    try:
        output = subprocess.check_output(timecmd, stderr=subprocess.STDOUT, shell=True)
        logger.info('contents of output(s)=%s' % output.decode().format())
    except Exception as e:
        logger.debug('failed cmd: %s' % str(timecmd))
        logger.debug(e.output)
        logger.debug('exception: %s' % e)
        sys.exit('failed cmd: %s' % str(timecmd))
    logger.info('completed cmd: %s' % str(timecmd))
    return output

def store_time(uuid, cmd, output, logger):
    user_time = float()
    system_time = float()
    percent_of_cpu = int()
    wall_clock = float()
    maximum_resident_set_size = int()
    exit_status = int()
    for line in output.decode().format().split('\n'):
        line = line.strip()
        if line.startswith('User time (seconds):'):
            user_time = float(line.split(':')[1].strip())
        if line.startswith('System time (seconds):'):
            system_time = float(line.split(':')[1].strip())
        if line.startswith('Percent of CPU this job got:'):
            percent_of_cpu = int(line.split(':')[1].strip().rstrip('%'))
            assert (percent_of_cpu is not 0)
        if line.startswith('Elapsed (wall clock) time (h:mm:ss or m:ss):'):
            value = line.replace('Elapsed (wall clock) time (h:mm:ss) or m:ss:', '').strip()
            # hour case
            if value.count(':') == 2:
                hours = int(value.split(':')[0])
                minutes = int(value.split(':')[1])
                seconds = float(value.split(':')[2])
                total_seconds = (hours * 60 * 60) + (minutes * 60) + seconds
                wall_clock = total_seconds
            # under hour case
            if value.count(':') == 1:
                minutes = int(value.split(':')[0])
                seconds = float(value.split(':')[1])
                total_seconds = (minutes * 60) + seconds
                wall_clock = total_seconds
        if line.startswith('Maximum resident set size (kbytes):'):
            maximum_resident_set_size = int(line.split(':')[1].strip())
        if line.startswith('Exit status:'):
            exit_status = int(line.split(':')[1].strip())

    df = pd.DataFrame({'uuid': [uuid],
                       'user_time': user_time,
                       'system_time': system_time,
                       'percent_of_cpu': percent_of_cpu,
                       'wall_clock': wall_clock,
                       'maximum_resident_set_size': maximum_resident_set_size,
                       'exit_status': exit_status})
    return df

def main():
    parser = argparse.ArgumentParser('BAm to SAM conversion',
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
    do_shell_command(shell_BtS_CMD, logger)
    logger.info('Completed: BAM to SAM conversion')

if __name__ == '__main__':
    main()
    
