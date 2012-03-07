from sys import argv
from os.path import getsize,basename,splitext
if len(argv)==2:
    origfile = argv[1]
    size = getsize(origfile)
    f = open(origfile,'rb')
    g = open('testfile'+splitext(origfile)[1],'wb')

    #find a block at the middle of the file
    f.seek(size/150/2*150)
    #read at least 3 whole data blocks
    for i in range(4):
        x =f.read(150*13)
        g.write(x)
    f.close()
    g.close()



