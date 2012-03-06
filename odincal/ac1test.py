from ctypes import Structure,c_ushort,c_float,c_uint,sizeof
import matplotlib.pyplot as plt
import numpy
class hblock(Structure):
    _fields_=[
        ('sync',c_ushort),
        ('stw_lsb',c_ushort),
        ('stw_msb',c_ushort),
        ('user',c_ushort),
        #data starts
        ('nodata1',(c_ushort*8)),
        ('chopper_pos',c_ushort),
        ('nodata2',(c_ushort*3)),
        ('int_time',c_ushort),
        ('nodata3',(c_ushort*3)),
        ('acd',(c_ushort*16)),
        #config copy starts
        #08
        ('mask3',c_ushort,8),
        ('mask2',c_ushort,8),
        #09
        ('mask5',c_ushort,8),
        ('mask4',c_ushort,8),
        #0A
        ('mask6',c_ushort),
        #0B
        ('inttime',c_ushort,8),
        ('ccmxset',c_ushort,8),
        #0C
        ('simswitch',c_ushort,4),
        ('nop',c_ushort,4),
        ('mxm',c_ushort,8),
        #0D
        ('ssb1_att',c_ushort),
        #0E
        ('ssb2_att',c_ushort),
        #0F
        ('ssb3_att',c_ushort),
        #10
        ('ssb4_att',c_ushort),
        #11
        ('ssb4_fq',c_ushort),
        #12
        ('ssb3_fq',c_ushort),
        #13
        ('ssb2_fq',c_ushort),
        #14
        ('ssb1_fq',c_ushort),
        #15
        ('useraddress',c_ushort),
        #16
        ('r',c_ushort,8),
        ('s',c_ushort,8),
        #('noconfig',(c_ushort*17)),
        ('noconfig',(c_ushort*2)),
        ('prescaler',c_ushort),
        ('lags',(c_ushort*8)),
        ('noconfig2',(c_ushort*6)),
        ('index',c_ushort),
        ('nodummy',(c_ushort*6)),
        ]

class dblock(Structure):
    _fields_=[
        ('sync',c_ushort),
        ('stw_lsb',c_ushort),
        ('stw_msb',c_ushort),
        ('user',c_ushort),
        ('userdata',(c_ushort*64)),
        ('index',c_ushort),
        ('dummy',(c_ushort*6)),
        ]

class ac:

    def __init__(self):
        self.datatype = '>i2'
        self.inputshape = (12,64)
        self.outputshape = (8,96)
        self.header = hblock()
        self.data = numpy.ndarray(self.inputshape,self.datatype)

    def readblocks(self,f):
        a = hblock()
        b = dblock()
        while (f.readinto(a)!=0):
            if a.user==0x7380:
                for j in range(12):
                    f.readinto(b)
                    self.data[j]=numpy.ndarray(64,self.datatype,b)
                self.data.shape = self.outputshape
                return

    def plot(self):
        fig, axarr = plt.subplots(4,2,sharex=True,sharey=True)
        for i in range(8):
            axarr[i%4,i/4].plot(range(96),self.data[i,:])
            axarr[i%4,i/4].set_title('CC_{}'.format(i))
            axarr[i%4,i/4].annotate(
                'ACD_mon_{0}_hi/lo={1}/{2}\nlag={3}'.format(
                    i,self.header.acd[2*i+0],self.header.acd[2*i+1],
                    self.header.lags[i]),
                xy=(.7,.7), xycoords='axes fraction')
        plt.show()

f=open('/home/joakim/Downloads/149a04f1.ac1','rb')
ac1 = ac()
ac1.readblocks(f)
ac1.plot()
f.close()
