import copy
import numpy
from odincal.ac_level1a_importer import ac_level1a_importer
from odincal.att_level1_importer import att_level1_importer
from odincal.shk_level1_importer import shk_level1_importer
import pg
from pg import DB
from sys import stderr,stdout,stdin,argv,exit
from odincal.config import config

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname=config.get('database','dbname'),
                         user=config.get('database','user'),
                         host=config.get('database','host'),
                         passwd=config.get('database','passwd'),
                         )


class Prepare_data():
    '''prepare level0 database data for calibration''' 
    def __init__(self,acfile,backend,version,con): 
        self.acfile=acfile
        self.backend=backend
        self.con=con
        self.version=version
    def get_stw_from_acfile(self):
        temp=[self.acfile]
        query=self.con.query('''select min(stw),max(stw)
                       from ac_level0 where file='{0}' '''.format(*temp))
        result=query.dictresult()
        if result[0]['max']==None:
	    #no data from file imported in ac_level0 table
            return -1,-1
        else:
            return result[0]['min'],result[0]['max']
        
    def get_soda_version(self,stw1,stw2):
        temp=[stw1,stw2]
        query=self.con.query('''select soda 
                       from attitude_level0 where stw>{0} and stw<{1} 
                       group by soda'''.format(*temp))
        result=query.dictresult()
        if result==[]:
            return -1
        else:
            return result[0]['soda'] 
    def att_level1_process(self,stw1,stw2,sodaversion):
        error=att_level1_importer(stw1,stw2,sodaversion,self.backend)
        return error
    def shk_level1_process(self,stw1,stw2):
        error=shk_level1_importer(stw1,stw2,self.backend)
        return error
    def ac_level1a_process(self,stw1,stw2):
        error=ac_level1a_importer(stw1,stw2,self.backend)
        return error
    def get_scan_starts(self,stw1,stw2):
        temp=[stw1,stw2]
        if self.backend=='AC1':
            query=self.con.query('''select start,ssb_att from ac_level0 
                    natural join getscansac1({0},{1}) 
                    join shk_level1 using(stw,backend)
                    where start>={0} and start<={1}
                    and backend='AC1' group by start,ssb_att 
                    order by start'''.format(*temp))
            
        else:
            query=self.con.query('''select start,ssb_att from ac_level0 
                    natural join getscansac2({0},{1})
                    join shk_level1 using(stw,backend)
                    where start>={0} and start<={1}
                    and backend='AC2' group by start,ssb_att 
                    order by start'''.format(*temp))
        result=query.dictresult()
        return result

    def get_data_for_calibration(self,stw1,stw2,tdiff,sodaversion):
        temp=[stw1-tdiff,stw2+tdiff,sodaversion]
        if self.backend=='AC1':

            query=self.con.query('''(
                       select ac_level0.stw,start,ssb_att,skybeamhit,cc,
                       ac_level0.backend,
                       frontend,sig_type,
                       spectra,inttime,qerror,qachieved,
                       latitude,longitude,altitude,lo,ssb,
                       mixc,imageloadb,imageloada,hotloada,hotloadb,
                       ssb_fq,mech_type,vgeo,mode,
                       frontendsplit
                       from ac_level0
                       natural join getscansac1({0},{1})
                       join ac_level1a using (backend,stw)
                       join shk_level1 using (backend,stw)
                       join attitude_level1 using (backend,stw)
                       where ac_level0.stw>={0} and ac_level0.stw<={1}
                       and ac_level0.backend='AC1' and soda={2} and lo>1 
                       order by stw)'''.format(*temp))
      

        if self.backend=='AC2':
        
            query=self.con.query('''(
                       select ac_level0.stw,start,ssb_att,skybeamhit,cc,
                       ac_level0.backend,
                       frontend,sig_type,
                       spectra,inttime,qerror,qachieved,
                       latitude,longitude,altitude,lo,ssb,
                       mixc,imageloadb,imageloada,hotloada,hotloadb,
                       ssb_fq,mech_type,vgeo,mode,
                       frontendsplit
                       from ac_level0
                        natural join getscansac2({0},{1})
                       join ac_level1a using(stw,backend)
                       join shk_level1 using(stw,backend)
                       join attitude_level1 using(stw,backend)
                       where ac_level0.stw>={0} and ac_level0.stw<={1}
                       and ac_level0.backend='AC2' and soda={2}
                       and lo>1 
                       order by stw)'''.format(*temp))
            
        result=query.dictresult()
        print len(result)
        return result

    def filter_data(self,result,start,ssb_att,scanfrontend,tdiff):
        spectra=[]
        remove_next_ref=0
        calspec=0
        start0=0
        for row in result:

            if row['frontendsplit']!=scanfrontend:
                continue
            if row['start']>=start-tdiff and row['start']<=start+tdiff:
                pass
            else:
                continue
            if row['ssb_att']!=ssb_att:
                continue
            
            if row['start']>start0:
                start0=row['start']
                calspec=0

            #remove sky beam references
            if row['sig_type']=='REF' and row['mech_type']=='SK2':
                remove_next_ref=1
                continue
            if row['sig_type']=='REF' and row['mech_type']=='REF':
                remove_next_ref=1
                continue
            #remove data that where skybeam1 interfere with objects
            EARTH1=0x0001
            MOON1=0x0002
            GALAX1=0x0004
            SUN1=0x0008
            if  ( (row['sig_type']=='REF' and row['mech_type']=='SK1') 
                and
                (  ( row['skybeamhit'] & EARTH1==EARTH1) or 
                   ( row['skybeamhit'] & MOON1==MOON1) or 
                   ( row['skybeamhit'] & SUN1==SUN1)
                   )):
                continue

            #remove first refrence data after a calibration
            if row['sig_type']=='REF' and row['mech_type']=='CAL':
                remove_next_ref=1
            #do not use SK1 signals when the earlier
            #reference signal was from another source
            if (row['sig_type']=='REF' and row['mech_type']=='SK1'
                and remove_next_ref==1):
                remove_next_ref=0
                continue
            
            #remove unwished calibration spectrum
            #keep only the second 
            if (row['sig_type']=='REF' and row['mech_type']=='CAL'):
                calspec=calspec+1
                if calspec==2:
                    row['sig_type']='CAL'
                else:
                    continue
            spectra.append(row)
        return spectra


