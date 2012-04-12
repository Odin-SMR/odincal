from oops.level0 import ACfile,FBAfile
from oops import attitude

import ctypes
import numpy
from pg import DB
from sys import argv
from os.path import splitext,basename

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin')


def ac2db():
    if len(argv)>1:
        con = db()
        for datafile in argv[1:]:
            stw_overflow= basename(datafile).startswith('1')
            extension = splitext(datafile)[1]
            if extension == '.ac1' or extension == '.ac2':
                f = ACfile(datafile)
                while 1:
                    try:
                        datadict = getAC(f)
                        if stw_overflow:
                            datadict['stw']+=2**32
                        dbdict = db_prep(datadict,con)
                        con.insert('ac_level0',dbdict)
                    except EOFError:
                        break
def fba2db():
    if len(argv)>1:
        con = db()
        for datafile in argv[1:]:
            stw_overflow= basename(datafile).startswith('1')
            extension = splitext(datafile)[1]
            if extension == '.fba':
                f = FBAfile(datafile)
                while 1:
                    try:
                        datadict = getFBA(f)
                        if stw_overflow:
                            datadict['stw']+=2**32
                        con.insert('fba_level0',datadict)
                    except EOFError:
                        break
def att2db():
    if len(argv)>1:
        con = db()
        for datafile in argv[1:]:
            extension = splitext(datafile)[1]
            if extension == '.att':
                datalist=getATT(datafile)
                for datadict in datalist:
                    con.insert('attitude_level0',datadict)

def db_prep(datadict,db):
    dbdict = dict(datadict)
    dbdict['acd_mon'] = db.escape_bytea(datadict['acd_mon'])
    dbdict['cc']  = db.escape_bytea(datadict['cc'])
    return dbdict

def getAC(ac):
    """AC factory.
    reads a fileobject and creates a dictionary for easy insertation
    into a postgresdatabase. Uses Ohlbergs routines to read the files (ACfile)
    """
    backend = {
        0x7380 : 'AC1',
        0x73b0 : 'AC2',
    }
    CLOCKFREQ= 224.0e6
    head = ac.getSpectrumHead()
    while head is not None:
        data = []
        stw = ac.stw
        back = backend[ac.user]
        for j in range(12):
            data.append(ac.getBlock())
            if data[j]==[]:
                raise(EOFError('File ended.'))
        cc=numpy.array(data,dtype='int16')
        cc.shape = (8,96)
        cc64 = numpy.array(cc,dtype='int64')
        lags = numpy.array(head[50:58],dtype='uint16')
        lags64 = numpy.array(lags,dtype='int64')
        #combine lags and data to ensure validity of first value in cc-channels
        zlags = numpy.left_shift(lags64,4)  + numpy.bitwise_and(cc64[:,0],0xf)
        zlags.shape=(8,1)
        cc64[:,0]=zlags[:,0]
        #find potential underflow in third element of cc
        mask = cc64[:,2]>0
        cc64[mask,2]-=65536
        #scale
        cc64 = cc64*2048.0*(1/ac.IntTime(head))/(CLOCKFREQ/2.0)
        mon = numpy.array(head[16:32],dtype='uint16')
        mon.shape=(8,2)
        #find potential overflows/underflows in monitor values
        mon64 = numpy.bitwise_and(zlags,0xf0000) + mon
        overflow_mask = numpy.abs(mon64-zlags)>0x8000
        mon64[overflow_mask & (mon64>zlags)]-=0x10000
        mon64[overflow_mask & (mon64<zlags)] +=0x10000
        #scale
        mon64 = mon64 * 1024.0*(1/ac.IntTime(head))/(CLOCKFREQ/2.0)
        prescaler = head[49]
        datadict = {
            'stw': stw,
            'backend': back,
            'frontend': ac.Frontend(head),
            'sig_type':ac.Type(head),
            'ssb_att': "{{{},{},{},{}}}".format(*ac.Attenuation(head)),
            'ssb_fq':"{{{},{},{},{}}}".format(*ac.SSBfrequency(head)),
            'prescaler': prescaler,
            'inttime': ac.IntTime(head),
            'mode':ac.Mode(head),
            'acd_mon': mon64,
            'cc': cc64,
        }
        return datadict
    raise(EOFError('File ended.'))

def getFBA(fba):
    """AC factory.
    reads a fileobject and creates a dictionary for easy insertation
    into a postgresdatabase. Uses Ohlbergs routines to read the files (ACfile)
    """
    word = fba.getSpectrumHead()
    while word is not None:
        stw = fba.stw
        mech = fba.Type(word)
        datadict = {
            'stw': stw,
            'mech_type': mech,
        }
        return datadict
    raise(EOFError('File ended.'))

def getATT(file):
	"""use Ohlbergs code to read in attitude data from file
        and creates a dictionary for easy insertation
        into a postgresdatabase.
        """
	ap=attitude.AttitudeParser([file])
	# sorting attitudes
	tbl = ap.table
	keys = tbl.keys()
	if not keys:
                return
	keys.sort()
	key0 = keys[0]
	for key1 in keys[1:]:
		stw0 = tbl[key0][6]
                stw1 = tbl[key1][6]
                if stw1-stw0 < 17:
                    qe0 = tbl[key0][10]
                    qe1 = tbl[key1][10]
                    if qe0 != qe1:
                        err0 = qe0[0]*qe0[0] + qe0[1]*qe0[1] + qe0[2]*qe0[2]
                        err1 = qe1[0]*qe1[0] + qe1[1]*qe1[1] + qe1[2]*qe1[2]
                        #print "errors:", err0, err1
                        if err1 < err0:
                            del tbl[key0]
                            key0 = key1
                        else:
                            del tbl[key1]
                else:
                    key0 = key1
        
        datalist=[]
	for key in keys:
            (year,mon,day,hour,minute,
	     secs,stw,orbit,qt,qa,qe,gps,acs) = ap.table[key]
            datadict={
                'year'     :year,
                'mon'      :mon,			
                'day'      :day,
                'hour'     :hour,
                'min'      :minute,
                'secs'     :secs,
                'stw'      :stw,
                'orbit'    :orbit,
                'qt'       :"{{{},{},{},{}}}".format(*qt),
                'qa'       :"{{{},{},{},{}}}".format(*qa),
                'qe'       :"{{{},{},{}}}".format(*qe),
                'gps'      :"{{{},{},{},{},{},{}}}".format(*gps),
                'acs'      :acs,
                }
            datalist.append(datadict)
        return datalist
