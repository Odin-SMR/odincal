from odincal.data_structures import  ACData,AC,HK
from odincal.database import ACHandler
import pg
import ctypes
import numpy



def getHK(f):
    """AC factory.
    reads a fileobject and creates an AC instance
    """
    h = HK()
    while (f.readinto(h)!=0):
        if h.backend==0x732c:
            return HKHandler(h)
    raise(EOFError('File ended.'))



def getAC(f):
    """AC factory.
    reads a fileobject and creates an AC instance
    """
    h = AC()
    d = ACData()
    while (f.readinto(h)!=0):
        if (h.backend&0xff0f)==0x7300:
            tmp = numpy.ndarray((12,64),'int16')
            for j in range(12):
                if f.readinto(d)==0:
                    raise(EOFError('File ended.'))
                tmp[j]=numpy.ndarray(64,'int16',d.userdata)
            tmp.shape = (8,96)
            #correction first value in cc due to overflow
            tmp = tmp.astype('int32')
            for i in range(8):
                tmp[i,0] = numpy.uint16(tmp[i,0])
            return ACHandler(h,tmp)
    raise(EOFError('File ended.'))

