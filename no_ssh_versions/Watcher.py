from threading import *
from logger_tools import *
import time
from xml_tool import MyXMLParser
import subprocess

class WatcherMonitor():
    def __init__(self,limit):
        self.limit = limit
        self.last_evaluation = time.time()
        self.evaluations = 0

    def converged(self):
        time_since_last = time.time() - self.last_evaluation
        #print time_since_last
        return time_since_last >= 20

    def evaluation_done(self):
        self.evaluations += 1
        self.last_evaluation = time.time()

    def hit_limit(self):
        return self.evaluations >= self.limit

class Watcher(Thread):
    def __init__(self,process_dict,config,monitor,pers_dict_list,\
                     transport_dict_list):
        Thread.__init__(self)
        self.monitor = monitor

        #Dict: node_id -> persistent table names (capture content)
        #self.node_to_persistent = node_to_persistent

        self.pers_tables = []
        for table in pers_dict_list:
            self.pers_tables.append(table['name'])


        #self.limit = config.limit
        #self.evaluations = 0
        self.stopped = False
        self.process_dict = process_dict
        #FROM THREAD_2_CAPTURE  ####################
        #Used to catch convergence
        #self.last_evaluation = time.time()

        #Used to capture the sent messages of a node
        self.current_sent_messages = {}
        self.send_buffer = {}
        self.sending = {}
        for instance in process_dict:
            self.current_sent_messages[instance] = []
            self.send_buffer[instance] = ''
            self.sending[instance] = False

        #Used to capture received messages by nodes
        self.current_received_messages = {}
        self.receiving = {}
        self.receive_buffer = {}
        
        self.transport_names = []
        for table in transport_dict_list:
            self.transport_names.append(table['name'])

        #print "TRANSPORT NAMES {0}".format(self.transport_names)
        for instance in process_dict:
            self.current_received_messages[instance] = []
            self.receiving[instance] = False
            self.receive_buffer[instance] = ''

        #Used to capture the states of nodes
        #Each instance has a list of states
        self.state_nr = {}
        self.states = {}
        self.logging_state = {}
        self.state_buffer = {}
        for instance in process_dict:
            self.states[instance] = []
            self.logging_state[instance] = False
            self.state_buffer[instance] = ''
            self.state_nr[instance] = 0

        #Terminates the infinite work loop
        self.stopped = False

        
        #Put the logs in files
        self.open_files = {}
        for instance in process_dict:
            self.open_files[instance] = open("engine-{0}".format(instance),'w')
            
        #END FROM THREAD_2_CAPTURE

        #FROM CENTRAL_SIMULATOR ==================

        self.err_buffer = {}
        self.out_buffer = {}
        for instance in self.process_dict:
            self.out_buffer[instance] = ''
            self.err_buffer[instance] = ''
        #END CENTRAL_SIMULATOR ==================

        #LINE BUFFER SHOULD SPEED UP LOGGING FOR ENGINES
        self.line_buffer = {}
        for instance in process_dict:
            self.line_buffer[instance] = ''


    def converged(self):
        time_since_last = time.time() - self.last_evaluation
        return time_since_last >= 20

    def hit_limit(self):
        return self.evaluations == self.limit
        
    def run(self):
        while not self.stopped and not self.monitor.hit_limit():
            #start_of_loop = time.time()
            for instance in self.process_dict:
                if self.process_dict[instance].poll() != None:
                    print "Instance {0} terminated".format(instance)

                try:
                    #ONLY LOOKING AT STDERR
                    lines = self.process_dict[instance].stderr.read(2048)
                    lines = lines.splitlines(True)
                   
                    if self.line_buffer[instance] != '':
                        lines[0] = self.line_buffer[instance] + lines[0]
                        self.line_buffer[instance] = ''

                    for l in lines:
                        if l.find('\n') != -1: #full line
                            self.analyse(l,instance)
                        else: #partial line add to the buffer
                            self.line_buffer[instance] = l
                except IOError:
                    pass
            #end_of_loop = time.time()
            #print "Time of one loop: {0}".format(end_of_loop - start_of_loop)


    def analyse(self,l,instance):
        #WRITE TO DISK
        self.open_files[instance].write(l)
        self.open_files[instance].flush()
                             
        #CHECK IF THE LISTENER EXITS
        if 'exiting' in l:
            print 'Instance {0} listener exited' 

        if self.sending[instance]:
            self.send_buffer[instance] += l

        if self.logging_state[instance]:
            self.state_buffer[instance] += l

        if self.receiving[instance]:
            #print "Receiving {0}".format(instance)
            self.receive_buffer[instance] += l
 
        #Star of state logging FOUND
        if 'After complete evaluation...Application' in l and not self.monitor.hit_limit():
            print 'Instance {0} has done an evaluation'.format(instance)
        
            self.monitor.evaluation_done()
            print "So far there have been {0} evaluations"\
                   .format(self.monitor.evaluations)

            self.logging_state[instance] = True

        #Logging the state has finished
        elif self.logging_state[instance] and l == '\n' and not self.monitor.hit_limit():

        #Create the new state and add the messages sent and received to it
            new_state = state_log_to_state(self.state_buffer[instance],instance,\
                                           self.state_nr[instance],\
                                           self.current_sent_messages[instance],\
                                           self.current_received_messages[instance],\
                                           self.pers_tables)
                                    
            self.current_sent_messages[instance] = []
            self.current_received_messages[instance] = []
            self.states[instance].append(new_state)

         
            self.state_nr[instance] += 1
            self.state_buffer[instance] = ''
            #Prepare for next state logging
            self.logging_state[instance] = False  
            #self.last_evaluation = time.time()

        #Logging sent messages STARTED
        elif 'Sending transport tuples' in l and not self.monitor.hit_limit():
            self.sending[instance] = True
                                
        #Logging sent messages ENDED
        elif self.sending[instance] and ']}' in l and not self.monitor.hit_limit():
            self.sending[instance] = False
            if self.send_buffer != '':
                #Get a list of the current transition's sent messages to add
                #to the state when the state transition is done
                self.current_sent_messages[instance] = sent_message_to_list(self.send_buffer[instance],\
                                                                            self.state_nr[instance])

                self.send_buffer[instance] = ''
                                    
        #Logging received messages STARTED
        elif 'FINE: Appending tuples' in l and \
              has_transport_table(l, self.transport_names)\
              and not self.monitor.hit_limit():

            self.receiving[instance] = True
            self.receive_buffer[instance] += l
                                
        #Logging received messages ENDED
        elif self.receiving[instance] == True and l == ']\n' and not self.monitor.hit_limit():
            self.receiving[instance] = False
            
            if self.receive_buffer != '':
                #Get a list of the current transitions received messages to add
                #to the state when the state transition is done
                self.current_received_messages[instance] = received_messages_to_list(\
                                                                      self.receive_buffer[instance],\
                                                                      self.state_nr[instance])
                #self.received_messages[instance] += current_transition_messages
                self.receive_buffer[instance] = ''
    
    def stop(self):
        print "Watcher has stopped"
        cmd = '$PROJECT_HOME/clear_engines.sh'
        p = subprocess.Popen(cmd, shell=True,\
                             stdout=subprocess.PIPE,\
                             stderr=subprocess.PIPE,\
                             executable = '/bin/bash')
        self.stopped = True
        return self.states
