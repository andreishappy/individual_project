from threading import *
import subprocess 
import time

class InserterThread(Thread):
    def __init__(self, input_list):
        super(InserterThread,self).__init__()
        self.input_list = input_list
        print "Called thread __init__"

    def run(self):
        for link in self.input_list:
            #print "Inserting link {0} <==> {1}".format(link[0],link[1])
            self.insert_link(link[0],link[1])
            self.insert_link(link[1],link[0])

        #print "Thread Done inserting"

    def insert_link(self,node1,node2):
        success = False
        while not success:
            process = subprocess.Popen('tuple insert andrei {0} add_neighbour to_add={1}'\
                                           .format(node1,node2),shell=True,\
                                           stdout=subprocess.PIPE,\
                                           stderr=subprocess.PIPE,\
                                           executable = '/bin/bash')
            out,err = process.communicate()
            out = str.splitlines(out)
            for line in out:
                        #print line
                if 'Tuples sent' in line:
                    success = True
                elif 'Target application not found in registry.' in line:
                    print line
                    exit(0)
            if not success:
                    time.sleep(2)      
        #print "Link {0} ==> {1} added".format(node1,node2)
