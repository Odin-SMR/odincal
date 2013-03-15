import numpy
import copy
from oops import odin
import pg
from pg import DB
from sys import stderr,stdout,stdin,argv,exit
import matplotlib.pyplot as pyplt
from odincal.reference_fit import Ref_fit

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin',user='odinop',host='malachite',passwd='***REMOVED***')


class Level1b_cal():
    """A class that can perform intensity calibration of level 1a spectra"""
    def __init__(self,spectra,calstw,con):
        self.spectra=spectra
        self.calstw=calstw
        self.con=con
    def calibrate(self):
        """Do intensity calibration for all receivers."""
        VERSION = 0x0009
        (sig,ref,cal) = self.sortspec(self.spectra)
        self.checkaltitude(sig)
        if len(sig) == 0:
            return None,VERSION,None
        #ns = len(sig)/len(scans)
        #if ns < 5:
        #    return None
        if len(ref) > 0:
            ref = self.cleanref(ref)
        if len(ref) == 0:
            odin.Warn("no reference spectra found") 
            return None,VERSION,None
        if len(cal) > 0:
            cal = self.cleancal(cal, ref)
        if len(cal) == 0:
            odin.Warn("no calibration spectra found")
            return None,VERSION,None
        print 'skyfreq',ref[0].skyfreq/1e9

        #some tests
        #now we are calibrating reference spectra as well
        #so now we remove these reference spectra that
        #where filtered out
        sig=self.cleansigref(sig,ref)
        C = self.medTsys(cal)
        nref = len(ref)
        (rstw,rmat,inttime,start) = self.matrix(ref)
        calibrated = []
        maxalt = 0.0
        iscan = 0
        nspec = 0
        gain = copy.copy(sig[0])
        gain.type = 'CAL'
        gain.data = C.data
        if self.calstw!=0:
            gain.stw=self.calstw
        calibrated.append(gain)
        ssb = copy.copy(gain)
        ssb.type = 'SSB'
        ssb.data = self.ssbCurve(ssb)
        calibrated.append(ssb)
        for t in sig:
            s = copy.copy(t)
            stw = float(s.stw)
            R = ref[0]
            if t.ref==1:
                for indrstw in enumerate(rstw):
                    if indrstw==t.stw:
                        rstwnew=numpy.array(rstw[rstw!=indrstw])
                        rmatnew=numpy.array(rmat[rstw!=indrstw,:])
                        inttimenew=numpy.array(inttime[rstw!=indrstw,:])
                        startnew=numpy.array(start[rstw!=indrstw,:])
                        R.data = self.interpolate(rstwnew, rmatnew, 
                                                  stw,inttimenew,
                                                  startnew)
            else:
                R.data = self.interpolate(rstw, rmat, stw,inttime,start)
            self.calibrate1(s,R.data,gain.data, 1.0)
                
            T = numpy.take(gain.data,numpy.nonzero(gain.data)[0])
            if T.shape[0] == 0:
                return None,VERSION,None
            s.tsys = numpy.add.reduce(T)/T.shape[0]
            d = numpy.take(s.data, numpy.nonzero(s.data))
            mean = numpy.add.reduce(d[0])/d[0].shape[0]
            msq = numpy.sqrt(numpy.add.reduce((d[0]-mean)**2)/(d[0].shape[0]-1))
            if mean < -1.0 or mean > 300.0:
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
        #odin.Info("maximum altitude in orbit %6.2f km" % (maxalt/1000.0))
        baf=[]
        bafstw=[]
        bafaltitude=[]
        for s in calibrated:
            if s.type == 'SPE' and s.altitude > maxalt-10.0e3 and s.ref!=1:
                baf.append(s.data)
                bafstw.append(s.stw)
                bafaltitude.append(s.altitude)
                n = len(s.data)
                #med = numpy.sort(s.data)[n/2]
                #Tspill.append(med)
                med = numpy.sort(s.data[s.data.nonzero()])
                Tspill.append(med[len(med)/2])
                med = numpy.sort(s.data[s.data.nonzero()])
                Tspillnew.append(med[len(med)/2])
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
        #baf=numpy.array(baf)
        #bafstw=numpy.array(bafstw)
        #bafaltitude=numpy.array(bafaltitude)
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
        #pyplt.figure()
        #for ind,s in enumerate(calibrated):
        #    pyplt.plot(s.data)
        #    if ind==100:
        #        break
        #pyplt.show()
                

        return calibrated,VERSION,Tspill
   
    def cleanref(self, ref):
        if len(ref) == 0:
            return
        (rstw,rmat,inttime,start) = self.matrix(ref)
        ns = rmat.shape[0]
        if ref[0].backend == 'AOS':
            mr = numpy.add.reduce(rmat,1)/rmat.shape[1]
        else:
            n = 112
            bands = len(ref[0].data)/n
            rms = numpy.zeros(shape=(bands,))
            for band in range(bands):
                i0 = band*n
                i1 = i0+n
                mr = numpy.add.reduce(rmat[:,i0:i1],1)/float(n)
                mr = mr - numpy.add.reduce(mr)/float(ns)
                rms[band] = numpy.sqrt(numpy.add.reduce(mr*mr)/float(ns-1))
            i = numpy.argsort(numpy.where(rms == 0.0, max(rms), rms))
            i0 = i[0]*n
            i1 = i0+n
            mr = numpy.add.reduce(rmat[:,i0:i1],1)/float(n)
            
        n = len(mr)
        med = self.medfilter(mr,2)

        for i in range(n-1,-1,-1):
            if med[i] == 0.0 or abs((mr[i]-med[i])/med[i]) > 0.001:
                del ref[i]
        del med
        del mr
         
        return ref
    
    def cleansigref(self,sig,ref):
        #now we are calibrating reference spectra as well
        #so now we remove these reference spectra that
        #where filtered out by cleanref
        for ind,refsig in enumerate(sig):
            if refsig.ref==1:
                filtered_ref=1
                #assume refsig is filtered
                for refleft in ref:
                    if refsig.stw==refleft.stw:
                        #do not remove refsig
                        filtered_ref=0
                if filtered_ref:
                    del sig[ind]
        return sig

    def cleancal(self, cal, ref):
        if len(ref) == 0 or len(cal) == 0:
            return
        (rstw,rmat,inttime,start) = self.matrix(ref)
        ns = rmat.shape[0]
        R = cal[0]
        (Tmin,Tmax) = self.acceptableTsys(R.frontend)
        for k in range(len(cal)):
            stw = float(cal[k].stw)
            # find reference data by table lookup
            R.data=self.interpolate(rstw, rmat, stw, inttime,start)
            #i = numpy.searchsorted(rstw, stw)
            #if i == 0:
            #    R.data = ref[0].data
            #elif i == ns:
            #    R.data = ref[ns-1].data
            #else:
            #    dt0 = rstw[i]-stw
            #    dt1 = stw-rstw[i-1]
            #    dt =  rstw[i]-rstw[i-1]
            #    R.data = (dt0*ref[i-1].data + dt1*ref[i].data)/dt
            #    print R.data
            #    print error
            # calculate a Tsys spectrum from given C and R
            cal[k].data=self.gain(cal[k],R)
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
            # mc = add.reduce(cmat[:,i0:i1],1)/float(n)
            mc =numpy.add.reduce(cmat,1)/cmat.shape[1]
        # to start with, disgard any Tsys spectra which are clearly
        # too high
        # print mc
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

    def medfilter(self, a, m):
        width = 2*m+1
        n = len(a)
        if n <= width:
            odin.Warn("not enough values for median filter")
            return a
        med = numpy.zeros(shape=(n, width))
        for i in range(n):
            i1 = i-m
            if   i1 < 0:
                i1 = 0
            elif i1 > n-width:
                i1 = n-width
            i2 = i1+width
            if i2 > n:
                i2 = n
            
            # one row of med are 'width' adjacent values
            med[i] = numpy.array(a[i1:i2])

        # sort and pick the middle column (median values)
        med = numpy.sort(med)
        med = med[:,m]
        return med
        
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

    def gain(self,cal,ref):
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
        #for i in range(0,len(cal.data)):
        #    data[i]

        return data

    def calibrate1(self,sig,ref,cal,eta):
        #void Calibrate(Scan *sig, Scan *ref, Scan *cal, double eta)
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
        data=numpy.zeros(shape=len(sig.data),)
        #for i in range(0,len(sig.data)):
        #    data[i]=sig.data[i]-ref[i]
        #    if (ref[i] > 0.0):
        #        data[i]=data[i]/ref[i]
        #        data[i]=data[i]*cal[i]
        #        data[i] += spill
        #        data[i] /= eta
        #        
        #    else: 
        #        data[i] = 0.0
        sig.data=((sig.data-ref)/ref*cal+spill)/eta
	sig.data[ref<=0.0]=0
	#sig.data=data
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

    def checkaltitude(self, spectra):
        n = len(spectra)
        for i in range(n-1,-1,-1):
            s = spectra[i]
            alt = s.altitude
            x = s.qerror[0]
            y = s.qerror[1]
            z = s.qerror[2]
            err = numpy.sqrt(x*x+y*y+z*z)
            if err > 20.0:
                del spectra[i]
            elif numpy.add.reduce(s.qachieved) == 0.0:
                del spectra[i]
            elif alt < 0.0 or alt > 120000.0:
                odin.Warn("deleting altitude: %10.3f" % (alt/1000.0))
                del spectra[i]
        n2 = len(spectra)
     

    def freqMode(self, s):
        df = 30.0e6
        self.freqmode = 0
        self.split = 0
        LO = s.lofreq*(1.0 + s.vgeo/2.99792456e8)
        modes = {
            'STRAT':  "Stratospheric",
            'ODD_H':  "Odd hydrogen",
            'ODD_N':  "Odd nitrogen",
            'WATER':  "Water isotope",
            'SUMMER': "Summer mesosphere",
            'DYNAM':  "Transport"
            }

        config = None
        if s.backend == 'AC1':
            if s.frontend == '495':
                config = [[492.750e9,23, "DYNAM", 0],
                          [495.402e9,29, "DYNAM", 0],
                          [499.698e9,25, "DYNAM", 0]]
            elif s.frontend == '549':
                config = [[548.502e9, 2, "STRAT", 0],
                          [553.050e9,19, "WATER", 0],
                          [547.752e9,21, "WATER", 1],
                          [553.302e9,23, "DYNAM", 0],
                          [553.302e9,29, "DYNAM", 0]]
            elif s.frontend == '555':
                config = [[553.298e9,13, "SUMMER", 0]]
            elif s.frontend == '572':
                config = [[572.762e9,24, "DYNAM", 0]]
        elif s.backend == 'AC2':
            if s.frontend == '495':
                config = [[497.880e9, 1, "STRAT", 1],
                          [492.750e9, 8, "WATER", 1],
                          [494.250e9,17, "WATER", 0],
                          [499.698e9,25, "DYNAM", 0]]
            elif s.frontend == '572':
                config = [[572.964e9,22, "DYNAM", 1],
                          [572.762e9,14,"SUMMER", 0]]
        if config:
            df = [0.0]*len(config)
            for i in range(len(df)):
                df[i] = abs(LO-config[i][0])
            i = df.index(min(df))
            # print "configuration", i, config[i]
            self.freqmode = config[i][1]
            self.topic    = config[i][2]
            self.split    = config[i][3]
            # print "configuration %s:%s:%10.1f" % \
            #       (s.backend, s.frontend, LO/1.0e6),
            # print " %d, %s" % (self.freqmode, self.topic)
        else:
            odin.Warn("unknown configuration %s:%s:%10.1f" % \
                      (s.backend, s.frontend, LO/1.0e6))

        if self.freqmode:
            self.source = "%s FM=%d" % (modes[self.topic], self.freqmode)
        else:
            self.source ="unknown"
            self.topic = "N/A"
        
        return self.freqmode

