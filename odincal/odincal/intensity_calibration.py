import numpy
import copy

class Level1b_cal():
    """A class that can perform intensity calibration of odin ac-data"""
    def __init__(self,spectra,calstw,con):
        self.spectra=spectra
        self.calstw=calstw
        self.con=con
    def calibrate(self,version):
        """Do intensity calibration for all receivers."""
        VERSION = version
        (sig,ref,cal) = self.sortspec(self.spectra)
        
        if len(sig) == 0:
            return None,VERSION,None
        if len(ref) == 0:
            #odin.Warn("no reference spectra found") 
            return None,VERSION,None
 
        if len(cal) > 0:
            cal = self.cleancal(cal, ref)
        else:
            #odin.Warn("no calibration spectra found")
            return None,VERSION,None
        print 'skyfreq',ref[0].skyfreq/1e9
        
        C = self.medTsys(cal)
        nref = len(ref)
        (rstw,rmat,inttime,start) = self.matrix(ref)
        calibrated = []
        maxalt = 0.0
        iscan = 0
        nspec = 0
        Tsys = copy.copy(sig[0])
        Tsys.type = 'CAL'
        Tsys.data = C.data
        if self.calstw!=0:
            Tsys.stw=self.calstw
        calibrated.append(Tsys)
        ssb = copy.copy(Tsys)
        ssb.type = 'SSB'
        ssb.data = self.ssbCurve(ssb)
        calibrated.append(ssb)
        for t in sig:
            s = copy.copy(t)
            stw = float(s.stw)
            R = ref[0]
	    R.data = self.interpolate(rstw, rmat, stw,0,0)
            self.calibrate1(s,R.data,Tsys.data, 1.0)
                
            T = numpy.take(Tsys.data,numpy.nonzero(Tsys.data)[0])
            if T.shape[0] == 0:
                return None,VERSION,None
            s.tsys = numpy.add.reduce(T)/T.shape[0]
            d = numpy.take(s.data, numpy.nonzero(s.data))
            mean = numpy.add.reduce(d[0])/d[0].shape[0]
            msq = numpy.sqrt(numpy.add.reduce((d[0]-mean)**2)/(d[0].shape[0]-1))
            if version==9 and (mean < -1.0 or mean > 300.0):
                #odin.Warn("spectrum mean out of range: %10.1f" % (mean))
                continue
            if s.altitude > maxalt:
                maxalt = s.altitude
            calibrated.append(s)
        ########## determination of baffle contribution ##########
        ### Tspill = zeros(8, Float)
        Tspill = []
        Tspillnew=[]
        eff = []
        baf=[]
        bafstw=[]
        bafaltitude=[]
        for s in calibrated:
            if s.type == 'SPE' and s.altitude > maxalt-10.0e3 and s.ref!=1:
                baf.append(s.data)
                bafstw.append(s.stw)
                bafaltitude.append(s.altitude)
                n = len(s.data)
                med = numpy.sort(s.data[s.data.nonzero()])
                Tspill.append(med[len(med)/2])
                if s.backend == "AOS":
                    d = s.data
                    mean = numpy.add.reduce(d)/d.shape[0]
                    msq = numpy.add.reduce((d-mean)**2)/(d.shape[0]-1)
                    teff = (s.tsys*s.tsys/msq)/s.freqres
                    eff.append(teff/s.inttime)
                else:
                    n = 112
                    bands = 8
                    sigma = numpy.zeros(shape=(bands,)) 
                    for band in range(bands):
                        i0 = band*n
                        i1 = i0+n
                        d = s.data[i0:i1]
                        mean = numpy.add.reduce(d)/float(n)
                        msq = numpy.add.reduce((d-mean)**2)/float(n-1)
                        sigma[band] = msq
                    msq = min(numpy.take(sigma,numpy.nonzero(sigma))[0])
                    teff = (s.tsys*s.tsys/msq)/s.freqres
                    eff.append(teff/s.inttime)
        # Tspill is the median contribution from the baffle
        n = len(Tspill)
        if n:
            Tspill = numpy.sort(Tspill)[n/2]
        else:
            #odin.Warn("no spectra at high altitude")
            Tspill = 9.0
        # eff is the mean integration efficiency, in the sense that
        # s.inttime*eff is an effective integration time related to
        # the noise level of a spectrum via the radiometer formula
        eff = numpy.array(eff)
        n = len(eff)
        if n:
            eff = numpy.add.reduce(eff)/n
        else:
            eff = 1.0

        eta = 1.0-Tspill/300.0
        for s in calibrated:
            # set version number of calibration routine
            #s.level = s.level | VERSION
            if s.type == 'SPE' and s.ref!=1:
                s.data = numpy.choose(numpy.equal(s.data,0.0), 
                                      ((s.data-Tspill)/eta, 0.0))
                s.efftime = s.inttime*eff
        print 'Tspill '+str(Tspill) 
       
        return calibrated,VERSION,Tspill
   
    
   
    def cleancal(self, cal, ref):
        if len(ref) == 0 or len(cal) == 0:
            return
        (rstw,rmat,inttime,start) = self.matrix(ref)
        ns = rmat.shape[0]
        R = copy.copy(cal[0])
        (Tmin,Tmax) = self.acceptableTsys(R.frontend)
        for k in range(len(cal)):
            stw = float(cal[k].stw)
            # find reference data by table lookup
            R.data=self.interpolate(rstw, rmat, stw, inttime,start)
            # calculate a Tsys spectrum from given C and R
            cal[k].data=self.Tsys(cal[k],R)
        # combine CAL spectra into matrix
        (cstw,cmat,dummy,dummy) = self.matrix(cal)
        nc = cmat.shape[0]
        if cal[0].backend == 'AOS':
            mc = numpy.add.reduce(cmat,1)/cmat.shape[1]
        else:
            n = 112
            bands = len(cal[0].data)/n
            rms = numpy.zeros(shape=(bands,))
            for band in range(bands):
                i0 = band*n
                i1 = i0+n
                mc = numpy.add.reduce(cmat[:,i0:i1],1)/float(n)
                # print "mc =", mc, nc, len(nonzero(mc))
                if len(numpy.nonzero(mc)[0]) < nc or nc < 2:
                    rms[band] = 1.0e10
                else:
                    mc = mc - numpy.add.reduce(mc)/float(nc)
                    rms[band] = numpy.sqrt(
                        numpy.add.reduce(mc*mc)/(float(nc-1)))
                print "rms of band",band," =",rms[band]
            i = numpy.argsort(numpy.where(rms == 0.0, max(rms), rms))
            i0 = i[0]*n
            i1 = i0+n
            mc =numpy.add.reduce(cmat,1)/cmat.shape[1]
        # to start with, disgard any Tsys spectra which are clearly
        # too high
        mc0 = numpy.take(mc,numpy.nonzero(numpy.less(mc,Tmax)))[0]
        mc0 = numpy.take(mc0,numpy.nonzero(numpy.greater(mc0,Tmin)))[0]
        n1 = len(mc0)
        if n1 == 0:
            tsys = 0.0
            cal = []
        else:
            tsys = numpy.sort(mc0)[n1/2]
            print "mean Tsys", tsys
            for i in range(nc-1,-1,-1):
                if (mc[i] < Tmin or mc[i] > Tmax or 
                    abs((mc[i]-tsys)/tsys) > 0.02):
                    pass
                    #del cal[i]
                if (mc[i] < Tmin or mc[i] > Tmax):
                    del cal[i]

        del mc
        n2 = len(cal)
        return cal

    def matrix(self, spectra):
        if len(spectra) == 0:
            return None

        rows = len(spectra)
        cols = len(spectra[0].data)

        stw = numpy.zeros(shape=(rows,))
        start = numpy.zeros(shape=(rows,))
        inttime=numpy.zeros(shape=(rows,))
        mat = numpy.zeros(shape=(rows,cols))
        

        for i in range(rows):
            s = spectra[i]
            if s.data.shape[0] == cols:
                mat[i,:] = s.data
            else:
                pass
            stw[i] = s.stw
            inttime[i] = s.inttime
            start[i]=s.start

        return (stw,mat,inttime,start)


    def ssbCurve(self, s):
        dB = {'495': -26.7, '549': -27.7, '555': -32.3, '572': -28.7 }
        if s.frontend in ['495', '549', '555', '572']:
            maxdB = dB[s.frontend]
        else:
            return numpy.ones(shape=len(s.data,))
        
        fIF = 3900e6
        if s.skyfreq > s.lofreq:
            fim = s.lofreq - fIF
        else:
            fim = s.lofreq + fIF
        c = 2.9979e8
        d0 = c/fIF/4.0
        l = c/fim
        n = numpy.floor(d0/l)
        dx = (n+0.5)*l-d0
  
        x0 = d0+dx
        if s.skyfreq > s.lofreq:
            f = self.frequency(s)-2.0*fIF/1.0e9
        else:
            f = self.frequency(s)+2.0*fIF/1.0e9
            fim = s.lofreq + fIF
        l = c/f/1.0e9
        p = 2.0*numpy.pi*x0/l
        Y = 0.5*(1.0+numpy.cos(p))
        S = 10.0**(maxdB/10.0)
        Z = S + (1.0-S)*Y
        Z = 1.0-Z
        # for i in range(10):
        #     print "%15.6e %15.6e %10.5f" % (f[i], l[i], Z[i])
        return Z

    def frequency(self,s):
       df = 1.0e6
       n=896
       f=numpy.zeros(shape=(n,))
       split=0
       upper=0
       if split:
           if upper:
               for j in range(0,n/4):
                   f[j+0*n/4] = s.LO[2]*1e6 - (n/4-1-j)*df;
                   f[j+1*n/4] = s.LO[2]*1e6 + j*df;                      
                   f[j+2*n/4] = s.LO[3]*1e6 - (n/4-1-j)*df
                   f[j+3*n/4] = s.LO[3]*1e6 + j*df;
           else:
               for j in range(0,n/4):
                   f[j+0*n/4] = s.LO[0]*1e6 - (n/4-1-j)*df
                   f[j+1*n/4] = s.LO[0]*1e6 + j*df
                   f[j+2*n/4] = s.LO[1]*1e6 - (n/4-1-j)*df
                   f[j+3*n/4] = s.LO[1]*1e6 + j*df 
       else:
           for j in range(n/8):
               f[j+0*n/8] = s.LO[0]*1e6 - (n/8-1-j)*df
               f[j+1*n/8] = s.LO[0]*1e6 + j*df


               f[j+2*n/8] = s.LO[1]*1e6 - (n/8-1-j)*df
               f[j+3*n/8] = s.LO[1]*1e6 + j*df
  
               f[j+4*n/8] = s.LO[2]*1e6 - (n/8-1-j)*df
               f[j+5*n/8] = s.LO[2]*1e6 + j*df
               
               f[j+4*n/8] = s.LO[2]*1e6 + j*df
               f[j+5*n/8] = s.LO[2]*1e6 - (n/8-1-j)*df

               f[j+6*n/8] = s.LO[3]*1e6 - (n/8-1-j)*df
               f[j+7*n/8] = s.LO[3]*1e6 + j*df
                
       seq=[1,1,1,-1,1,1,1,-1,1,-1,1,1,1,-1,1,1] 
       m=0
       for adc in range(8):
           if seq[2*adc]:
               k = seq[2*adc]*112
               df = 1.0e6/seq[2*adc]
               if seq[2*adc+1] < 0:
                   df=-df
               for j in range(k): 
                   f[m+j] = s.LO[adc/2]*1e6 +j*df;
               m += k;
       fdata=numpy.zeros(shape=(n,))
       if s.skyfreq >= s.lofreq:            
            for i in range(n):               
                v = f[i]
                v = s.lofreq + v
                v /= 1.0e9
                fdata[i] = v
       else: 
           for i in range(n):
               v = f[i]
               v = s.lofreq - v
               v /= 1.0e9
               fdata[i]=v
       return fdata
        
    def interpolate(self, mstw, m, stw, dummy1,dummy2):
        rows = m.shape[0]
        if rows != len(mstw):
            raise IndexError
        i = numpy.searchsorted(mstw, stw)
        if i == 0:
            return m[0]
        elif i == rows:
            return m[rows-1]
        else:
            dt0 = float(mstw[i]-stw)
            dt1 = float(stw-mstw[i-1])
            dt =  float(mstw[i]-mstw[i-1])
            return (dt0*m[i-1] + dt1*m[i])/dt


    def medTsys(self, cal):
        C = cal[0]
        (Tmin,Tmax) = self.acceptableTsys(C.frontend)

        (cstw,cmat,dummy,dummy) = self.matrix(cal)
        if C.backend == 'AOS':
            C.data = numpy.add.reduce(cmat)/float(cmat.shape[0])
        else:
            n = 112
            bands = len(C.data)/n
            C.data=numpy.zeros(shape=(len(C.data,)))
            for band in range(bands):
                c = numpy.zeros(shape=(n,))
                i0 = band*n
                i1 = i0+n
                k = 0
                for i in range(cmat.shape[0]):
                    d = cmat[i,i0:i1]
                    if len(numpy.nonzero(d)[0]) == 112:
                        tsys = numpy.add.reduce(d)/112.0
                        if tsys > Tmin and tsys < Tmax:
                            c = c+d
                            k = k+1
                if k > 0:
                    c = c/float(k)
                C.data[i0:i1] = c
        return C

    def acceptableTsys(self, rx):
        if rx == '119':
            Tmin =  400.0
            Tmax =  1500.0
        else:
            Tmin = 2000.0
            Tmax = 7000.0
        return (Tmin, Tmax)

    def Tsys(self,cal,ref):
        data=numpy.zeros(shape=(len(cal.data),))
        epsr=1.0
        etaMT=1.0
        etaMS=1.0
        Tspill=290.0
        f = cal.skyfreq
        Tbg = planck(2.7, f)
        Thot = planck(cal.tcal, f)
        if Thot == 0.0:
            Thot = 275.0
        dT = epsr*etaMT*Thot - etaMS*Tbg + (etaMS-etaMT)*Tspill;
        for i in range(0,len(cal.data)):
            if ref.data[i] > 0.0:
                if cal.data[i] > ref.data[i]:
                    data[i] = (ref.data[i]/
                                      (cal.data[i]-ref.data[i]))
                    data[i] *= dT
                else: 
                    data[i] = 0.0;
            else: 
                data[i] = 0.0;
       

        return data

    def calibrate1(self,sig,ref,cal,eta):
        etaML = [0.976, 0.968, 0.978, 0.975, 0.954 ]
        etaMS  = 1.0
        Tspill = 290.0
        if eta == 0.0:
            #rx = sig.frontend - 1;
            rx=0
            if (rx < 0 or rx > 4):
                #ODINwarning("invalid receiver");
                return;
            eta = etaML[rx];
        f = sig.skyfreq
        Tbg = planck(2.7, f);
        spill = etaMS*Tbg - (etaMS-eta)*Tspill;
       	ok_ind=numpy.nonzero(ref>0.0)[0]
        data=numpy.zeros(shape=len(sig.data),)
	data[ok_ind]=((sig.data[ok_ind]-ref[ok_ind])/ref[ok_ind]*cal[ok_ind]+spill)/eta
	sig.data=data
        sig.type = 'SPE'

    def sortspec(self, spectra):
        sig = []
        ref = []
        cal = []
        for s in spectra:
            if s.type == 'SIG':
                sig.append(s)
            elif s.type == 'SK1' or s.type == 'SK2' or s.type == 'REF':
                ref.append(s)
            elif s.type == 'CAL':
                cal.append(s)

        return (sig, ref, cal)

     

   
def planck(T,f):
    h = 6.626176e-34;     # Planck constant (Js)
    k = 1.380662e-23;     # Boltzmann constant (J/K)
    T0 = h*f/k
    if (T > 0.0): 
        Tb = T0/(numpy.exp(T0/T)-1.0);
    else:         
        Tb = 0.0;
    return Tb


if __name__ == "__main__":
    pass

