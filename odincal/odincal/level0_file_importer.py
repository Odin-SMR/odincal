from datetime import datetime, timedelta
from os.path import basename,splitext
from sys import argv
from odincal.config import config
import psycopg2
from StringIO import StringIO


def timestamp_from_filename(datafile):
    filename=splitext(datafile)[0]
    stw=eval('0x'+filename+'0')
    #reference stw and mjd
    stw0=6161431982
    MJD0=56416.7782534
    rate=1/16.0016444
    #calculate mjd for the filename stw
    MJD=MJD0+(stw-stw0)*rate/86400.0
    #get a time stamp
    d=datetime.date(datetime(1858,11,17)+timedelta(days=MJD))
    return d

def import_file(file):
    filename=basename(file)
    if (filename.endswith('.ac1') or filename.endswith('.ac2') or
            filename.endswith('.shk') or filename.endswith('.att') or
            filename.endswith('.fba')):
        pass
    else:
        return 0
    timestamp=timestamp_from_filename(filename) 
    fgr= StringIO()
    fgr.write( filename             +'\t'+
               str(timestamp)       +'\t'+
               str(datetime.now())  +'\n')

    conn = psycopg2.connect(config.get('database','pgstring'))    
    cur = conn.cursor()
    fgr.seek(0)
    cur.execute("create temporary table foo ( like level0_files );")
    cur.copy_from(file=fgr,table='foo')
    cur.execute("delete from level0_files ac using foo f where f.file=ac.file ")
    cur.execute("insert into level0_files (select * from foo)")
    conn.commit()
    conn.close()
    fgr.close()

if __name__=='__main__':
    files=argv[1::]
    fgr= StringIO()
    for file in files:
        filename=basename(file)
        if (filename.endswith('.ac1') or filename.endswith('.ac2') or
            filename.endswith('.shk') or filename.endswith('.att') or
            filename.endswith('.fba')):
            pass
        else:
            continue
        timestamp=timestamp_from_filename(filename)
        fgr.write( filename             +'\t'+
                   str(timestamp)       +'\t'+
                   str(datetime.now())  +'\n')

    conn = psycopg2.connect(config.get('database','pgstring'))
    cur = conn.cursor()
    fgr.seek(0)
    cur.execute("create temporary table foo ( like level0_files );")
    cur.copy_from(file=fgr,table='foo')
    fgr.close()
    cur.execute("delete from level0_files ac using foo f where f.file=ac.file ")
    cur.execute("insert into level0_files (select * from foo)")
    conn.commit()
    conn.close()


