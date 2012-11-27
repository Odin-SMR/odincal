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
                       where imageloadb is NULL 
                       order by stw''')
    sigresult=query.dictresult()
    for sig in sigresult: 
        #For the split modes and the currently accepted
        #frontend configurations, AC1 will hold REC_495 data in its lower half
        #and REC_549 in its upper half. AC2 will hold REC_572 data in its
        #lower half and REC_555 in its upper half.
        if sig['frontend']=='SPL':
            if sig['backend']=='AC1':
                frontends=['495','549']
            if sig['backend']=='AC2':
                frontends=['572','555']
        else:
            frontends=[sig['frontend']]
        for ind,frontend in enumerate(frontends):
            shkdict={
                    'stw'           :sig['stw'],
                    'backend'       :sig['backend'],
                    'frontendsplit' :frontend,
                    'lo'            :[],
                    'ssb'           :[],
                    'mixc'          :[],
                    'imageloada'    :[],
                    'imageloadb'    :[],
                    'hotloada'      :[], 
                    'hotloadb'      :[],
                    'mixera'        :[],
                    'mixerb'        :[],
                    'lnaa'          :[],
                    'lnab'          :[],
                    'mixer119a'     :[],
                    'mixer119b'     :[],
                    'warmifa'       :[],
                    'warmifb'       :[],
                    }
            shklist=['LO','SSB','mixC','imageloadB','imageloadA','imageloadB',
                     'hotloadA','hotloadB','mixerA','mixerB','lnaA','lnaB',
                     '119mixerA','119mixerB','warmifA','warmifB']
            if frontend=='119':
                shklist=['imageloadA','imageloadB','hotloadA','hotloadB',
                        'mixerA','mixerB','lnaA','lnaB',
                        '119mixerA','119mixerB','warmifA','warmifB']
            insert=1

            for shk in shklist:
                if shk=='LO' or shk=='SSB' or shk=='mixC':
                    sel=[shk+frontend,sig['stw']]
                else:
                    sel=[shk,sig['stw']]
                query=con.query('''select stw,shk_value from shk_level0n
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
                if shk=='119mixerA':
                    shkdict['mixer119a']=float(data0)
                elif shk=='119mixerB':
                    shkdict['mixer119b']=float(data0)
                else:
                    shkdict[shk.lower()]=float(data0)
            if insert==1:
                con.insert('shk_level1',shkdict)
            #query=con.query('''select LO from shk_level1''') 
            #res=query.getresult()
