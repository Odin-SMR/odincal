import unittest

import pg
import numpy
import ctypes
from pkg_resources import resource_filename

from odincal.data_structures import AC,ACData,HK
from odincal.datahandlers import getAC,getHK,ACHandler,HKHandler


class ACTestCase(unittest.TestCase):
    '''Reading and writing AC - data'''
    def setUp(self):
        self.con = pg.connect('odin')

    def test_ac1(self):
        '''Reading ac1.
        inserting to database
        '''
        ac = AC()
        data = numpy.zeros((2,2),'int16')
        ach = ACHandler(ac,data)
        createtest = ach.create_statement(temporary=True)
        self.con.query(createtest)
        f = open(resource_filename('tests','testfile.ac1'))
        while 1:
            try:
                ac = getAC(f)
            except EOFError:
                break
            inserttest = ac.insert_statement()
            self.con.query(inserttest)
        q = self.con.query('select count(*) from AC')
        res  = q.getresult()
        self.assertEqual(res[0][0],3)

    def test_ac2(self):
        '''Reading ac2.
        inserting to database
        '''
        ac = AC()
        data = numpy.zeros((2,2),'int16')
        ach = ACHandler(ac,data)
        createtest = ach.create_statement(temporary=True)
        self.con.query(createtest)
        f = open(resource_filename('tests','testfile.ac2'))
        while 1:
            try:
                ac = getAC(f)
            except EOFError:
                break
            inserttest = ac.insert_statement()
            self.con.query(inserttest)
        q = self.con.query('select count(*) from AC')
        res  = q.getresult()
        self.assertEqual(res[0][0],3)

    def test_shk(self):
        '''Reading shk.
        inserting to database
        '''
        hk = HK()
        hkh = HKHandler(hk)
        createtest = hkh.create_statement(temporary=True)
        self.con.query(createtest)
        f = open(resource_filename('tests','testfile.shk'))
        while 1:
            try:
                hk = getHK(f)
            except EOFError:
                break
            inserttest = hk.insert_statement()
            self.con.query(inserttest)
        q = self.con.query('select count(*) from HK')
        res  = q.getresult()
        self.assertEqual(res[0][0],52)

    def test_bogus_ac(self):
        '''Reading a bogus file as ac.
        not containing data
        '''
        f = open(resource_filename('tests','testfile.bogus'))
        self.assertRaises(EOFError,getAC,f)

    def test_bogus_hk(self):
        '''Reading a bogus file as hk.
        not containing data
        '''
        f = open(resource_filename('tests','testfile.bogus'))
        self.assertRaises(EOFError,getHK,f)

if __name__=='__main__':
    unittest.main()
    