def planck(T,f):
    h = 6.626176e-34;     # Planck constant (Js)
    k = 1.380662e-23;     # Boltzmann constant (J/K)
    T0 = h*f/k
    if (T > 0.0): 
        Tb = T0/(numpy.exp(T0/T)-1.0);
    else:         
        Tb = 0.0;
    return Tb



class Spectra: 
    """A class that perform frequency calibration of ac level 1a spectra"""
    def __init__(self,con,data,ref):
        self.ref=ref
        self.start=data['start']
        self.data=numpy.ndarray(shape=(112*8,),
                     dtype='float64',buffer=con.unescape_bytea(
                     data['spectra']))
        self.stw=data['stw']
        self.LO=eval(data['ssb_fq'].replace('{','(').replace('}',')'))
        self.backend=data['backend']
        self.frontend=data['frontend']
        self.vgeo=data['vgeo']
        self.mode=data['mode']
        self.tcal=data['hotloada']
        if self.tcal==0:
            self.tcal=data['hotloadb']
        self.freqres=1e6
        if data['sig_type']=='SIG':
            self.qerror=eval(data['qerror'].replace('{','(').replace('}',')'))
            self.qachieved=eval(data['qachieved'].replace('{','(').replace('}',')'))
        self.inttime=data['inttime']
        self.intmode=511
        self.skyfreq=0
        self.lofreq=data['lo']
        self.ssb=data['ssb']
        self.Tpll=data['imageloadb']
        if self.Tpll==0:
            self.Tpll=data['imageloada'] 
        self.current=data['mixc']
        self.type=data['sig_type']
        self.source=[]
        self.topic=[]
        self.restfreq=[]
        self.latitude=data['latitude']
        self.longitude=data['longitude']
        self.altitude=data['altitude']
        self.tsys=0
        self.efftime=0
        self.sbpath=0
        self.cc=numpy.ndarray(shape=(8,96),dtype='float64',
                              buffer=con.unescape_bytea(data['cc']))
        self.zerolag=numpy.array(self.cc[0:8,0])
        self.skybeamhit=data['skybeamhit']
        self.ssb_att=eval(data['ssb_att'].replace('{','(').replace('}',')'))
    def tuning(self):

        if self.frontend == '119':
            IFfreq = 3900.0e6
            self.lofreq = 114.8498600000000e+9
            self.fcalibrate(self.lofreq,IFfreq)
            return
        
        rxs = { '495': 1, '549': 2, '555': 3, '572': 4 }
        if not self.frontend in rxs.keys():
            return 
        (IFfreq,sbpath) = getSideBand(self.frontend, self.lofreq, self.ssb)
        self.sbpath = sbpath/1.0e6
        (ADC_SPLIT, ADC_UPPER) = (0x0200, 0x0400)
        if self.intmode & ADC_SPLIT:
            if self.backend == 'AC1':
                if self.intmode & ADC_UPPER: 
                    IFfreq = IFfreq*3.6/3.9
                else:                     
                    IFfreq = IFfreq*4.2/3.9
            elif self.backend == 'AC2':
                if self.intmode & ADC_UPPER: 
                    IFfreq = IFfreq*4.2/3.9
                else:                     
                    IFfreq = IFfreq*3.6/3.9
                
        if self.current < 0.25:
            #odin.Warn("low mixer current %5.2f" % (current))
            if self.frontend <> '572':
                self.lofreq = 0.0
        #else:
        #    IFfreq = 0.0
           #odin.Warn("LO frequency lookup failed")
        self.fcalibrate(self.lofreq, IFfreq)

         
    def fcalibrate(self,LOfreq, IFfreq):
        """Perform frequency calibration."""
        if LOfreq == 0.0: 
            return
        if self.frontend == '495' or self.frontend == '549':
            drift = 1.0+(29.23-0.138*self.Tpll)*1.0e-6
        else:
            drift = 1.0+(24.69-0.109*self.Tpll)*1.0e-6
        LOfreq = LOfreq*drift
        self.lofreq  = LOfreq
        self.skyfreq = LOfreq+IFfreq
        self.maxsup  = LOfreq-IFfreq
        #self.restfreq = self.skyfreq
        # apply Doppler correction
        self.restfreq = self.skyfreq/(1.0 - self.vgeo/2.99792456e8);
        #self.quality = quality
 
