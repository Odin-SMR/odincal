from odincal.data_structures import  Data,Header
import pg
import matplotlib.pyplot as plt
import numpy

class AC:
    def __init__(self,header,data):
        self.header = header
        self.data = data


    def plot(self):
        fig, axarr = plt.subplots(4,2,sharex=True,sharey=True)
        for i in range(8):
            axarr[i%4,i/4].plot(range(96),self.data[i,:])
            axarr[i%4,i/4].set_title('CC_{}'.format(i))
            axarr[i%4,i/4].annotate(
                'ACD_mon_{0}_hi/lo={1}/{2}\nlag={3}'.format(
                    i,self.header.acd_mon[2*i+0],self.header.acd_mon[2*i+1],
                    self.header.lags[i]),
                xy=(.3,.7), xycoords='axes fraction')
        plt.show()

    def write_to_db(self,dbcon):
        query = """
            insert into ac ( stw, backend, counter, chopper_pos, int_time,
            acd_monitor, mask2, mask3, mask4, mask5, mask6, inttime,ccmxset,
            switch, sim, mxm, ssb1_att, ssb2_att, ssb3_att, ssb4_att, ssb1_fq,
            ssb2_fq, ssb3_fq, ssb4_fq, useraddress, r, s, prescaler, lags, tail,
            cc) values ({0.stw}, {0.backend}, {0.counter}, {0.chopper_pos},
            {0.int_time}, '{1}', {0.mask2}, {0.mask3}, {0.mask4},
            {0.mask5}, {0.mask6}, {0.inttime}, {0.ccmxset}, {0.switch}, {0.sim},
            {0.mxm}, {0.ssb1_att}, {0.ssb2_att}, {0.ssb3_att}, {0.ssb4_att},
            {0.ssb1_fq}, {0.ssb2_fq}, {0.ssb3_fq}, {0.ssb4_fq}, {0.useraddress},
            {0.r}, {0.s}, {0.prescaler}, '{2}', {0.tail}, '{3}')
            
            """.format(
                self.header,
                pg.escape_bytea(
                    numpy.ndarray((8,2), 'int16', self.header.acd_mon)),
                pg.escape_bytea(
                    numpy.ndarray((8,), 'int16', self.header.lags)),
                pg.escape_bytea(self.data)
            )
        dbcon.query(query)

    def __repr__(self):
        output =""
        for i in self.header._fields_:
            if i[0].startswith('no'):
                continue
            elif i[0]=='acd_mon':
                continue
            elif i[0]=='lags':
                continue
            else:
                output += '  {0:<12}:{1:x}\n'.format(i[0],getattr(self.header,i[0]))
        return output

def getAC(f):
    """AC factory.
    reads a file and creates an AC instance
    """
    h = Header()
    d = Data()
    while (f.readinto(h)!=0):
        if (h.backend&0xff0f)==0x7300:
            tmp = numpy.ndarray((12,64),'int16')
            for j in range(12):
                if f.readinto(d)==0:
                    raise(EOFError('File ended.'))
                tmp[j]=numpy.ndarray(64,'int16',d.userdata)
            return AC(h,tmp.reshape(8,96))
    raise(EOFError('File ended.'))

if __name__=="__main__":
    con = pg.connect('odin')
    f=open('/home/joakim/Downloads/149a04f1.ac1','rb')
    ac1 = getAC(f)
    print ac1
    ac2 = getAC(f)
    ac2.plot()
    ac3 = getAC(f)
    ac3.write_to_db(con)
    f.close()
