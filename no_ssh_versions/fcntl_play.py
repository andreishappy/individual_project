import fcntl
import subprocess, os
import time

cmd = "dsmengine -namespace andrei -instance a BGP_v2.dsmr"
p = subprocess.Popen(cmd, shell=True,\
                     stdout=subprocess.PIPE,\
                     stderr=subprocess.PIPE,\
                     executable = '/bin/bash')

fcntl.fcntl(p.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
fcntl.fcntl(p.stderr.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
while True:
    
    try:
        out = p.stdout.readline()

        #print "one read===================\n {0}".format(out)
        if 'started' in out:
            print "STDOUT =======\n" + err
    except IOError:
        pass

    try:
        err = p.stderr.readline()
        print "STDERR ===========\n" + err
        if 'started' in err:
            print "STARTED ERR"
        #print "one read err==================\n {0}".format(err)
    except IOError:
        pass