def getSideBand(rx, LO, ssb):
    SSBparams = {
    '495': ( 61600.36, 104188.89, 0.0002977862, 313.0 ),
    '549': ( 57901.86, 109682.58, 0.0003117128, 313.0 ),
    '555': ( 60475.43, 116543.50, 0.0003021341, 308.0 ),
    '572': ( 58120.92, 115256.73, 0.0003128605, 314.0 )}
    d = 0.0
    C1 = SSBparams[rx][0]
    C2 = SSBparams[rx][1]
    sf = SSBparams[rx][2]
    sbpath = (-SSBparams[rx][3]+2.0*SSBparams[rx][3]*ssb/4095.0)*2.0
    for i in range(-2,3):
        s3900 = 299.79/(ssb + C1)*(C2 + i/sf)-LO/1.0e9;
        if abs(abs(s3900)-3.9) < abs(abs(d)-3.9):
            d = s3900;
    if d < 0.0: 
        IFfreq = -3900.0e6
    else:       
        IFfreq =  3900.0e6
    return (IFfreq,sbpath)

   
   
#if __name__ == "__main__":
#def level1b_importer_window():
class Newer(Level1b_cal):
    def __init__(self,spectra,calstw,con):
        Level1b_cal.__init__(self,spectra,calstw,con)
        self.ref_fit=Ref_fit()
    #def interpolate(self, mstw, m, stw, inttime, start):
    #    return self.ref_fit.interp(mstw, m, stw, inttime, start)