def main():
    '''prepare data for calibration'''
     
    #acfile='100b8721.ac1'
    #backend='AC1'
    backend=argv[1]
    acfile=argv[2]
    level0_process=1
    version=8
    tdiff=45*60*16
    con=db()

    p=Prepare_data(acfile,backend,version,con)
    
    #find out max and min stw from acfile to calibrate
    stw1,stw2=p.get_stw_from_acfile()
    if stw1==-1:
        info={'info': 'no ac data',
              'total_scans': 0,
              'success_scans': 0,
              'version': version}
        print info
        return   

    #find out which sodaversion we have for this data
    sodaversion=p.get_soda_version(stw1,stw2) 
    if sodaversion==-1:
        info={'info': 'no attitude data',
              'total_scans': 0,
              'success_scans': 0,
              'version': version}
        print info
        return

    #perform level0 data processing
    if level0_process==1:
       error=p.att_level1_process(stw1-tdiff,stw2+tdiff,sodaversion)
       if error==1:
           print {'info': 'pg problem'}
           return
       error=p.shk_level1_process(stw1-tdiff,stw2+tdiff)
       if error==1:
           print {'info': 'pg problem'}
           return
       error=p.ac_level1a_process(stw1-tdiff,stw2+tdiff)
       if error==1:
           print {'info': 'pg problem'}
           return
    
    con.close()
   

if __name__=='__main__':
    main()