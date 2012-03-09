import pg
from ctypes import Array
from odincal.ac import ACHandler,HKHandler
from odincal.data_structures import AC,HK


if __name__=='__main__':
   con = pg.connect('odin')
   ac = ACHandler(AC(),None)
   hk = HKHandler(HK())
   con.query(ac.create_statement())
   con.query(hk.create_statement())
   con.close()
