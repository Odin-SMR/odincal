import unittest

import pg
from pkg_resources import resource_filename

from odincal.data_structures import Header,Data
from odincal.ac import getAC
from db.create_script import create_statement


class ACTestCase(unittest.TestCase):
    '''Reading and writing AC - data'''
    def setUp(self):
        self.con = pg.connect('odin')
        createst = create_statement.replace('create table', 
                                            'create temporary table')
        self.con.query(createst)

    def test_ac1(self):
        '''Reading ac1.
        inserting to database
        '''
        f = open(resource_filename('tests','testfile.ac1'))
        while 1:
            try:
                ac = getAC(f)
            except EOFError:
                break
            ac.write_to_db(self.con)
        q = self.con.query('select count(*) from ac')
        res  = q.getresult()
        self.assertEqual(res[0][0],3)

    def test_ac2(self):
        '''Reading ac2.
        inserting to database
        '''
        f = open(resource_filename('tests','testfile.ac2'))
        while 1:
            try:
                ac = getAC(f)
            except EOFError:
                break
            ac.write_to_db(self.con)
        q = self.con.query('select count(*) from ac')
        res  = q.getresult()
        self.assertEqual(res[0][0],3)

    def test_ac(self):
        '''Reading ac1 and ac2.
        inserting to database
        '''
        f1 = open(resource_filename('tests','testfile.ac1'))
        f2 = open(resource_filename('tests','testfile.ac2'))
        while 1:
            try:
                ac = getAC(f1)
            except EOFError:
                break
            ac.write_to_db(self.con)
        while 1:
            try:
                ac = getAC(f2)
            except EOFError:
                break
            ac.write_to_db(self.con)
        q = self.con.query('select count(*) from ac')
        res  = q.getresult()
        self.assertEqual(res[0][0],6)

    def test_bogus(self):
        '''Reading a bogus file.
        not containing data
        '''
        f = open(resource_filename('tests','testfile.bogus'))
        self.assertRaises(EOFError,getAC,f)

if __name__=='__main__':
    unittest.main()


