import numpy
import copy
from oops import odin
from pg import DB
from sys import stderr,stdout,stdin,argv,exit
import h5py
 
class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin')


def level1b_exporter():
    '''export data orbit data from database tables
       and store data into hdf5 format'''
    #example usage: bin/level1b_exporter 8575 AC1 odintestfile.hdf5

    orbit=argv[1] 
    backend=argv[2] 
    outfile=argv[3]

    con =db()
    #find min and max stws from orbit
    query=con.query('''select min(stw),max(stw)
                       from attitude_level1 where
                       floor(orbit)={0}'''.format(orbit))
    result=query.dictresult()
    if result[0]['max']==None:
        print 'no attitude data from orbit '+str(orbit)
        exit(0)

    #find out which scans that starts in the orbit
    if backend=='AC1':
        stwoff=1
    else:
        stwoff=0
    temp=[result[0]['min'],result[0]['max'],backend,stwoff]
    if backend=='AC1':
        query=con.query('''select min(ac_level0.stw),max(ac_level0.stw) 
                   from ac_level0 
                   natural join getscansac1() 
                   where start>={0} and start<={1}
                   and backend='{2}'
                   '''.format(*temp))
    
    if backend=='AC2':
        query=con.query('''select min(ac_level0.stw),max(ac_level0.stw) 
                   from ac_level0 
                   natural join getscansac2() 
                   where start>={0} and start<={1}
                   and backend='{2}'
                   '''.format(*temp))

    result=query.dictresult()
    if result[0]['max']==None:
        print 'no data from '+backend+' in orbit '+str(orbit)
        exit(0)

    #extract all necessary data for the orbit
    temp=[result[0]['min'],result[0]['max'],backend]
    query=con.query('''select stw,backend,orbit,mjd,lst,intmode,spectra,
                       alevel,version,
                       channels,
                       skyfreq,lofreq,restfreq,maxsuppression,
                       tsys,sourcemode,freqmode,efftime,sbpath,
                       calstw,latitude,longitude,altitude,skybeamhit,  
                       ra2000,dec2000,vsource,qtarget,qachieved,qerror,
                       gpspos,gpsvel,sunpos,moonpos,sunzd,vgeo,vlsr,
                       ssb_fq,inttime,frontend,
                       hotloada,lo
                       from ac_level1b
                       natural join attitude_level1
                       natural join ac_level0
                       natural join shk_level1
                       where stw>={0} and stw<={1} and backend='{2}'
                       order by stw'''.format(*temp))
    result=query.dictresult()
    if result==[]:
        print 'could not extract all necessary data for processing '+backend+' in orbit '+orbit 
        exit(0)
    g= h5py.File(outfile,'w')
    stw=[]
    backend=[]
    orbit=[]
    mjd=[]
    alevel=[]
    lst=[]
    spectra=[]
    intmode=[]
    channels=[]
    skyfreq=[]
    lofreq=[]
    restfreq=[]
    maxsuppression=[]
    tsys=[]
    sourcemode=[]
    freqmode=[]
    efftime=[]
    sbpath=[]
    latitude=[]    
    longitude=[]   
    altitude=[]      
    skybeamhit=[]    
    ra2000=[]            
    dec2000=[]      
    vsource=[]     
    qtarget=[]       
    qachieved=[]     
    qerror=[]        
    gpspos=[]       
    gpsvel=[]      
    sunpos=[]       
    moonpos=[]      
    sunzd=[]       
    vgeo=[]          
    vlsr=[]
    ssb_fq=[]
    inttime=[]
    frontend=[]
    hotloada=[]
    lo=[]
    for res in result:
        stw.append(res['stw'])
        backend.append(res['backend'])
        mjd.append(res['mjd'])
        orbit.append(res['orbit'])
        lst.append(res['lst'])
        spec=numpy.ndarray(shape=(res['channels'],),dtype='float64',
                           buffer=con.unescape_bytea(res['spectra']))
        spectra.append(spec)
        intmode.append(res['intmode'])
        channels.append(res['channels'])
        skyfreq.append(res['skyfreq'])
        lofreq.append(res['lofreq'])
        restfreq.append(res['restfreq'])
        maxsuppression.append(res['maxsuppression'])
        tsys.append(res['tsys'])
        sourcemode.append(res['sourcemode']+' FM='+str(res['freqmode']))
        alevel.append(res['alevel']+res['version'])
        freqmode.append(res['freqmode'])
        efftime.append(res['efftime'])
        sbpath.append(res['sbpath'])
        latitude.append(res['latitude'])  
        longitude.append(res['longitude']) 
        altitude.append(res['altitude'])    
        skybeamhit.append(res['skybeamhit'])  
        ra2000.append(res['ra2000'])          
        dec2000.append(res['dec2000'])    
        vsource.append(res['vsource'])   
        qtarget.append(eval(res['qtarget'].replace('{','(').replace('}',')')))
        qachieved.append(eval(res['qachieved'].replace('{','(').replace('}',')')))
        qerror.append(eval(res['qerror'].replace('{','(').replace('}',')')))
        gpspos.append(eval(res['gpspos'].replace('{','(').replace('}',')')))
        gpsvel.append(eval(res['gpsvel'].replace('{','(').replace('}',')')))  
        sunpos.append(eval(res['sunpos'].replace('{','(').replace('}',')')))    
        moonpos.append(eval(res['moonpos'].replace('{','(').replace('}',')')))  
        sunzd.append(res['sunzd'])     
        vgeo.append(res['vgeo'])        
        vlsr.append(res['vlsr'])
        ssb_fq.append(eval(res['ssb_fq'].replace('{','(').replace('}',')')))
        inttime.append(res['inttime'])
        frontend.append(res['frontend'])
        hotloada.append(res['hotloada'])
        lo.append(res['lo'])
    dtype1=[('Level', '>u2'), 
            ('STW', '>u4'), ('MJD', '>f8'), ('Orbit', '>f8'), 
            ('LST', '>f4'), ('Source', '|S32'),   
            ('Frontend', '|S32'), ('Backend', '|S32'), 
            ('SkyBeamHit', '>i2'), ('RA2000', '>f4'), ('Dec2000', '>f4'), 
            ('VSource', '>f4'), ('Longitude', '>f4'), ('Latitude', '>f4'), 
            ('Altitude', '>f4'),('Qtarget', '>f8', (4,)), 
            ('Qachieved', '>f8', (4,)), ('Qerror', '>f8', (3,)), 
            ('GPSpos', '>f8', (3,)), ('GPSvel', '>f8', (3,)), 
            ('SunPos', '>f8', (3,)), ('MoonPos', '>f8', (3,)), 
            ('SunZD', '>f4'), ('Vgeo', '>f4'), ('Vlsr', '>f4'), 
            ('Tcal', '>f4'), ('Tsys', '>f4'), ('SBpath', '>f4'), 
            ('LOFreq', '>f8'), ('SkyFreq', '>f8'), ('RestFreq', '>f8'), 
            ('MaxSuppression', '>f8'), ('FreqCal', '>f8', (4,)), 
            ('IntMode', '>i4'), ('IntTime', '>f4'), ('EffTime', '>f4'), 
            ('Channels', '>i4'),]
    dtype2=[('Array','>f8', (len(spectra[0]),))]  
    dset1 = g.create_dataset("SMR", shape=(len(stw),1),dtype=dtype1)
    dset2 = g.create_dataset("SPECTRUM",data=spectra)
    for ind in range(len(stw)):
        data=(alevel[ind],stw[ind],mjd[ind],orbit[ind],lst[ind],
              sourcemode[ind],
              frontend[ind],backend[ind],skybeamhit[ind],ra2000[ind],
              dec2000[ind],vsource[ind],longitude[ind],latitude[ind],
              altitude[ind],qtarget[ind],qachieved[ind],qerror[ind],
              gpspos[ind],gpsvel[ind],
              sunpos[ind],moonpos[ind],sunzd[ind],
              vgeo[ind],vlsr[ind],hotloada[ind],
              tsys[ind],sbpath[ind],lofreq[ind],
              skyfreq[ind],restfreq[ind],
              maxsuppression[ind],ssb_fq[ind],intmode[ind],
              inttime[ind],efftime[ind],channels[ind])
        dset1[ind]=data
       
    g.close()
    con.close()
    
