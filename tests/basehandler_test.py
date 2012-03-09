import unittest
import numpy
import ctypes
import pg
from odincal.basehandler import BaseHandler

class Test(ctypes.Structure):
    _fields_ = [
        ('field1',ctypes.c_int),
        ('field2',ctypes.c_ushort),
        ('vector1',(ctypes.c_ushort*4)),
    ]
class BaseHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.test = Test()

    def test_create_simple(self):
        bh = BaseHandler(['field1'])
        bh.data_fields = self.test
        correct = 'create table Test (field1 integer,field2 integer,vector1 bytea,constraint pk_Test primary key (field1))'
        self.assertEqual(bh.create_statement(),correct)

    def test_create_extra(self):
        bh = BaseHandler(['field1'])
        bh.data_fields = self.test
        bh.extra_data_field = 'data'
        bh.data = numpy.ones(2,dtype='int8')
        correct = 'create table Test (field1 integer,field2 integer,vector1 bytea,data bytea,constraint pk_Test primary key (field1))'
        self.assertEqual(bh.create_statement(),correct)

    def test_create_insert(self):
        bh = BaseHandler(['field1'])
        bh.data_fields = self.test
        bh.extra_data_field = 'data'
        bh.data = numpy.ones(2,dtype='int8')
        con = pg.connect('odin')
        con.query(bh.create_statement(temporary=True))
        con.query(bh.insert_statement())
        q =con.query('select * from Test')
        res = q.dictresult()
        self.assertEqual(res[0]['field1'],0)
        self.assertEqual(pg.unescape_bytea(res[0]['data']),bh.data.tostring())


if __name__=='__main__':
    unittest.main()

