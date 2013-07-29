import subprocess
import string

if __name__ == "__main__":
    to_insert = {'a':['b'], 'b':['c'], 'c': ['d','e']}
    for node in to_insert:
        for neighbour in to_insert[node]:
            success = False
            while not success:
                process = subprocess.Popen('tuple insert andrei {0} add_neighbour to_add={1}'\
                                           .format(node,neighbour),shell=True,stdout=subprocess.PIPE,\
                                               executable = '/bin/bash')
                out,err = process.communicate()
                out = str.splitlines(out)
                for line in out:
                    if 'Tuples sent' in line:
                        success = True
                        print "Neighbour {0} added to node {1}".format(neighbour,node)

            
 
