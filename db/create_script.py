import pg

create_statement = """
create table ac (
   stw int not null,
   backend int not null,
   counter int,
   chopper_pos int,
   int_time int,
   acd_monitor bytea,
   mask2 int,
   mask3 int,
   mask4 int,
   mask5 int,
   mask6 int,
   inttime int,
   ccmxset int,
   switch int,
   sim int,
   mxm int,
   ssb1_att int,
   ssb2_att int,
   ssb3_att int,
   ssb4_att int,
   ssb1_fq int,
   ssb2_fq int,
   ssb3_fq int,
   ssb4_fq int,
   useraddress int,
   r int,
   s int,
   prescaler int,
   lags bytea,
   tail int,
   cc bytea,
   primary key (stw,backend)
)
"""
if __name__=='__main__':
   con = pg.connect('odin')
   con.query(create_statement)



   
