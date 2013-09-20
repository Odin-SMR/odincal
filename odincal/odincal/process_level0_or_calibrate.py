from subprocess import call
from pg import DB
from datetime import date,datetime,timedelta 
from tempfile import NamedTemporaryFile
from odincal.config import config
from os.path import join,split
from pkg_resources import resource_filename
from odincal.launcher import ShellLauncher
import torquepy
import numpy as N

configuration=config.get('odincal','config')
period_starts=eval(config.get(configuration,'period_start'))
period_ends=eval(config.get(configuration,'period_end'))
version=int(config.get(configuration,'version'))

binfile=resource_filename('odincal','dummy').replace(
        'odincal/odincal/dummy','bin/level1b_window_importer')
interpreter=resource_filename('odincal','dummy').replace(
        'odincal/odincal/dummy','bin/odinpy')
launcher='shell'
Error_Path=resource_filename('odincal','dummy').replace('dummy','')
Output_Path=resource_filename('odincal','dummy').replace('dummy','')

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname=config.get('database','dbname'),
                         user=config.get('database','user'),
                         host=config.get('database','host'),
                         passwd=config.get('database','passwd'),
                         )



def get_full_path(filename):
    dirname='/misc/pearl/odin/level0/'
    if filename.endswith('ac1'):
        filetype='ac1'
    elif filename.endswith('ac2'):
        filetype='ac2'
    elif filename.endswith('shk'):
        filetype='shk'
    elif filename.endswith('fba'):
        filetype='fba'
    elif filename.endswith('att'):
	if (eval('0x'+filename.replace('.att',''))<
    eval('0x'+'0ce8666f.att'.replace('.att',''))):
                filetype='att_17'
        else:   
                filetype='att'
    else:
        pass
    partdir=filename[0:3]
    full_filename=join(dirname,filetype,partdir,filename)

    #dirname='/home/bengt/data/odin/'
    #full_filename=join(dirname,filetype,filename)
    return full_filename



