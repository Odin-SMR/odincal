from ctypes import LittleEndianStructure, c_ushort, c_uint, c_short
class Header(LittleEndianStructure):
    _pack_=2
    _fields_=[
        ('sync',c_ushort),
        ('stw',c_uint),
        ('user',c_ushort),
        #data starts
        ('nodata0',(c_ushort*2)),
        ('counter',c_ushort),
        ('nodata0',(c_ushort*5)),
        ('chopper_pos',c_ushort),
        ('nodata2',(c_ushort*3)),
        ('int_time',c_ushort),
        ('nodata3',(c_ushort*3)),
        ('acd_mon',(c_short*16)),
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
        ('switch',c_ushort,1),
        ('sim',   c_ushort,1),
        ('nop',c_ushort,6),
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
        ('lags',(c_short*8)),
        ('noconfig2',(c_ushort*6)),
        ('index',c_ushort),
        ('nodummy',(c_ushort*6)),
        ]

class Data(LittleEndianStructure):
    _pack_=2
    _fields_=[
        ('sync',c_ushort),
        ('stw',c_uint),
        ('user',c_ushort),
        ('userdata',(c_short*64)),
        ('index',c_ushort),
        ('dummy',(c_ushort*6)),
        ]
