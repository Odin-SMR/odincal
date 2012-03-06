from odincal.data_structures import  Data,Header
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
        if (h.user&0xff0f)==0x7300:
            tmp = numpy.ndarray((12,64),'int16')
            for j in range(12):
                f.readinto(d)
                tmp[j]=numpy.ndarray(64,'int16',d.userdata)
            return AC(h,tmp.reshape(8,96))

if __name__=="__main__":
    f=open('/home/joakim/Downloads/149a04f1.ac1','rb')
    ac1 = getAC(f)
    print ac1
    ac2 = getAC(f)
    ac2.plot()
    f.close()
