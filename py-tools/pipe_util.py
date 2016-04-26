import configparser
import logging
import os
import subprocess
import sys

import sqlalchemy

from sqlalchemy.ext.declarative import declarative_base


POSTGRES_CONN_FMT = 'postgresql+psycopg2://{username}:{password}@{host}:{port}/{db}'

Base = declarative_base()


def update_env(logger):
    env = dict()
    env.update(os.environ)
    path = env['PATH']
    logger.info('path=%s' % path)
    home_dir = os.path.expanduser('~')
    new_path = path
    new_path += ':' + os.path.join(home_dir, '.local', 'bin')
    pipe_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    new_path += ':' + pipe_dir
    logger.info('new_path=%s' % new_path)
    env['PATH'] = new_path
    return env


def do_command(cmd, logger, stdout=subprocess.STDOUT, stderr=subprocess.PIPE, allow_fail=False):
    env = update_env(logger)
    timecmd = cmd
    timecmd.insert(0, '/usr/bin/time')
    timecmd.insert(1, '-v')
    logger.info('running cmd: %s' % timecmd)

    output = b''
    try:
        output = subprocess.check_output(timecmd, env=env, stderr=subprocess.STDOUT)
    except Exception as e:
        output = e.output
        sys.stdout.buffer.write(output)
        logger.debug('failed cmd: %s' % str(timecmd))
        logger.debug('exception: %s' % e)
        if allow_fail:
            return e.output
        else:
            sys.exit('failed cmd: %s' % str(timecmd))
    finally:
        logger.info('contents of output(s)=%s' % output.decode().format())
    logger.info('completed cmd: %s' % str(timecmd))
    return output


def do_shell_command(cmd, logger, stdout=subprocess.STDOUT, stderr=subprocess.PIPE):
    env = update_env(logger)
    #timecmd=cmd
    #timecmd.insert(0,'/usr/bin/time')
    #timecmd.insert(1,'-v')
    timecmd = '/usr/bin/time -v ' + cmd
    logger.info('running cmd: %s' % timecmd)
    try:
        output = subprocess.check_output(timecmd, env=env, stderr=subprocess.STDOUT, shell=True)
        logger.info('contents of output(s)=%s' % output.decode().format())
        #p1=subprocess.Popen(timecmd,env=env,stdout=stdout,stderr=stderr)
        #output=p1.communicate()
        #logger.info('type(output)=%s' % type(output))
        #logger.info('contents of output(s)=%s' % str(output))
    except Exception as e:
        logger.debug('failed cmd: %s' % str(timecmd))
        logger.debug(e.output)
        logger.debug('exception: %s' % e)
        sys.exit('failed cmd: %s' % str(timecmd))
    logger.info('completed cmd: %s' % str(timecmd))
    return output


def touch(fname, logger, mode=0o666, dir_fd=None, **kwargs):
    logger.info('creating empty file: %s' % fname)
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd, **kwargs)
    return


def already_step(step_dir, step, logger):
    have_step_flag = os.path.join(step_dir, 'have_' + step)
    if os.path.exists(have_step_flag):
        logger.info('step flag exists: %s' % have_step_flag)
        return True
    else:
        logger.info('step flag does not exist: %s' % have_step_flag)
        return False


def create_already_step(step_dir, step, logger):
    have_step_flag = os.path.join(step_dir, 'have_' + step)
    touch(have_step_flag, logger)
    return
    

def setup_logging(tool_name, args, uuid):
    logging.basicConfig(
        filename=os.path.join(uuid + '_' + tool_name + '.log'),
        level=args.level,
        filemode='w',
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d_%H:%M:%S_%Z',
    )
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    return logger


def setup_db(uuid, conn_fmt=None, username='', password='', host=None, port=None, db=None, **kwargs):
    """Set up an SQLAlchemy database connection.
    """

    # NOTE these default values should be moved to an external configuration
    conn_fmt = conn_fmt if conn_fmt is not None else POSTGRES_CONN_FMT
    host = host if host is not None else 'pgreadwrite.osdc.io'
    port = port if port is not None else '5432'
    db = db if db is not None else 'prod_bioinfo'

    conn = conn_fmt.format(
        username=username,
        password=password,
        host=host,
        port=port,
        db=db,
    )

    engine = sqlalchemy.create_engine(conn, **kwargs)

    # TODO determine if there are any common table structures
    Base.metadata.bind = engine
    Base.metadata.create_all()

    return engine


def get_param(args, param_name):
    if vars(args)[param_name] == None:
        sys.exit('--'+ param_name + ' is required')
    else:
        return vars(args)[param_name]

    
def get_db_cred(db_cred_s3url, s3cfg_path, logger):
    cmd = ['s3cmd', '-c', s3cfg_path, 'get', '--force', db_cred_s3url]
    output = do_command(cmd, logger)
    db_cred_path = os.path.basename(db_cred_s3url)
    return db_cred_path

def get_connect_dict(db_cred_s3url, s3cfg_path, logger):
    db_cred_path = get_db_cred(db_cred_s3url, s3cfg_path, logger)
    config = configparser.ConfigParser()
    config.read(db_cred_path)
    connect_dict = dict(config['DEFAULT'])
    os.remove(db_cred_path)
    return connect_dict