def level1b_importer():
    
    if len(argv)!=6:
        print 'error in function call, example usage: bin/ipython level1b_importer 46370(orbit1) 46372(orbit2)  AC2(backend) soda(version) filter'
        exit(0)

    orbit=argv[1] #59715
    orbit2=argv[2]
    backend=argv[3] #AC2
    soda=argv[4]
    ss=int(argv[5])
    con =db()
    
    #find min and max stws from orbit
    keys=[orbit,soda,orbit2]
    query=con.query('''select min(stw),max(stw)
                       from attitude_level1 where
                       floor(orbit)>={0} and floor(orbit)<={2} and soda={1}'''.format(*keys))
    result1=query.dictresult()
    if result1[0]['max']==None:
        print 'no attitude data from orbit '+str(orbit)
        exit(0)
    #find out which scans that starts in the orbit
    if backend=='AC1':
        stwoff=1
    else:
        stwoff=0
    temp=[result1[0]['min'],result1[0]['max'],backend,stwoff]
        
    if backend=='AC1':
        query=con.query('''select min(ac_level0.stw),max(ac_level0.stw) 
                   from ac_level0 
                   natural join getscansac1() 
                   natural join shk_level1
                   where start>={0} and start<={1}
                   '''.format(*temp))
    if backend=='AC2':
        query=con.query('''select min(ac_level0.stw),max(ac_level0.stw) 
                   from ac_level0 
                   natural join getscansac2()
                   natural join shk_level1
                   where start>={0} and start<={1}
                   '''.format(*temp))

    result2=query.dictresult()
    if result2[0]['max']==None:
        print 'no data from '+backend+' in orbit '+str(orbit)
        exit(0)
    

    if backend=='AC1':
        query=con.query('''select start from ac_level0 
                    natural join getscansac1() 
                    natural join shk_level1
                    where start>={0} and start<={1}
                    and backend='AC1' group by start order by start'''.format(*temp))
    if backend=='AC2':
        query=con.query('''select start from ac_level0 
                    natural join getscansac2()
                    natural join shk_level1
                    where start>={0} and start<={1}
                    and backend='AC2' group by start order by start'''.format(*temp))
    result2=query.dictresult()
    firstscan=result2[0]['start']
    lastscan=result2[len(result2)-1]['start']
    tdiff=45*60*16
    temp=[firstscan-tdiff,lastscan+tdiff,backend,stwoff,soda]
  
    #extract all necessary data for processing

    if backend=='AC1':
        query=con.query('''(
                       select ac_level0.stw,start,ssb_att,skybeamhit,cc,backend,
                       frontend,sig_type,
                       spectra,inttime,qerror,qachieved,
                       latitude,longitude,altitude,lo,ssb,
                       mixc,imageloadb,imageloada,hotloada,hotloadb,
                       ssb_fq,mech_type,vgeo,mode,
                       frontendsplit
                       from ac_level0
                       natural join ac_level1a
                       natural join shk_level1
                       natural join attitude_level1
                       natural join getscansac1()
                       join fba_level0 on (fba_level0.stw+{3}=ac_level0.stw)
                       where ac_level0.stw>={0} and ac_level0.stw<={1}
                       and backend='{2}' and soda={4} and lo>1 
                       order by stw)'''.format(*temp))
    if backend=='AC2':
        
        query=con.query('''(
                       select ac_level0.stw,start,ssb_att,skybeamhit,cc,backend,
                       frontend,sig_type,
                       spectra,inttime,qerror,qachieved,
                       latitude,longitude,altitude,lo,ssb,
                       mixc,imageloadb,imageloada,hotloada,hotloadb,
                       ssb_fq,mech_type,vgeo,mode,
                       frontendsplit
                       from ac_level0
                       natural join ac_level1a
                       natural join shk_level1
                       natural join attitude_level1
                       natural join getscansac2()
                       join fba_level0 on (fba_level0.stw+{3}=ac_level0.stw)
                       where ac_level0.stw>={0} and ac_level0.stw<={1}
                       and backend='{2}' and soda={4}
                       and lo>1 
                       order by stw)'''.format(*temp))
         
    result=query.dictresult()
    print str(len(result))+' rows of data in database used for processing'
    if result==[]:
        print 'could not extract all necessary data for processing '+backend 
        return
    
        
    for index,row in enumerate(result2):

        print 'processing scan '+str(row['start'])+' nr '+str(index)+' of '+str(len(result2))
        try:          
	    result3=copy.deepcopy(result)
            level1b_window_importer(result3,row['start'],tdiff,con,soda)
        except:
            pass

    con.close()
