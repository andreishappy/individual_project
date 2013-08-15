import subprocess,os
import fcntl
import time

cmd = 'tuple insert andrei a add_neighbour to_add=1'

p = subprocess.Popen(cmd, shell=True,
                     executable = '/bin/bash')

stdout = p.communicate()[0]

stdout = stdout.splitlines()

for line in stdout:
    print line
    

    
