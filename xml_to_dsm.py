from xml_tool import MyXMLParser
import subprocess
from thread_2_capture_messages import PhysicalNodeController,Controller
from optparse import OptionParser
import sys
import threading
import time
from lamport_transformation import *
from lxml.etree import *
from result_to_xml import *

class XML_to_DSM:

    def __init__(self,config_file):
        config = MyXMLParser(config_file)
        self.hosts = config.hosts
        self.nodes = config.nodes
        self.limit = config.limit
        self.topology = config.topology
        self.pre_inputs = config.pre_inputs
        self.post_inputs = config.post_inputs
        self.rule = config.rule
        self.monitor = Controller(self.limit,len(self.hosts))
        #next 2 return list of dicts
        self.tran_table_dict = get_table_dict(self.rule,'transport')
        self.persistent_table_dict = get_table_dict(self.rule,'persistent')

    def make_xml(self):
        result = Element('result')
        
        #Do_declarations in result_to_xml.py
        messages_elem = do_declarations(self.tran_table_dict,'messages')
        tables_elem = do_declarations(self.persistent_table_dict,'tables')

        result.append(messages_elem)
        result.append(tables_elem)
        
        states_elem = do_states(self.node_states)
        result.append(states_elem)
        return tostring(result, xml_declaration=True, pretty_print=True)

    def start_nodes(self):
    ##START THE NODES
    ##Still need to implement being able to load different rules into different engines
    ##----> node dict contains the info
    #get a list of all the node ids
        host_controllers = []
        instances = []
        
        nodes_started = 0
        hosts_done = 0
        for node in self.nodes:
            instances.append(node)
            
        
        nodes_per_host = len(self.nodes)/len(self.hosts)
        
        
        for host in self.hosts:
        #get a list of nodes to be started for each host
            first = nodes_started
            if hosts_done == len(self.hosts) -1 :
                last = len(instances)
            else:
                last = nodes_started + nodes_per_host
                
            to_start = instances[first:last]
            print "contructing for {0} with instances {1}".format(host,to_start)
            t = PhysicalNodeController(host,self.hosts[host]['username'],'andrei',to_start,self.rule,self.monitor)
            print "done constructing"
            nodes_started += nodes_per_host

            #print "started for {0}".format(host)
           
            host_controllers.append(t)
            hosts_done += 1

        #start the threads
        for thread in host_controllers:
            thread.start()
        return host_controllers
 
    def tuple_insert(self,input_list):
        for inp in input_list:
            success = False
            cmd = 'tuple insert andrei {0} {1} {2}={3}'\
                     .format(inp['instance'],inp['table_name'],
                             inp['var_name'],inp['value'])
            
            while not success:
                print "Trying {0}".format(cmd)
                process = subprocess.Popen(cmd, shell=True,\
                                           stdout=subprocess.PIPE,\
                                           stderr=subprocess.PIPE,\
                                           executable = '/bin/bash')
                
                out,err = process.communicate()
                out = str.splitlines(out)
                for line in out:
                        #print line
                    if 'Tuples sent' in line:
                        success = True
                if not success:
                    time.sleep(3)               
        
            print "SUCCEEDED {0}".format(cmd)

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
            if not success:
                    time.sleep(3)      
        print "Link {0} ==> {1} added".format(node1,node2)

    def set_topology(self):
    ##INSERT THE TOPOLOGY INTO THE NODES
        print "####Starting Insert####"
        
        for link in self.topology:
            print "Inserting link {0} <==> {1}".format(link[0],link[1])
            self.insert_link(link[0],link[1])
            self.insert_link(link[1],link[0])
    
    def run_simulation(self):
    

        #Start the nodes and get a LIST of host specific threads
        host_controllers = self.start_nodes()
        
        while not self.monitor.all_threads_started():
            pass

        time.sleep(2)
        print "all threads started"

        #Catch keyboard interrupt for clean exit
        try:
            #Pre inputs
            print '#### Doing pre inputs ####'
            self.tuple_insert(self.pre_inputs)

        #Setting Topology
            self.set_topology()

            #Post inputs
            print '#### Doing post inputs ####'
            self.tuple_insert(self.post_inputs)
        except KeyboardInterrupt:
            for thread in host_controllers:
                thread.stop()
            exit(0)
        
        time.sleep(2)
        while not self.monitor.converged() and not self.monitor.hit_limit():
            pass

        if self.monitor.hit_limit():
            print "hit_limit"
        elif self.monitor.converged():
            print "convergence reached"
        

        thread_states = []
        for thread in host_controllers:
            #Returns a dict of id -> list of State objects for each thread
            states = thread.stop()
            thread = None
            thread_states += states.items()

        self.node_states = dict(thread_states)

  

        lamport_transformation(self.node_states)
       
        for node in self.node_states:
            print "Instance {0} states".format(node)
            print "================================"
            for state in self.node_states[node]:
                print state
                '''
        f = open('bgp_dict','w')
        f.write(self.node_states)
        f.close
        '''
        result = self.make_xml()
        f = open('output.xml','w')
        f.write(result)
        f.close
        
        '''
        for thread_state in thread_states:
            for instance in thread_state:
                #if instance == "id6":
                print "Instance {0} states:\n===================".format(instance)
                for state in thread_state[instance]:
                    print state
                    '''

if __name__ == "__main__":

    parser = OptionParser()
    '''MAYBE LATER
    parser.add_option("-c", "--config", dest="config",\
                     help="xml file to load configuration")
    '''                 
    (options,args) = parser.parse_args()
    if len(args) == 0:
        print "Need to supply config file"
        exit(-1)
    
    config = args[0]
    simulator = XML_to_DSM(config)
    
    simulator.run_simulation()
    
    '''config = XMLParser(config)
    hosts = config.hosts
    nodes = config.nodes
    
    #This is HORRIBLE CODE HERE
    for node in nodes:
        rule = nodes[node]['rule']
        break

    monitor = Controller(100,len(hosts))
    
    #Start the nodes and get a LIST of host specific threads
    host_controllers = start_nodes(hosts,nodes,rule)
    
    while not monitor.all_threads_started():
        pass

    set_topology(nodes)
    while not monitor.converged():
        pass

    print "convergence reached"
    
    for thread in host_controllers:
        thread.stop()
        thread = None
        '''
    
