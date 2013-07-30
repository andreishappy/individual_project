from xml_tool import XMLParser
import subprocess
from thread_2_capture_messages import PhysicalNodeController,Controller
from optparse import OptionParser
import sys
import threading
import time

class XML_to_DSM:

    def start_nodes(self,hosts,nodes,rule,monitor):
    ##START THE NODES
    ##Still need to implement being able to load different rules into different engines
    ##----> node dict contains the info
    #get a list of all the node ids
        host_controllers = []
        instances = []
        
        nodes_started = 0
        hosts_done = 0
        for node in nodes:
            instances.append(node)
            
        
        nodes_per_host = len(nodes)/len(hosts)
        
        
        for host in hosts:
        #get a list of nodes to be started for each host
            first = nodes_started
            if hosts_done == len(hosts) -1 :
                last = len(instances)
            else:
                last = nodes_started + nodes_per_host
                
            to_start = instances[first:last]
            print "contructing for {0} with instances {1}".format(host,to_start)
            t = PhysicalNodeController(host,hosts[host]['username'],'andrei',to_start,rule,monitor)
            print "done constructing"
            nodes_started += nodes_per_host

            #print "started for {0}".format(host)
           
            host_controllers.append(t)
            hosts_done += 1

        #start the threads
        for thread in host_controllers:
            thread.start()
        return host_controllers
                
                
    def set_topology(self,nodes):
    ##INSERT THE TOPOLOGY INTO THE NODES
        print "####Starting Insert####"
        for node in nodes:
            print "node {0} has links {1}".format(node,nodes[node]['links'])
            for link in nodes[node]['links']:
                success = False
                while not success:
                    print "inserting link {0} into node {1}".format(link,node)
                    process = subprocess.Popen('tuple insert andrei {0} add_neighbour to_add={1}'\
                                                   .format(node,link),shell=True,\
                                                   stdout=subprocess.PIPE,\
                                                   stderr=subprocess.PIPE,\
                                                   executable = '/bin/bash')
                    out,err = process.communicate()
                    out = str.splitlines(out)
                    for line in out:
                        if 'Tuples sent' in line:
                            success = True
                    time.sleep(3)
            print "Neighbour {0} added to node {1}".format(link,node)
                            
    def run_simulation(self,config_file):
        config = XMLParser(config_file)
        hosts = config.hosts
        nodes = config.nodes
        limit = config.limit
        #This is HORRIBLE CODE HERE
        for node in nodes:
            rule = nodes[node]['rule']
            print 'l'
            break

        print "rule is {0}".format(rule)

        monitor = Controller(limit,len(hosts))
    
        #Start the nodes and get a LIST of host specific threads
        host_controllers = self.start_nodes(hosts,nodes,rule,monitor)
        
        while not monitor.all_threads_started():
            pass

        time.sleep(2)
        print "all threads started"

        #Setting Topology
        try:
            self.set_topology(nodes)
        except KeyboardInterrupt:
            for thread in host_controllers:
                thread.stop()
            exit(0)
        while not monitor.converged() and not monitor.hit_limit():
            pass

        if monitor.converged():
            print "convergence reached"
        elif monitor.hit_limit():
            print "hit_limit"
        

        thread_states = []
        thread_messages_sent = []
        thread_messages_received = []
        for thread in host_controllers:
            #Returns a dict of id -> list of State objects for each thread
            states,sent_messages,received_messages = thread.stop()
            thread = None
            thread_states.append(states)
            thread_messages_sent.append(sent_messages)
            thread_messages_received.append(received_messages)
        
        for thread_state in thread_states:
            for instance in thread_state:
                print "Instance {0} states:\n===================".format(instance)
                if instance == "id3":
                    for state in thread_state[instance]:
                        print state

        print "Messages Sent ========================="
        for thread_message in thread_messages_sent:
            for instance in thread_message:
                if instance == "id3":
                    print "Instance {0} messages sent:\n================".format(instance)
                    for mess in thread_message[instance]:
                        print mess
                    
        print "Messages Received ====================="
        for thread_message in thread_messages_received:
            for instance in thread_message:
                if instance == "id3":
                    print "Instance {0} messages received:\n================".format(instance)
                    for mess in thread_message[instance]:
                        print mess
            


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
    simulator = XML_to_DSM()
    
    simulator.run_simulation(config)
    
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
    
