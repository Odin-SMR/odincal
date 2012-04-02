import unittest

import pg
import numpy
import ctypes
from pkg_resources import resource_filename

#from odincal.data_structures import AC,ACData,HK
from oops.level0 import ACfile
from odincal.level0 import getAC,db_prep#,getHK,ACHandler,HKHandler

class dbtest(pg.DB):
    def __init__(self):
        pg.DB.__init__(self,dbname='odin')

class ACTestCase(unittest.TestCase):
    '''Reading and writing AC - data'''
    def setUp(self):
        self.db = dbtest()

#    def Xtest_ac1(self):
#        '''Reading ac1.
#        inserting to database
#        '''
#        ac = AC()
#        data = numpy.zeros((2,2),'int16')
#        ach = ACHandler(ac,data)
#        createtest = ach.create_statement(temporary=True)
#        self.con.query(createtest)
#        f = open(resource_filename('tests','testfile.ac1'))
#        while 1:
#            try:
#                ac = getAC(f)
#            except EOFError:
#                break
#            inserttest = ac.insert_statement()
#            self.con.query(inserttest)
#        q = self.con.query('select count(*) from AC')
#        res  = q.getresult()
#        self.assertEqual(res[0][0],3)
#
#    def Xtest_ac2(self):
#        '''Reading ac2.
#        inserting to database
#        '''
#        ac = AC()
#        data = numpy.zeros((2,2),'int16')
#        ach = ACHandler(ac,data)
#        createtest = ach.create_statement(temporary=True)
#        self.con.query(createtest)
#        f = open(resource_filename('tests','testfile.ac2'))
#        while 1:
#            try:
#                ac = getAC(f)
#            except EOFError:
#                break
#            inserttest = ac.insert_statement()
#            self.con.query(inserttest)
#        q = self.con.query('select count(*) from AC')
#        res  = q.getresult()
#        self.assertEqual(res[0][0],3)
#
#    def Xtest_shk(self):
#        '''Reading shk.
#        inserting to database
#        '''
#        hk = HK()
#        hkh = HKHandler(hk)
#        createtest = hkh.create_statement(temporary=True)
#        self.con.query(createtest)
#        f = open(resource_filename('tests','testfile.shk'))
#        while 1:
#            try:
#                hk = getHK(f)
#            except EOFError:
#                break
#            inserttest = hk.insert_statement()
#            self.con.query(inserttest)
#        q = self.con.query('select count(*) from HK')
#        res  = q.getresult()
#        self.assertEqual(res[0][0],52)
#
    def test_ac1(self):
        '''Reading ac1file
        '''
        #filename = '/home/joakim/Downloads/149a04f1.ac1'
        filename = resource_filename('tests','testfile.ac1')
        ac = ACfile(filename)
        cnt = 0
        while 1:
            try:
                ccdata = getAC(ac)
                cnt+=1
            except EOFError:
                break
        self.assertEqual(cnt,3)

    def test2_ac1(self):
        '''Reading ac1file
        '''
        con  = self.db.query('''
        create temporary table ac_level0(
               stw bigint,
               backend backend,
               frontend frontend,
               sig_type signal_type,
               ssb_att int[4],
               ssb_fq int[4],
               prescaler int,
               inttime real,
               mode int,
               acd_mon bytea,
               cc bytea,
               constraint pk_ac_data primary key (backend,stw)
        )''')

        #filename = '/home/joakim/Downloads/149a04f1.ac1'
        filename = resource_filename('tests','testfile.ac1')
        ac = ACfile(filename)
        cnt = 0
        while 1:
            try:
                data = getAC(ac)
                datadb = db_prep(data,self.db)

                self.db.insert('ac_level0',datadb)
            except EOFError:
                break
        q=self.db.query('select count(*) from ac_level0')
        self.assertEqual(q.getresult()[0][0],3)



    def test_bogus(self):
        '''Reading a bogus file.
        not containing data
        '''
        filename = resource_filename('tests','testfile.bogus')
        self.assertRaises(TypeError,ACfile,filename)

#    def Xtest_bogus_hk(self):
#        '''Reading a bogus file as hk.
#        not containing data
#        '''
#        f = ACfile(resource_filename('tests','testfile.bogus'))
#        self.assertRaises(EOFError,getHK,f)

if __name__=='__main__':
    unittest.main()
    


