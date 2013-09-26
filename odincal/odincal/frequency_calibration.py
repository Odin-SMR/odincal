import numpy


class Spectra: 
    """A class derived to perform frequency calibration of odin spectra"""
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
	self.gain=[]
    def tuning(self):

        if self.frontend == '119':
            IFfreq = 3900.0e6
            self.lofreq = 114.8498600000000e+9
            self.fcalibrate(self.lofreq,IFfreq)
            return
        
        rxs = { '495': 1, '549': 2, '555': 3, '572': 4 }
        if not self.frontend in rxs.keys():
            return 
        (IFfreq,sbpath) = self.getSideBand(self.frontend, self.lofreq, self.ssb)
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
        # apply Doppler correction
        self.restfreq = self.skyfreq/(1.0 - self.vgeo/2.99792456e8);
       
 
    def getSideBand(self,rx, LO, ssb):
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

    def freqMode(self):
        df = 30.0e6
        self.freqmode = 0
        self.split = 0
        LO = self.lofreq*(1.0 + self.vgeo/2.99792456e8)
        modes = {
            'STRAT':  "Stratospheric",
            'ODD_H':  "Odd hydrogen",
            'ODD_N':  "Odd nitrogen",
            'WATER':  "Water isotope",
            'SUMMER': "Summer mesosphere",
            'DYNAM':  "Transport"
            }

        config = None
        if self.backend == 'AC1':
            if self.frontend == '495':
                config = [[492.750e9,23, "DYNAM", 0],
                          [495.402e9,29, "DYNAM", 0],
                          [499.698e9,25, "DYNAM", 0]]
            elif self.frontend == '549':
                config = [[548.502e9, 2, "STRAT", 0],
                          [553.050e9,19, "WATER", 0],
                          [547.752e9,21, "WATER", 1],
                          [553.302e9,23, "DYNAM", 0],
                          [553.302e9,29, "DYNAM", 0]]
            elif self.frontend == '555':
                config = [[553.298e9,13, "SUMMER", 0]]
            elif self.frontend == '572':
                config = [[572.762e9,24, "DYNAM", 0]]
        elif self.backend == 'AC2':
            if self.frontend == '495':
                config = [[497.880e9, 1, "STRAT", 1],
                          [492.750e9, 8, "WATER", 1],
                          [494.250e9,17, "WATER", 0],
                          [499.698e9,25, "DYNAM", 0]]
            elif self.frontend == '572':
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
        
       


 
if __name__ == "__main__":
    pass
