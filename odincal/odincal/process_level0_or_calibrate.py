from subprocess import call
from pg import DB
from datetime import date,datetime,timedelta 
from odincal.config import config
from os.path import join,split
from odincal.level0 import import_file

configuration=config.get('odincal','config')
period_starts=eval(config.get(configuration,'period_start'))
period_ends=eval(config.get(configuration,'period_end'))
PROCESS_NUM=2
PROCESS_CHUNKSIZE=10

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin_test')
   
def get_full_path(filename):
    dirname='/misc/pearl/odin/level0/'
    if filename.endswith('ac1'):
        filetype='ac1'
    elif filename.endswith('ac2'):
        filetype='ac1'
    elif filename.endswith('shk'):
        filetype='shk'
    elif filename.endswith('fba'):
        filetype='fba'
    elif filename.endswith('att'):
        filetype='att'
    else:
        pass
    partdir=filename[0:3]
    full_filename=join(dirname,filetype,partdir,filename)

    dirname='/home/bengt/data/odin/'
    full_filename=join(dirname,filetype,filename)
    return full_filename



if __name__=='__main__':
    con=db()

    #make a list of which periods we consider
    periods=[]
    for period_start,period_end in zip(period_starts,period_ends):
        if period_end=='today':
            end=datetime.today()
            info='today'
        else:
            end= datetime.strptime(period_end, '%Y-%m-%d')
            info='old period'
        start= datetime.strptime(period_start, '%Y-%m-%d')
        start_1=start-timedelta(days=1)
        end_1=end+timedelta(days=1)
        period={
            'start'   : start.date(),
            'end'     : end.date(),
            'start-1' : start_1.date(),
            'end+1'   : end_1.date(),
            'info'    : info
            }    
        periods.append(period)

    #loop over the periods
    #perform level0 import for the period first
    #if all level0 import is done for a period
    #we can start to calibrate
        
    for period in periods:
        #for level0_period we consider to import level0 data
        level0_period=[str(period['start-1']),str(period['end+1']),
                       PROCESS_NUM*PROCESS_CHUNKSIZE]
        #for ac_period we consider to calibrate data 
        ac_period=[str(period['start']),str(period['end']),
                   PROCESS_NUM*PROCESS_CHUNKSIZE]
    
        #check if we have any level0_files at all for this period
        query=con.query('''
           select file,measurement_date from level0_files
           where measurement_date>='{0}' and measurement_date<='{1}' limit 1 
           '''.format(*level0_period))
        result=query.dictresult()
        if len(result)==0:
            #we do not have any level0_files for this period
            #continue with next period
            continue

        #check if we have any level0 files 
        #where data is not imported for this period
        query=con.query('''
           select level0_files.file,measurement_date from level0_files 
           left join level0_files_imported using(file)
           left join level0_files_in_process using(file)
           where measurement_date>='{0}' and measurement_date<='{1}'
           and level0_files_imported.created is Null and
           level0_files_in_process.created is Null
           order by measurement_date asc limit {2}
           '''.format(*level0_period))

        result=query.dictresult()

        if len(result)>0:
            #do level0 import
            job_list = map(None, *([iter(result)] * PROCESS_CHUNKSIZE))
            for grp in job_list:
                for row in grp:
                    if not row is None:
                        fullname=get_full_path(row['file'])
                        temp={'file':row['file'],
                              'created': datetime.today()}
                        print row['file'],row['measurement_date']
                        con.insert('level0_files_in_process',temp) 
                        
                        #this is what the jobscript should do
                        import_file(fullname)
                        con.query('''delete from level0_files_in_process 
                         where file='{0}' '''.format(row['file']))
                        con.insert('level0_files_imported',temp)
                        
                        
                #create jobscript,import_file(filename)
                #launch jobscript,
        else:
            #check that all level0 files are imported
            #we can possibly have level0 files in process
            query=con.query('''
           select file,measurement_date from level0_files
           left join level0_files_imported using(file) 
           where measurement_date>='{0}' and measurement_date<='{1}' 
           and level0_files_imported.created is Null
           order by file limit 1
           '''.format(*level0_period))
            result=query.dictresult()

            if len(result)>0:
                #there are level0 files in process,
                #we should not start to calibrate data within
                #this period yet
                #continue to next period
                continue
            
            #check if this is the near real time period
            if 1 :#period['info']=='today':
                #require some extra check
                #check which is the last date from where we have all
                #different files imported
                query=con.query('''
             select right(file,3) as ext,max(measurement_date) 
             from level0_files_imported 
             join level0_files using (file)
             where measurement_date>='{0}' and
             measurement_date<='{1}' group by ext'''.format(*level0_period))
                result=query.dictresult()
                t0=datetime(2100,01,01)
                att_data=0
                shk_data=0
                fba_data=0
                for row in result:
                    t1=datetime.strptime(row['max'], '%Y-%m-%d')
                    if t1<t0:
                        t0=t1
                    if row['ext']=='att':
                       att_data=1
                    if row['ext']=='shk':
                       shk_data=1
                    if row['ext']=='fba':
                       fba_data=1
                if att_data==1 and shk_data==1 and fba_data==1:
                    #the latest date we have attitude,shk,and fba data
                    #is t1, now subtract one day for safety reason
                    t1=t1-timedelta(days=1)
                    ac_period[1]=str(t1.date())
                else:
                    #continue to next period
                    continue  

                 
            #check which ac_files that are not calibrated
            query=con.query('''
           select file from level0_files
           join level0_files_imported using(file)
           left join processed using(file)
           left join in_process using(file)
           where measurement_date>='{0}' and measurement_date<='{1}' 
           and (right(file,3)='ac1' or right(file,3)='ac2')
           and processed.total_scans is Null and
           in_process.created is Null
           order by measurement_date desc limit {2}
           '''.format(*ac_period))
            result=query.dictresult()
            
            if len(result)>0:
               #do level1b_calibration import
                job_list = map(None, *([iter(result)] * PROCESS_CHUNKSIZE))
                for grp in job_list:
                    for row in grp:
                        if not row is None:
                              temp={
                                  'file'   :row['file'],
                                  'created': datetime.today()
                                  }
                              con.insert('in_process',temp)
            
                for grp in job_list:
                    for row in grp:
                        if not row is None:
                              binfile='/home/bengt/work/odincal_2013/odincal_outputfiles/odincal/bin/level1b_window_importer'
                              ac=row['file'][-3::]
                              call([binfile,file,ac.upper(),'1'])
                              
                              #con.insert('processed',temp)
                              #con.query('''delete from in_process 
                              #where file='{0}' '''.format(row['file']))
                         #create jobscript
                         #launch jobscript,
            

    con.close()



