""" Register a file in the database """
from datetime import datetime, timedelta
from os.path import basename, splitext
from sys import argv
from StringIO import StringIO
import logging
import psycopg2
from odincal.config import config


def timestamp_from_filename(datafile):
    """ return datetime from filename """
    filename = splitext(datafile)[0]
    stw = int('0x' + filename + '0', base=16)
    # reference stw and mjd
    stw0 = 6161431982
    mjd0 = 56416.7782534
    rate = 1 / 16.0016444
    # calculate mjd for the filename stw
    mjd = mjd0 + (stw - stw0) * rate / 86400.0
    # get a time stamp
    timestamp = datetime.date(datetime(1858, 11, 17) + timedelta(days=mjd))
    return timestamp


def import_file(file_name):
    """ import one file """
    logger = logging.getLogger(__name__)
    filename = basename(file_name)
    logger.info("importing filename %s", filename)
    suffix = filename[-3:]
    if suffix in ['ac1', 'ac2', 'shk', 'att', 'fba']:
        timestamp = timestamp_from_filename(filename)
        conn = psycopg2.connect(config.get('database', 'pgstring'))
        cur = conn.cursor()
        cur.execute("delete from level0_files where file=%s", (filename,))
        logger.debug('executed %s', cur.query)
        cur.execute(
            "insert into level0_files values (%s, %s, %s)",
            (filename, str(timestamp), str(datetime.now()))
        )
        logger.debug('executed %s', cur.query)
        conn.commit()
        conn.close()


def main():
    """ import many files """
    files = argv[1::]
    fgr = StringIO()
    for file_name in files:
        filename = basename(file_name)
        if (filename.endswith('.ac1') or filename.endswith('.ac2') or
                filename.endswith('.shk') or filename.endswith('.att') or
                filename.endswith('.fba')):
            pass
        else:
            continue
        timestamp = timestamp_from_filename(filename)
        fgr.write(
            filename + '\t' + str(timestamp) + '\t' + str(datetime.now()) +
            '\n'
        )

    conn = psycopg2.connect(config.get('database', 'pgstring'))
    cur = conn.cursor()
    fgr.seek(0)
    cur.execute("create temporary table foo ( like level0_files );")
    cur.copy_from(file=fgr, table='foo')
    fgr.close()
    cur.execute(
        "delete from level0_files ac using foo f where f.file=ac.file "
    )
    cur.execute("insert into level0_files (select * from foo)")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
