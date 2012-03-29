from oops.level0 import ACfile


import pg
import ctypes
import numpy



def getAC(ac):
    """AC factory.
    reads a fileobject and creates an AC instance
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
            'acd_mon': pg.escape_bytea(mon.data),
            'cc': pg.escape_bytea(cc.data),
        }
        return datadict
    raise(EOFError('File ended.'))