def level1b_window_importer(result,calstw,tdiff,con,soda):
   
    #extract data from the "result" and do a frequency calibration
    listofspec=[]
    start=0
    remove_ref=0
    remove_ref2=0
    remove_next_ref=0
    startspec=0
    for rowind,row in enumerate(result):
        if row['start']>=calstw-tdiff and row['start']<=calstw+tdiff:
            pass
        else:
            continue

        if startspec==0:
            #do not use any calibration signals from first scan
            #since we do not have any reference signal before this measurement
            start0=row['start']
            startspec=1
        if (row['sig_type']=='REF' and row['mech_type']=='CAL' and 
            row['start']==start0):
            remove_next_ref=1
            continue

        #remove first refrence data after a calibration
        if row['sig_type']=='REF' and row['mech_type']=='CAL':
            remove_next_ref=1
            #the number of references that should be removed
            #after a calibration
        if (row['sig_type']=='REF' and (row['mech_type']=='SK1' 
            or row['mech_type']=='SK2' or row['mech_type']=='REF') and 
            remove_next_ref>0):
            remove_next_ref=remove_next_ref-1
            continue
        #if a scan has several calibration signals
        #keep only the the second (the first has already
        #been removed in the query)
        if row['start']>start:
            start=row['start']
            start1=row['stw']
            got_ref=0
            
        #remove unwished calibration spectrum
        if (row['stw']>=start1 and row['sig_type']=='REF' and 
            row['mech_type']=='CAL'):
            if got_ref==0:
                #get next ref
                got_ref=1
                continue
            elif got_ref==1:
                got_ref=2
            else:
                continue
        
        if row['sig_type']=='REF' and row['mech_type']=='CAL':
           row['sig_type']='CAL' 
        spec=Spectra(con,row,0)
        spec.tuning()
	if spec.lofreq<1:
        	continue	
	listofspec.append(spec)
        if row['sig_type']=='REF' and (row['mech_type']=='SK1' or
           row['mech_type']=='SK2' or row['mech_type']=='REF' ):
             row['sig_type']='SIG'
             spec=Spectra(con,row,1)
             spec.tuning()
             listofspec.append(spec)

        if spec.frontend=='SPL':
            #split data into two spectra
            aa=odin.Spectrum()
            aa.backend=spec.backend
            aa.channels=len(spec.data)
            aa.data=spec.data
            aa.lofreq=spec.lofreq
            aa.intmode=spec.intmode
            aa.frontend=spec.frontend
            (s1, s2) = aa.Split()
            if s1.frontend==row['frontendsplit']:
                spec.data=s1.data
                spec.intmode=s1.intmode
                spec.frontend=s1.frontend
            if s2.frontend==row['frontendsplit']:
                spec.data=s2.data
                spec.intmode=s2.intmode
                spec.frontend=s2.frontend
        
    #group data by frontend
    #frontend=['495', '549', '555', '572']
    frontend=[]
    for row in listofspec:
        frontend.append(row.frontend)
    frontend=numpy.array(frontend)
    frontends=numpy.unique(frontend)
    if len(frontends)==0:
	return
    if len(frontends)==1:
        fe={frontends[0] : [],
            }
    elif len(frontends)==2:
        fe={frontends[0] : [],
            frontends[1]:  [],
            }
    elif len(frontends)==3:
        fe={frontends[0] : [],
            frontends[1]:  [],
            frontends[2]:  [],
            }
    elif len(frontends)==4:
        fe={frontends[0] : [],
            frontends[1]:  [],
            frontends[2]:  [],
            frontends[3]:  [],
            }
    for row in listofspec:
        fe[row.frontend].append(row)
    spectra=[]
    frontends=fe.keys()
    for frontend in frontends:
        spectra=fe[frontend]
        fsky=[]
        for spec in spectra:
            fsky.append(spec.skyfreq)
        fsky=numpy.array(fsky)
        # create vector with all indices of fsky where frequency
        # changes by more than one MHz
        modes = numpy.nonzero(abs(fsky[1:]-fsky[:-1]) > 1.0e6)
        #modes =numpy.ndarray(shape=(len(modes[0]),),buffer=modes[0])
        modes=numpy.array(modes[0])
        # prepend integer '0' and append integer 'len(fsky)'
        modes = numpy.concatenate((numpy.concatenate(([0], modes)), 
                                   [len(fsky)]))
        for m in range(len(modes)-1):
            start=int(modes[m]+1)
            stop=int(modes[m+1])
            #ac=Level1b_cal(spectra[start:stop],calstw,con)
            ac=Newer(spectra[start:stop],calstw,con)
            
            #intensity calibrate
            (calibrated,VERSION,Tspill)=ac.calibrate()
            if calibrated==None:
                continue
            #store data into database tables
            #ac_level1b (spectra) or ac_cal_level1b (tsys and ssb)
            for s in calibrated:
                specs=[]
                fm=ac.freqMode(s)
                #if s.type == 'CAL':
                #    calstw=s.stw 
                s.source = ac.source
                s.topic = ac.topic
                #if s.ref==0:
                #    continue
                if ac.split:
                    #split data into two spectra
                    aa=odin.Spectrum()
                    aa.backend=s.backend
                    aa.channels=len(s.data)
                    aa.data=s.data
                    aa.lofreq=s.lofreq
                    aa.intmode=s.intmode
                    (s1, s2) = aa.Split()
                    specs.append(s1)
                    specs.append(s2)
                else:
                    specs.append(s)

		insertcal=0
                for spec in specs: 
		   	 
                    #spec.data=spec.data[0:112]
                    if s.type=='SPE' and s.start==calstw:
			insertcal=1
                        temp={
                    'stw'             :s.stw,
                    'backend'         :s.backend,
	            'frontend'        :s.frontend,
                    'version'         :int(VERSION),
                    'intmode'         :spec.intmode,
                    'soda'            :soda,
                    'spectra'         :con.escape_bytea(spec.data.tostring()),
                    'channels'        :len(spec.data),
                    'skyfreq'         :s.skyfreq,
                    'lofreq'          :s.lofreq,
                    'restfreq'        :s.restfreq,
                    'maxsuppression'  :s.maxsup,
                    'tsys'            :s.tsys,
                    'sourcemode'      :ac.topic,
                    'freqmode'        :ac.freqmode,
                    'efftime'         :s.efftime,
                    'sbpath'          :s.sbpath,
                    'calstw'          :calstw
                    }
                        
                        con.insert('ac_level1b',temp)
		for spec in specs:
                    if s.type=='CAL' or s.type=='SSB' and insertcal==1:
			print s.lofreq
                        temp={
                    'stw'             :s.stw,
                    'backend'         :s.backend,
	            'frontend'        :s.frontend,
                    'version'         :int(VERSION),
                    'spectype'        :s.type,
                    'intmode'         :spec.intmode,
                    'soda'            :soda,
                    'spectra'         :con.escape_bytea(spec.data.tostring()),
                    'channels'        :len(spec.data),
                    'skyfreq'         :s.skyfreq,
                    'lofreq'          :s.lofreq,
                    'restfreq'        :s.restfreq,
                    'maxsuppression'  :s.maxsup,
                    'sourcemode'      :ac.topic,
                    'freqmode'        :ac.freqmode,
                    'sbpath'          :s.sbpath,
                    'tspill'          :Tspill,
                    }
                        con.insert('ac_cal_level1b',temp)
            
    
                        




