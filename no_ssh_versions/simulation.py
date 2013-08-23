from xml_tool import MyXMLParser
import subprocess
from optparse import OptionParser
import sys,os
import time
from lamport_transformation import *
from lxml.etree import *
from result_to_xml import *
from Starter import *
from Watcher import Watcher,WatcherMonitor
from Inserter import Inserter
import fcntl
import os
import string

class Simulator:

    def __init__(self,config_file, output):
        #The file to which the output should be written
        self.output = output

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
        self.topology = self.config.topology

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
        
        #Do pre inputs in parallel
        self.input_pre()
       
        #Set the topology
        self.set_topology()

        self.start_evaluations()

        #Do post inputs
        self.input_post()

        time.sleep(2) #MAY NOT be necessary
        while not watcher_monitor.converged() and\
              not watcher_monitor.hit_limit():
            pass

        if watcher_monitor.hit_limit():
            print "HIT LIMIT"
        else:
            print "CONVERGENCE REACHED"
               
        self.node_states = watcher_thread.stop()
        self.lost_list, self.nr_received, self.nr_sent = lamport_transformation(self.node_states)

        f = open('output','w')
        for node in self.node_states:
            f.write("Instance {0} states".format(node))
            f.write("================================")
            for state in self.node_states[node]:
                f.write(state.__str__())
        f.close()

        self.make_xml()
        f = open(self.output,'w')
        f.write(self.result)
        f.close()


    #==== HELPER FUNCTIONS FOR SIMULATION ====
    #=========================================
    def start_nodes(self):
        print "Starting Engines"
        for ins in self.nodes:
            instance = ins[0]
            rule = ins[1]
            cmd = 'dsmengine -namespace andrei -instance {0} {1}'\
                   .format(instance,rule)
                   

            #print "Calling command {0}".format(cmd)
            self.process_dict[instance] = subprocess.Popen(cmd, shell=True,\
                                              stdout=subprocess.PIPE,\
                                              stderr=subprocess.PIPE,\
                                              executable = '/bin/bash')

            #Set the stdout and stderr streams not to block
            #fcntl.fcntl(self.process_dict[instance].stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            fcntl.fcntl(self.process_dict[instance].stderr.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

        
    
        to_analyse = ''
        while self.started != len(self.nodes):
            for ins in self.nodes:
                instance = ins[0]
                try:
                    l = self.process_dict[instance].stderr.readline()

                    if 'DSMEngine engine started'.format(instance) in l:
                        self.started += 1
                        
                    if 'exiting' in l:
                        print "BUG IS BACK!!!!!!!!!!!!!",l
                
                except IOError:
                    pass
    
    def start_evaluations(self):
        print "DOING: Inserting the start tuples"
        inserters = []
        for ins in self.nodes:
            instance = ins[0]
            cmd = 'tuple insert andrei {0} start dummy=1'.format(instance)
            ins = Inserter(cmd)
            ins.start()
            
        for inserter in inserters:
            inserter.join()
        print "DONE: Inserting the start tuples"

    def input_pre(self):
        print "DOING: inputs before topology"
        inserters = []
        for inp in self.pre_inputs:
            #Create the csv file
            f = open('csv{0}'.format(inp['instance']),'w')
            f.write(inp['var_names'] + '\n')
            for row in inp['rows']:
                f.write(row + '\n')
            f.close()
            
            cmd = 'tuple insert andrei {0} {1} csv{2}'\
                  .format(inp['instance'],inp['table_name'],inp['instance'])

            ins = Inserter(cmd)
            ins.start()
            inserters.append(ins)

        for ins in inserters:
            ins.join()

        for inp in self.pre_inputs:
        #Delete the file
            os.remove('csv{0}'.format(inp['instance']))

        print "DONE: Inputs before topology"

    #PARALLEL TOPOLOGY - NETWORK OVERLOADS -> MESSAGES LOST
    def set_topology_parallel(self):
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
            
    
    def input_post(self):
        print "DOING: Post Inputs"
        for inp in self.post_inputs:
            if inp["type"] == "sever_link":
                table_name = "delete_neighbour"
                var_name = "to_delete"
            elif inp['type'] == "repair_link":
                table_name = "add_neighbour"
                var_name = "to_add"
            elif inp['type'] == 'start':
                table_name = 'start'
                var_name = 'dummy'

                cmd = 'tuple insert andrei {0} {1} {2}=1'\
                      .format(inp['node'],table_name,var_name)
                self.tuple_insert(cmd)

            else:
                sys.stderr.write("Wrong type of post_input: {0}"\
                                 .format(inp['type']))
                exit(-1)
            
            #Do dynamic topology - not used at the MO
            inserters = []
            if inp['type'] in ['sever_link','repair_link']:
                nodes = string.split(inp['link'],';')
                time.sleep(int(inp['delay']))
                for insert in [(nodes[0],nodes[1]),(nodes[1],nodes[0])]:
                    cmd = "tuple insert andrei {0} {1} {2}={3}"\
                        .format(insert[0],table_name,var_name,insert[1])
                    inserter = Inserter(cmd)
                    inserter.start()
                    inserters.append(inserter)

            for inserter in inserters:
                inserter.join()
        print "DONE: Post Inputs"
            
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
        print "Calling: {0}".format(cmd)
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
        print "DOING: Inserting Topology"
        #Dictionary : node -> neighbour list
        dic = {}

        for link in self.topology:
            #Add node -> neighbour to dict
            if link[0] in dic:
                dic[link[0]].append(link[1])
            else:
                dic[link[0]] = [link[1]]

            if link[1] in dic:
                dic[link[1]].append(link[0])
            else:
                dic[link[1]] = [link[0]]
        
        inserters = []
        files = []
        #create a CSV file and give it to an inserter
        for node in dic:
            f = open('csv{0}'.format(node), 'w')
            f.write('to_add\n')
            for neighbour in dic[node]:                
                f.write(neighbour + '\n')
            f.close()

            cmd = 'tuple insert andrei {0} add_neighbour csv{0}'.format(node)
            ins = Inserter(cmd)
            ins.start()
            inserters.append(ins)

        for ins in inserters:
            ins.join()

        #delete the file
        for node in dic:
            os.remove('csv{0}'.format(node))

        print "DONE: Inserting Topology"

        '''
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
                           '''                                                                                   

    def make_xml(self):
        result = Element('result')
        #Get info about the declarations at the start
        messages_elem = do_declarations(self.tran_table_dict,'messages')
        tables_elem = do_declarations(self.persistent_table_dict,'tables')

        result.append(messages_elem)
        result.append(tables_elem)

        messages_lost_elem = Element('messages_lost')
        messages_lost_elem.attrib['nr_sent'] = str(self.nr_sent)
        messages_lost_elem.attrib['nr_received'] = str(self.nr_received)
        append_messages_lost(messages_lost_elem,self.lost_list)
        result.append(messages_lost_elem)
        
        states_elem = do_states(self.node_states)
        result.append(states_elem)

        self.result = tostring(result, xml_declaration=True, pretty_print=True)

if __name__ == "__main__":
    #Add DSMEngine to the loadpath
    os.environ['PATH'] += ':/homes/ap3012/individual_project/unzipped22/bin'

    parser = OptionParser()
    '''MAYBE LATER
    parser.add_option("-c", "--config", dest="config",\
                     help="xml file to load configuration")
    '''                 

    (options,args) = parser.parse_args()
    if len(args) != 2:
        print "Need to supply config file and output file"
        exit(-1)

    config = args[0]
    output = args[1]
    if config[0] == '"':
        config = config[1,len(config-1)]
    if output[0] == '"':
        output = output[1,len(output-1)]

    time.sleep(5)
    simulator = Simulator(config,output)
    
    simulator.run_simulation()
    time.sleep(5)
