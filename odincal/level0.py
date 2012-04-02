from oops.level0 import ACfile


import ctypes
import numpy
from pg import DB
from sys import argv
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
                f = ACfile(datafile,con)
                while 1:
                    try:
                        datadict = getAC(f)
                        con.insert('ac_level0',datadict)
                    except EOFError:
                        break

def getAC(ac,db):
    """AC factory.
    reads a fileobject and creates a dictionary for easy insertation
    into a postgresdatabase.
    """
    backend = {
        0x7380 : 'AC1',
        0x73b0 : 'AC2',
    }
    CLOCKFREQ= 224.0e6
    head = ac.getSpectrumHead()
    while head is not None:
        data = []
        stw = ac.stw
        back = backend[ac.user]
        for j in range(12):
            data.append(ac.getBlock())
            if data[j]==[]:
                raise(EOFError('File ended.'))
        cc=numpy.array(data)
        cc.shape = (8,96)
        lags = numpy.array(head[50:58],dtype='int32')
        zlags = (lags<<4) | cc[:,0]
        cc[:,0]=zlags
        cc = cc*2048.0*(1/ac.IntTime(head))/(CLOCKFREQ/2.0)
        mon = numpy.array(head[16:32],dtype='int32')
        mon.shape=(2,8)
        mon |= zlags & 0xf0000
        mon = mon * 1024.0*(1/ac.IntTime(head))/(CLOCKFREQ/2.0)
        prescaler = head[49]
        datadict = {
            'stw': stw,
            'backend': back,
            'frontend': ac.Frontend(head),
            'sig_type':ac.Type(head),
            'ssb_att': "{{{},{},{},{}}}".format(*ac.Attenuation(head)),
            'ssb_fq':"{{{},{},{},{}}}".format(*ac.SSBfrequency(head)),
            'prescaler': prescaler,
            'inttime': ac.IntTime(head),
            'mode':ac.Mode(head),
            'acd_mon': db.escape_bytea(mon.data),
            'cc': db.escape_bytea(cc.data),
        }
        return datadict
    raise(EOFError('File ended.'))

