from threading import *
import subprocess

class LinkInserter(Thread):
    def __init__(self, link):
        Thread.__init__(self)
        self.insert = link

    def run(self):
        cmd = 'tuple insert andrei {0} add_neighbour to_add={1}'\
               .format(self.insert[0],self.insert[1])

        success = False
        while not success:
            p = subprocess.Popen(cmd, shell=True,
                                 stderr=subprocess.PIPE,\
                                 stdout=subprocess.PIPE,\
                                 executable = '/bin/bash')

            stdout = p.communicate()[0]
            
            stdout = stdout.splitlines()
            for line in stdout:
                if 'Tuples sent' in line:
                    print "LINK INSERTED: {0}".format(self.insert)
                    success = True
                    continue
                if 'Tuples NOT sent' in line:
                    print "LINK FAILED: {0}".format(self.insert)
                    continue
                             

                          
