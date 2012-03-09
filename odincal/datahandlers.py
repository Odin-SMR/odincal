from odincal.data_structures import  ACData,AC,HK
from odincal.basehandler import BaseHandler
import pg
import ctypes
import matplotlib.pyplot as plt
import numpy


class ACHandler(BaseHandler):
    def __init__(self,ac,data):
        self.data_fields = ac
        self.cc = data
        self.extra_data_field='cc'
        super(ACHandler,self).__init__(['stw','backend'])

    def plot(self):
        fig, axarr = plt.subplots(4,2,sharex=True,sharey=True)
        for i in range(8):
            axarr[i%4,i/4].plot(range(96),self.cc[i,:])
            axarr[i%4,i/4].set_title('CC_{}'.format(i))
            axarr[i%4,i/4].annotate(
                'ACD_mon_{0}_hi/lo={1}/{2}\nlag={3}'.format(
                    i,self.data_fields.acd_mon[2*i+0],
                    self.data_fields.acd_mon[2*i+1],
                    self.data_fields.lags[i]),
                xy=(.3,.7), xycoords='axes fraction')
        plt.show()

class HKHandler(BaseHandler):
    def __init__(self,hk):
        self.data_fields = hk
        super(HKHandler,self).__init__(['stw','backend'])

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

