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
        ('noconfig',(c_ushort*17)),
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

def getcc(f):
    a=hblock()
    b=dblock()
    cc_block = numpy.ndarray((12,64),'>f2')
    while (f.readinto(a)!=0):
        print '{:X}'.format(a.user)
        if a.user==0x7380:
            stw = (a.stw_msb<<16)+a.stw_lsb
            adc = numpy.ndarray((16,),'>i2',a.acd)
            print 'Data block at time {0:X}'.format(stw)
            for i in a._fields_:
                if i[0]=='acd':
                    print 'acd'
                elif not i[0].startswith('no'):
                    print '{0:>15} {1:4X} {1:8d}'.format(i[0],getattr(a,i[0]))
            for j in range(12):
                f.readinto(b)
                cc_block[j]=numpy.ndarray((1,64),'>f2',b)
            return cc_block.reshape(8,96)
        pass
    pass


f=open('/home/joakim/Downloads/149a04f1.ac1','rb')
print sizeof(hblock),sizeof(dblock)

cc = getcc(f)
plt.plot(cc.transpose())
plt.show()
f.close()
