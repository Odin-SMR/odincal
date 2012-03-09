from pg import connect
from sys import argv
from odincal import getAC,getHK
from os.path import splitext

def files2db():
    if len(argv)>1:
        con = connect('odin')
        for datafile in argv[1:]:
            extension = splitext(datafile)[1]
            if extension == '.ac1' or extension == '.ac2':
                f = open(datafile,'rb')
                while 1:
                    try:
                        ac = getAC(f)
                    except EOFError:
                        break
                    q = ac.insert_statement()
                    con.query(q)
                f.close()
            elif extension == '.shk':
                f = open(datafile,'rb')
                while 1:
                    try:
                        hk = getHK(f)
                    except EOFError:
                        break
                    q = hk.insert_statement()
                    con.query(q)
                f.close()

