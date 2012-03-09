import unittest
from odincal.data_structures import AC,ACData,HK
from ctypes import sizeof
class DatatypesTestCase(unittest.TestCase):
    def test_lenACD(self):
        self.assertEqual(sizeof(AC),150)
    def test_lenSHKD(self):
        self.assertEqual(sizeof(HK),150)
    def test_lenACH(self):
        self.assertEqual(sizeof(ACData),150)

if __name__=='__main__':
    unittest.main()

