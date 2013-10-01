import os
import subprocess
import time
import tempfile
import sys
import StringIO

class ShellLauncher(object):
    def submit(self, *args, **kwargs):
        name = kwargs['Job_Name']
        outfile = kwargs['Output_Path']
        errfile = kwargs['Error_Path']
        newpid = os.fork()
        if newpid == 0:
            #this is the child process that now runs in the backgroud
            er = file('{2}/{1}_{0}.er'.format(os.getpid(),name,errfile),'w')
            ou = file('{2}/{1}_{0}.ou'.format(os.getpid(),name,outfile),'w')
            a=subprocess.Popen('/home/bengt/work/odincal_2013/odincal_outputfiles/odincal/bin/odinpy '+args[0],shell=True,stdout=ou,stderr=er)
            a.wait()
            er.close()
            ou.close()
            sys.exit(0)
            #child is dead
        else:
            #returns the pid of the child
            return newpid

if __name__=='__main__':
#Example
    tc = ShellLauncher()
    #start two processings at the same time
    for i in range(2):
        # create the batch script
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmpfile.write('sleep 10\necho "hello wold"\n')
        tmpfile.flush()
        tmpfile.close()
        #send the job, same syntax as with Torque.
        jobid = tc.submit(tmpfile.name,'gosat',
                          Job_Name='preprocess',
                          Variable_List='PGHOST=smiles-p12',
                          Error_Path='./',
                          Output_Path='./',
                         )


