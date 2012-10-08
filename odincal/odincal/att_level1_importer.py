from oops import odin
import numpy
from pg import DB
from sys import stderr,stdout,stdin,argv,exit

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin')


def djl(year, mon, day, hour, min, secs):
        dn = 367L*year - 7*(year+(mon+9)/12)/4 \
             - 3*((year+(mon-9)/7)/100+1)/4 + 275*mon/9 \
             + day + 1721029L;
        jd = float(dn)-0.5+(hour+(min+secs/60.0)/60.0)/24.0
        return jd

def att_level1_importer():
    soda=argv[1]
    con =db()
    query=con.query('''select stw,backend,inttime from ac_level0
                       natural left join attitude_level1 
                       where sig_type='SIG' 
                       and (soda is NULL or soda!={0})
                       order by stw'''.format(soda))
    sigresult=query.dictresult()
    for sig in sigresult:
        keys=[sig['stw'],soda]
	query=con.query('''select year,mon,day,hour,min,secs,stw,
                           orbit,qt,qa,qe,gps,acs
	                   from attitude_level0 where 
                           stw>{0}-200 and stw<{0}+200 
                           and soda={1}
                           order by stw'''.format(*keys))
	result=query.dictresult()
	if len(result)>0:
            #interpolate attitude data to desired stw
            #before doing the actual processing
            stw=float(sig['stw'])-sig['inttime']*16.0/2.0
            #first create a lookup matrix
            cols = 2+2*4+3+6+1
            rows=len(result)
            lookup = numpy.zeros(shape=(rows,cols))
            attstw=numpy.zeros(shape=(rows,))
            for index,row in enumerate(result):
                attstw[index]=float(row['stw'])	
                #extract database data
	       	JD=djl(row['year'],row['mon'],row['day'],
	       	       row['hour'],row['min'],row['secs'])
                qt=eval(row['qt'].replace('{','(').replace('}',')'))
                qa=eval(row['qa'].replace('{','(').replace('}',')'))
                qe=eval(row['qe'].replace('{','(').replace('}',')'))
                gps=eval(row['gps'].replace('{','(').replace('}',')'))
                #fill up the lookup table with data
                lookup[index, 0: 2] = numpy.array((JD, row['orbit']))
                lookup[index, 2: 6] = numpy.array(qt)
                lookup[index, 6:10] = numpy.array(qa)
                lookup[index,10:13] = numpy.array(qe)
                lookup[index,13:19] = numpy.array(gps)
                lookup[index,19]    = row['acs']
            #search for the index with the lowest stw 
            #above the desired stw in the lookup table 
            ind=(attstw>stw).nonzero()[0]
            if len(ind)==0:
                continue
                #not enough match
            if ind[0]==0:
                continue
                #not enough match
            i=ind[0]
            #now interpolate
            dt = attstw[i]-attstw[i-1]
            dt0 = attstw[i]-stw
            dt1 = stw-attstw[i-1]
            att = (dt0*lookup[i-1,:] + dt1*lookup[i,:])/dt
            t = (att[0], long(stw), att[1],
                 tuple(att[2:6]), tuple(att[6:10]),
                 tuple(att[10:13]), tuple(att[13:19]), att[19])
            #now process data using Ohlbergs code (s.Attitude(t))
            s=odin.Spectrum()
            s.stw=long(stw)
            s.Attitude(t)
            datadict={
                'stw'       :sig['stw'],
                'backend'   :sig['backend'],
                'soda'      :soda,
                'mjd'       :s.mjd,
                'lst'       :s.lst,
                'orbit'     :s.orbit,
                'longitude' :s.longitude,
                'latitude'  :s.latitude,
                'altitude'  :s.altitude,
                'skybeamhit':s.skybeamhit,
                'ra2000'    :s.ra2000,
                'dec2000'   :s.dec2000,
                'vsource'   :s.vsource,
                'qtarget'   :"{{{},{},{},{}}}".format(*s.qtarget),
                'qachieved' :"{{{},{},{},{}}}".format(*s.qachieved),
                'qerror'    :"{{{},{},{}}}".format(*s.qerror),
                'gpspos'    :"{{{},{},{}}}".format(*s.gpspos),
                'gpsvel'    :"{{{},{},{}}}".format(*s.gpsvel),
                'sunpos'    :"{{{},{},{}}}".format(*s.sunpos),
                'moonpos'   :"{{{},{},{}}}".format(*s.moonpos),
                'sunzd'     :s.sunzd,
                'vgeo'      :s.vgeo,
                'vlsr'      :s.vlsr,
                'alevel'    :s.level,
                }
            con.insert('attitude_level1',datadict)
    con.close()
            