import numpy
import sys
from math import erfc, erf, pi, sqrt, exp,cos
from pg import DB
import ctypes 
from pkg_resources import resource_filename 
class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin')

class Level1a:
    """A class to process level 0 files into level 1a."""
    def __init__(self):  
        self.LAGSPERCHIP  =96
        self.MAXCHIPS     =8
        self.CLOCKFREQ    =224.0e6
        self.SAMPLEFREQ   =10.0e6
  
    def reduceAC(self,cc_data,acd_mon_pos,acd_mon_neg):
        self.nred=112
        datamod=numpy.zeros(shape=(self.MAXCHIPS,self.nred))
        datamod[:,0:self.LAGSPERCHIP]=cc_data
        self.got=[]
        for i in range(self.MAXCHIPS):
            goti=self.reduce1Band(datamod[i,:],acd_mon_pos[i],
                                             acd_mon_neg[i])
            if goti[0]==1:
                self.got.append(goti[1])
            else:
                self.got.append(numpy.zeros(shape=(self.nred,)))
      

    def reduce1Band(self,data,monitor_pos,monitor_neg):
        zlag = data[0];
        if zlag<=0:
            return 0,0
        if zlag>1:
            return 0,0
        power = zeroLag(zlag, 1.0)
        c_pos = threshold(monitor_pos)
        c_neg = threshold(monitor_neg)
        if (c_pos==0 or c_neg==0):
            return 0,0
        else:
            cmean = (c_pos+c_neg)/2.0
            dc = abs((c_pos-c_neg)/2.0/cmean)
            if dc>0.1:
                return 0,0
        data=qCorrect(cmean, data, self.nred)
        if data[0]==0:
            return 0,0
        #perform an fft of data
        librarypath=resource_filename('oops','libfft.so')
        libc=ctypes.CDLL(librarypath,mode=3)
        n0=ctypes.c_int(112)
        c_float_p = ctypes.POINTER(ctypes.c_double)
        data0 = numpy.array(data[1])
        data_p = data0.ctypes.data_as(c_float_p)
        libc.odinfft(data_p,n0)
        #Reintroduce power into filter shapes.
        data0=data0*power
        return 1,data0

     
def hanning(data,n):
    w = pi/n
    for i in range(1,n):
        data[i] = data[i]*(0.5+0.5*cos(w*i))
    return data
   
def inv_erfc(z):
    p =[1.591863138, -2.442326820, 0.37153461]
    q =[1.467751692, -3.013136362, 1.00000000]
    x = 1.0-z
    y = (x*x-0.5625)
    y = x*(p[0]+(p[1]+p[2]*y)*y)/(q[0]+(q[1]+q[2]*y)*y)
    return y

def threshold(monitor):
    if (monitor < 0.0 or monitor > 1.0): 
        return 0.0
    thr = sqrt(2.0)*inv_erfc(2.0*monitor)
    return thr

def qCorrect(c,f,n):
    #Perform quantisation correction using Kulkarni & Heiles approximation.
    #(taken from Kulkarni, S.R., Heiles, C., 1980, AJ, 85, 1413.
    A = (pi/2.0)*exp(c*c)
    B = -A*A*A*(pow((c*c-1), 2.0)/6.0)
    f[0] = 1.0;
    for i in range(1,n):
        fa = f[i]
        if (abs(fa) > 0.86):
            #level too high in QCorrect
            return 0,0;
        f[i] = (A + B*fa*fa)*fa
    return 1,f

def zeroLag(zlag,v):
    if (zlag >= 1.0 or zlag <= 0.0): 
        return 0.0
    x = v/inv_erfc(zlag)
    return  x*x/2.0

def ac_level1a_importer():
    con=db()
    #query=con.query('''select stw,backend,acd_mon,cc from
    #             ac_level0 
    #             natural left join ac_level1a
    #             where spectra is Null order by stw''')
    query=con.query('''select stw,backend from
                 ac_level0 
                 natural left join ac_level1a
                 where spectra is Null order by stw''')
    
    result=query.dictresult()
    ac=Level1a()
    for ind,row in enumerate(result):
        tempb=[row['stw'],row['backend']]
        queryb=con.query('''select acd_mon,cc from
                           ac_level0 where 
                           stw={0} and backend='{1}' '''.format(*tempb))
        resultb=queryb.dictresult() 
        rowb={'stw'      :row['stw'],
              'backend'  :row['backend'],
              'acd_mon'  :resultb[0]['acd_mon'],
              'cc'       :resultb[0]['cc'],}
        acd_mon=numpy.ndarray(shape=(8,2),dtype='float64',
                              buffer=con.unescape_bytea(rowb['acd_mon']))
        cc=numpy.ndarray(shape=(8,96),dtype='float64',
                         buffer=con.unescape_bytea(rowb['cc']))
        ac.reduceAC(cc,acd_mon[:,0],acd_mon[:,1])
        a=numpy.array(ac.got)
        a.shape=(8*112,)
        data=con.escape_bytea(abs(a).tostring())
        temp={
            'stw'         : row['stw'],
            'backend'     : row['backend'],
            'spectra'     : data,
            }
        con.insert('ac_level1a',temp)
    con.close()


