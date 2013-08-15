from xml_tool import MyXMLParser
import subprocess
from optparse import OptionParser
import sys
import time
from lamport_transformation import *
from lxml.etree import *
from result_to_xml import *
from Starter import *
from Watcher import Watcher,WatcherMonitor
from Inserter import LinkInserter
import fcntl
import os
import string
from result_to_xml import *
from lxml.etree import *

class Simulator:

    def __init__(self,config_file):
        self.config = MyXMLParser(config_file)
        #List of all the instances to start
        self.nodes = self.config.nodes
        self.limit = self.config.limit
        self.rule = self.config.rule
        
        #List of tables by type
        self.tran_table_dict = get_table_dict(self.rule,'transport')
        self.persistent_table_dict = get_table_dict(self.rule,'persistent')

        #List of (node1,node2) tuples representing
        #bidirectional links
        self.links = self.config.topology

        '''List of dict of 2 types of input:
             1: {'values': 'n001n002;3', 'instance': 'n001', 
                 'var_names': 'path;score', 'table_name': 'policy', 
                 'type': 'normal'}
                 
             2:{'csv_file': 'csv_attempt', 'instance': 'n001', 
                'table_name': 'policy', 'type': 'csv'}
             '''
        self.pre_inputs = self.config.pre_inputs
        self.post_inputs = self.config.post_inputs
        #string

        #COULD get list of table_names

        self.process_dict = {}
        self.lock = Lock()

        #For centralised version
        self.started = 0
        self.err_buffer = {}
        self.out_buffer = {}
        for instance in self.nodes:
            self.out_buffer[instance] = ''
            self.err_buffer[instance] = ''

    #|================================================|
    #|<><> MAIN FUNCTION CONTROLS THE SIMULATION ><><>|
    #|================================================|
    def run_simulation(self):
        start_time = time.time()
        self.start_nodes()
        start_time = time.time() - start_time
        print 'Starting network with {0} nodes took: {1} secods'\
              .format(len(self.nodes),start_time)
  
        watcher_monitor = WatcherMonitor(self.limit)
        #Launch a thread which watches the output of the engines
        watcher_thread = Watcher(self.process_dict,self.config,watcher_monitor,self.persistent_table_dict)
        watcher_thread.start()
        
        #Do pre inputs
        self.insert_list(self.pre_inputs)
       
        #Set the topology
        self.set_topology()

        #Do post inputs
        self.insert_list(self.post_inputs)

        time.sleep(2)
        while not watcher_monitor.converged() and\
              not watcher_monitor.hit_limit():
            pass

        if watcher_monitor.hit_limit():
            print "HIT LIMIT"
        else:
            print "CONVERGENCE REACHED"
               
        self.node_states = watcher_thread.stop()
        lamport_transformation(self.node_states)

        f = open('output','w')
        for node in self.node_states:
            f.write("Instance {0} states".format(node))
            f.write("================================")
            for state in self.node_states[node]:
                f.write(state.__str__())
        f.close()

        self.make_xml()
        f = open('output.xml','w')
        f.write(self.result)
        f.close()


    #==== HELPER FUNCTIONS FOR SIMULATION ====
    #=========================================
    def start_nodes(self):
        for instance in self.nodes:
            cmd = 'dsmengine -namespace andrei -instance {0} {1}'\
                   .format(instance,self.rule)
                   

            #print "Calling command {0}".format(cmd)
            with self.lock:
                self.process_dict[instance] = subprocess.Popen(cmd, shell=True,\
                                              stdout=subprocess.PIPE,\
                                              stderr=subprocess.PIPE,\
                                              executable = '/bin/bash')

            #Set the stdout and stderr streams not to block
            fcntl.fcntl(self.process_dict[instance].stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            fcntl.fcntl(self.process_dict[instance].stderr.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

        
    
        to_analyse = ''
        while self.started != len(self.nodes):
            for instance in self.nodes:
                try:
                    l = self.process_dict[instance].stderr.readline()
                    if 'DSMEngine engine started'.format(instance) in l:
                        print l
                        self.started += 1
                        
                    if 'exiting' in l:
                        print "BUG IS BACK!!!!!!!!!!!!!",l
                
                except IOError:
                    pass
    

    #PARALLEL TOPOLOGY - NETWORK OVERLOADS -> MESSAGES LOST
    '''
    def set_topology(self):
        inserters = []
        for link in self.links:
            to_insert = [(link[0],link[1]),(link[1],link[0])]
            for insert in to_insert:
                print "Doing insert of {0}".format(insert)
                inserter = LinkInserter(insert)
                inserters.append(inserter)
                inserter.start()
                
        
        for inserter in inserters:
            inserter.join()
            ''' 

    def insert_list(self,lis):
        for inp in lis:
            if inp['type'] == 'csv':
                self.csv_insert(inp)
            elif inp['type'] == 'normal':
                self.normal_insert(inp)
            else:
                print "Wrong type of input {0}".format(inp)

    def normal_insert(self,inp):
        table_name = inp['table_name']
        var_names = string.split(inp['var_names'],';')
        values = string.split(inp['values'],';')
        instance = inp['instance']
        
        cmd = 'tuple insert andrei {0} {1} '.format(instance,table_name)

        if len(values) != len(var_names):
            print "Input value and var_name lengths don't match: {0}"\
                   .format(inp)

        for i in range(0,len(values)):
            cmd += "{0}={1} ".format(var_names[i],values[i])
            
        self.tuple_insert(cmd)

    def csv_insert(self,inp):
        cmd = "tuple insert andrei {0} {1} {2}"\
               .format(inp['instance'],\
                       inp['table_name'],\
                       inp['csv_file'])

        self.tuple_insert(cmd)

    def tuple_insert(self,cmd):
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
                    print "SUCCESS: {0}".format(cmd)
                    success = True
                    continue
                if 'Tuples NOT sent' in line:
                    print 'FAIL: {0}'.format(cmd)
                    continue
       
    #SEQUETIAL TOPOLOGY - WORKS
    def set_topology(self):
        for link in self.links:
            to_insert = [(link[0],link[1]),(link[1],link[0])]
            for insert in to_insert:
                
                cmd = 'tuple insert andrei {0} add_neighbour to_add={1}'\
                    .format(insert[0],insert[1])
                print 'Calling {0}'.format(cmd)
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
                           print "LINK INSERTED: {0}".format(insert)
                           success = True
                           continue
                        if 'Tuples NOT sent' in line:
                           print "LINK FAILED: {0}".format(insert)
                           continue
    

    def make_xml(self):
        result = Element('result')
        #Get info about the declarations at the start
        messages_elem = do_declarations(self.tran_table_dict,'messages')
        tables_elem = do_declarations(self.persistent_table_dict,'tables')

        result.append(messages_elem)
        result.append(tables_elem)
        
        states_elem = do_states(self.node_states)
        result.append(states_elem)
        self.result = tostring(result, xml_declaration=True, pretty_print=True)

if __name__ == "__main__":
    parser = OptionParser()
    '''MAYBE LATER
    parser.add_option("-c", "--config", dest="config",\
                     help="xml file to load configuration")
    '''                 

    (options,args) = parser.parse_args()
    if len(args) != 1:
        print "Need to supply config file"
        exit(-1)
    
    config = args[0]
    simulator = Simulator(config)
    
    simulator.run_simulation()