def main():
    
    PROCESS_NUM_LEVEL0=400
    PROCESS_CHUNKSIZE_LEVEL0=40
    PROCESS_NUM_LEVEL1B=400
    PROCESS_CHUNKSIZE_LEVEL1B=1
    PROCESS_QUEUE=400

    con=db()
    
    if launcher=='not shell':
        tc = ShellLauncher()
    else:
        tc = torquepy.TorqueConnection('morion')

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
    inqueue = tc.inqueue('odincal')
    no_inqueue = len(inqueue)    
    no_available=N.max([PROCESS_QUEUE-no_inqueue,0])
    print no_available
    if no_available==0:
    	exit(0)
    if PROCESS_NUM_LEVEL0>no_available:
    	PROCESS_NUM_LEVEL0=no_available
    if PROCESS_NUM_LEVEL1B>no_available:
	PROCESS_NUM_LEVEL1B=no_available

    for period in periods:
	print period
        #for level0_period we consider to import level0 data
        level0_period=[str(period['start-1']),str(period['end+1']),
                       PROCESS_NUM_LEVEL0*PROCESS_CHUNKSIZE_LEVEL0]
        #for ac_period we consider to calibrate data 
        ac_period=[str(period['start']),str(period['end']),
                   PROCESS_NUM_LEVEL1B*PROCESS_CHUNKSIZE_LEVEL1B,version]
    
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
            job_list = map(None, *([iter(result)] * PROCESS_CHUNKSIZE_LEVEL0))
            for grp in job_list:
                jobfile=NamedTemporaryFile(delete=False,mode='w+r+x')
                jobfile.write('''#!{0}\n'''.format(interpreter))
                jobfile.write('''from pg import DB\n''')
                jobfile.write('''from datetime import datetime \n''')
                jobfile.write('''from os.path import basename \n''')
		jobfile.write('''from odincal.config import config\n''')
                jobfile.write('''from odincal.level0 import import_file\n''')
		jobfile.write('''dbname=config.get('database','dbname')\n''')
		jobfile.write('''user=config.get('database','user')\n''')
		jobfile.write('''host=config.get('database','host')\n''')
		jobfile.write('''passwd=config.get('database','passwd')\n''')
                jobfile.write('''class db(DB):\n''')
                jobfile.write('''   def __init__(self):\n''')
                jobfile.write('''      DB.__init__(self,dbname=dbname,user=user,host=host,passwd=passwd)\n''')
                jobfile.write('''con=db()\n''')
                jobfile.write('''filelist=[''')
              
                for row in grp:
                    if not row is None:
                        fullname=get_full_path(row['file'])
                        temp={'file':row['file'],
                              'created': datetime.today()}
                        print row['file'],row['measurement_date']
                        con.insert('level0_files_in_process',temp) 
                        jobfile.write('\'{0}\''.format(fullname)+',')
                jobfile.write(''']\n''')
                jobfile.write('''for file in filelist:\n''')
                jobfile.write('''   print file\n''')
                jobfile.write('''   import_file(file)\n''')
                sqlstring='''\'''delete from level0_files_in_process where file=\'{0}\' \'''.format(basename(file))'''
                jobfile.write('''   con.query({0})\n'''.format(sqlstring))
                jobfile.write('''   temp={\'file\':basename(file),\'created\': datetime.today()}\n''')
                jobfile.write('''   con.insert(\'level0_files_imported\',temp)\n''')
                jobfile.write('''con.close()''')
                
                jobfile.flush()
                jobid = tc.submit(jobfile.name,'odincal',
                           Job_Name='level0_import',
                           Variable_List='PGHOST=malachite',
			   Resource_List=[
                               ('nodes','1:odincal'),
                               ('walltime','7200'),
			       ('mem','1400mb'),
			   ],
                           Error_Path=Error_Path,
                           Output_Path=Output_Path,
                           )
                jobfile.close()
                print jobid
            con.close()
	    exit(0)		
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
            if period['info']=='today':
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
		    if row['ext']=='ac1' or row['ext']=='ac2':
			continue
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
                    #is t1, now subtract 2 days for safety reason
                    t0=t0-timedelta(days=2)
                    ac_period[1]=str(t0.date())
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
           and (processed.total_scans is Null or
		processed.version!={3}) and (
           in_process.created is Null or
           in_process.version!={3})
           order by measurement_date desc limit {2}
           '''.format(*ac_period))
            result=query.dictresult()
            
            if len(result)>0:
               #do level1b_calibration import
                job_list = map(None, 
                               *([iter(result)] * PROCESS_CHUNKSIZE_LEVEL1B))
                for grp in job_list:
                    jobfile=NamedTemporaryFile(delete=False,mode='w+r+x')
                    jobfile.write('''#!{0}\n'''.format(interpreter))
                    jobfile.write('''from subprocess import call\n''')
                    jobfile.write('''binfile=\'{0}\'\n'''.format(binfile))
                    jobfile.write('''version={0}\n'''.format(version))
                    jobfile.write('''filelist=[''')
		    if PROCESS_CHUNKSIZE_LEVEL1B==1:
			temp={
                                  'file'   :grp['file'],
                                  'created':datetime.today(),
                                  'version':version 
                                  }
                  	con.insert('in_process',temp)
                        jobfile.write('\'{0}\''.format(grp['file'])+',')
			print grp['file']
		    else:			
                    	for row in grp:
                        	if not row is None:
                              		temp={
                                  'file'   :row['file'],
                                  'created':datetime.today(),
                                  'version':version 
                                  	}
                              		con.insert('in_process',temp)
                              		jobfile.write('\'{0}\''.format(row['file'])+',')
                              		print row['file']
                    jobfile.write(''']\n''')
                    jobfile.write('''for file in filelist:\n''')
                    jobfile.write('''  call([binfile,file,file[-3::].upper(),'1',str(version)])''')
                    jobfile.flush()
                    jobid = tc.submit(jobfile.name,'odincal',
                                      Job_Name='calibration_import',
                                      Variable_List='PGHOST=malachite',
			              Resource_List=[
                                          ('nodes','1:odincal'),
                                          ('walltime','7200'),
					  ('mem','990mb')
			              ],
                                      Error_Path=Error_Path,
                                      Output_Path=Output_Path,
                                      )
                    jobfile.close()
                    print jobid
                    #submit jobfile to queu
		con.close()
		exit(0)
    con.close()



if __name__=='__main__':
	main()
