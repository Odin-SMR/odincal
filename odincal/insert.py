from pg import DB
from sys import argv
from odincal.level0 import getAC
from oops.level0 import ACfile
from os.path import splitext

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin')


def files2db():
    if len(argv)>1:
        con = db()
        for datafile in argv[1:]:
            extension = splitext(datafile)[1]
            if extension == '.ac1' or extension == '.ac2':
                f = ACfile(datafile)
                while 1:
                    try:
                        datadict = getAC(f)
                        con.insert('ac_level0',datadict)
                    except EOFError:
                        break
