from oops import odin
import numpy
from pg import DB

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin')

def Lookup(table,stw0):
    i = 0
    while i < len(table[0])-1 and table[0][i+1] < stw0:
        i = i+1
    return table[1][i]

def shk_level1_importer():
    con =db()
    query=con.query('''select stw,backend,frontend from ac_level0
                       natural left join shk_level1 
                       where LO is NULL
                       order by stw''')
    sigresult=query.dictresult()
    for sig in sigresult:
        shkdict={
            'stw'        :sig['stw'],
            'backend'    :sig['backend'],
            'lo'         :[],
            'ssb'        :[],
            'mixc'       :[],
            'imageloadb' :[],
            'hotloada'   :[],
            'hotloadb'   :[],
            }
        shklist=['LO','SSB','mixC','imageloadB','hotloadA','hotloadB']
        insert=1
        for shk in shklist:
            if shk=='LO' or shk=='SSB' or shk=='mixC':
                sel=[shk+sig['frontend'],sig['stw']]
            else:
                sel=[shk,sig['stw']]
            query=con.query('''select stw,shk_value from shk_level0
                               where shk_type='{0}' and
                               stw>{1}-2080 and stw<{1}+2080
                               order by stw'''.format(*sel[:]))
            result=query.getresult()
            if len(result)<2:
                insert=0
                break    
            stw=[]
            data=[]
            for row in result:
                stw.append(row[0])
                data.append(row[1])
            table=(stw,data)
            data0=Lookup(table,sig['stw'])
            shkdict[shk.lower()]=float(data0)
        if insert==1:
            con.insert('shk_level1',shkdict)
            query=con.query('''select LO from shk_level1''') 
            res=query.getresult()
