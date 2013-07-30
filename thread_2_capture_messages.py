from threading import *
import paramiko
import select
import time
from logger_tools import *
import signal

class Controller():

    ############# HOW TO IMPLEMENT TERMINATION OF SIMULTAION #################
    # In order to save the state of the nodes a thread must get a state_lock #
    # While it has the state lock it will increment and check nr_evaluations #
    # If the limit is hit then the state_lock cannot be gained any more and  #
    # the threads will wait to be killed                                     #
    ##########################################################################

    def __init__(self, limit, nr_of_hosts):
        #ensures mutual exclusion on the number of evaluations
        self.evaluation_lock = Lock()        
        self.limit = limit
        self.evaluations = 0

        #ensures mutual exclusion on logging the state
        self.state_lock = Lock()

        #used to catch convergence
        self.last_state_transition = None

        #used to tell when all the threads have started all their engines
        self.started_lock = Lock()
        self.threads_started = 0
        self.to_start = nr_of_hosts

    #Monitor function which ensures mutual exclusion
    def evaluation_done(self):
        with self.evaluation_lock:
            self.evaluations += 1
            self.last_state_transition = time.time()


    def hit_limit(self):
        with self.evaluation_lock:
            return self.evaluations >= self.limit
    
    def get_evaluations(self):
        with self.evaluation_lock:
            return self.evaluations

    #Could need mutual exclusion here but I don't think so
    def signal_start(self):
        with self.started_lock:
            self.threads_started += 1

    def all_threads_started(self):
        return self.threads_started == self.to_start

    def converged(self):
        time_since_last = time.time() - self.last_state_transition

        #DEBUG
        '''
        print "Checking for convergence now ==========="
        print "last_state_transition is : {0}".format(self.last_state_transition)
        print "time since last          : {0}".format(time_since_last)'''
        return self.last_state_transition and time_since_last >= 2


class PhysicalNodeController(Thread):
    def __init__(self, hostname, user, namespace, instances, rule, controller):
        super(PhysicalNodeController,self).__init__()

        #Start the ssh session
        print "in constructor"

        #Prepare the dict of the channels
        self.channels = {}
        
        #Ensures mutual exclusion on evalution number
        self.controller = controller
        
        #Information for the ssh session - could save some memory here
        self.user = user
        self.namespace = namespace
        self.hostname = hostname
        self.client = self.start_ssh_session()

        #At the moment the rule is per thread, should change it
        #to per engine
        self.rule = rule 

        #Next 2 used to signal to controller when engines are up
        self.started = 0
        self.to_start = len(instances)
        self.thread_started = {}
        for instance in instances:
            self.thread_started[instance] = False


        self.instances = instances

        #Used to take output line by line
        self.line_buffer = {}
        for instance in instances:
            self.line_buffer[instance] = ''
        
        
        #Used to capture the sent messages of a node
        self.sent_messages = {}
        self.send_buffer = {}
        self.sending = {}
        for instance in instances:
            self.sent_messages[instance] = []
            self.send_buffer[instance] = ''
            self.sending[instance] = False

        #Used to capture received messages by nodes
        self.received_messages = {}
        self.receiving = {}
        self.receive_buffer = {}
        self.transport_names = get_transport_table_name_list(rule)
        print "TRANSPORT NAMES {0}".format(self.transport_names)
        for instance in instances:
            self.received_messages[instance] = []
            self.receiving[instance] = False
            self.receive_buffer[instance] = ''

        #Used to capture the states of nodes
        #Each instance has a list of states
        self.state_nr = {}
        self.states = {}
        self.logging_state = {}
        self.state_buffer = {}
        for instance in instances:
            self.states[instance] = []
            self.logging_state[instance] = False
            self.state_buffer[instance] = ''
            self.state_nr[instance] = 0

        #Terminates the infinite work loop
        self.stopped = False

        #Put the logs in files
        self.open_files = {}
        for instance in instances:
            self.open_files[instance] = open("engine-{0}".format(instance),'w')

        self.start_engines()


#Need to find a way to kill the engines AFTER all the states have been captured
#Idea: boolean for each instance to tell that the final state has been captured
#Talk to David about changing the logging

    def start_ssh_session(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.hostname, username=self.user, password='')
        return client

    def run(self):
        try:
            while not self.stopped:
               
                for instance in self.channels:
                    channel = self.channels[instance]
                    
                    r1, w1, x1 = select.select([channel],[],[],0.0)
                    
                    if len(r1) > 0:
                        # Must be stdout
                        
                        line = channel.recv(1024)
                        lines = line.splitlines(True)
                     
                        #Check if there is any partial line left from before
                        if self.line_buffer[instance] is not '':
                            lines[0] = self.line_buffer[instance] + lines[0]
                            self.line_buffer[instance] = ''
                        

                        for l in lines:                    

                            #Full Line - can do a check on it
                            if l.find('\n') != -1:
                                
                                self.open_files[instance].write(l)
                                self.open_files[instance].flush()
                                
                                
                                #TESTING
                                
                                if instance == 'id3' and "AbstractClientServer" not in l\
                                                   and "mcast" not in l\
                                                   and 'topology info' not in l\
                                                   and 'Refreshed registration' not in l\
                                                   and 'AbstractRouteTable' not in l:
                                    print l
                                    print "Controller is at {0}".format(self.controller.get_evaluations())

                                '''if self.thread_started[instance] == True and instance == 'id2':
                                    channel.send('^C')
                                    '''
                                if self.sending[instance]:
                                    self.send_buffer[instance] += l

                                if self.logging_state[instance]:
                                    self.state_buffer[instance] += l

                                if self.receiving[instance]:
                                    self.receive_buffer[instance] += l
 
                                #State lock is not released if 
                                if 'After complete evaluation...Application' in l and not self.controller.hit_limit():
                                    print 'Instance {0} has done an evaluation'.format(instance)
                                 
                                    print "So far there have been {0} evaluations".\
                                        format(self.controller.get_evaluations())

                                    self.logging_state[instance] = True

                                #Logging the state has finished
                                elif self.logging_state[instance] and l == '\n' and not self.controller.hit_limit():
                                    self.logging_state[instance] = False
                                    new_state = state_log_to_tables(self.state_buffer[instance],instance,self.state_nr[instance])
                                    self.states[instance].append(new_state)
                                    self.controller.evaluation_done()
                                    self.state_nr[instance] += 1
                                    self.state_buffer[instance] = ''
                                   
                                    #DEBUG
                                    '''if instance == 'id4':
                                        print "States for {0} are: {1}".format(instance,self.states[instance])
                                        '''

                                #Logging messages - if the limit has been hit, then no more are logged
                                elif 'Sending transport tuples' in l and not self.controller.hit_limit():
                                    self.sending[instance] = True
                                
                                elif self.sending[instance] and ']}' in l and not self.controller.hit_limit():
                                    self.sending[instance] = False
                                    if self.send_buffer != '':
                                        print self.state_nr[instance]
                                        current_transition_messages = sent_message_to_list(self.send_buffer[instance],\
                                                                                           self.state_nr[instance])
                                        self.sent_messages[instance] += current_transition_messages
                                    
                                        #DEBUG
                                        '''if instance == "id3":
                                            
                                            print "Sent_messages for {0} is: {1}"\
                                                .format(instance,self.sent_messages[instance])
                                        '''
                                    self.send_buffer[instance] = ''
                                    
                                #Logging received messages STARTED
                                elif 'FINE: Appending tuples' in l and has_transport_table(l, self.transport_names)\
                                                                   and not self.controller.hit_limit():
                                    self.receiving[instance] = True
                                    self.receive_buffer[instance] += l
                                
                                #Logging received messages ENDED
                                elif self.receiving[instance] == True and l == ']\n' and not self.controller.hit_limit():
                                    self.receiving[instance] = False
                                    print self.state_nr[instance]
                                    if self.receive_buffer != '':
                                        current_transition_messages = received_messages_to_list(\
                                                                      self.receive_buffer[instance],\
                                                                      self.state_nr[instance])
                                        self.received_messages[instance] += current_transition_messages
                                    self.receive_buffer[instance] = ''
                                '''                                      
                                #Check if the engine has started and signal controller
                                elif 'Engine andrei/{0} started'.format(instance) in l:
                                    print 'Host: {0} | Node: {1} STARTED'.format(self.hostname,instance)
                                    self.thread_started[instance] = True
                                    self.started += 1
                                    if self.started == self.to_start:
                                        'All engines started on: {0}'.format(self.hostname)
                                        self.controller.signal_start()
                                        '''
                            #Partial line - need to pass it into the next loop
                            else:
                                self.line_buffer[instance] = l

    


        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def start_engines(self):
        transport = self.client.get_transport()

        for instance in self.instances:
            #Open a channel for each instance
            channel = transport.open_session()
            channel.set_combine_stderr(True)
            #Add it to the dict
            self.channels[instance] = channel

            
            fail = True

            while fail:
                print "Trying to start instance {0}".format(instance)
                #Close the channel if it exits
                try:
                    self.channels[instance].close()
                except KeyError:
                    pass

                #Open a channel for the instance
                channel = transport.open_session()
                channel.set_combine_stderr(True)
                #Add it to the dict
                self.channels[instance] = channel

                cmd = 'dsmengine -namespace {0} -instance {1} {2}'.format(self.namespace,instance,self.rule)
                #print "before command"
                channel.exec_command(cmd)
                #print 'after command'

                #Loop until "engine started" is seen
                started = False
                listener_exited = False
                while not started:
                    
                    r1, w1, x1 = select.select([channel],[],[],0.0)
                    
                    if len(r1) > 0:
                        # Must be stdout
                        
                        line = channel.recv(1024)
                        #print line
                        lines = line.splitlines(True)
                        
                        #Check if there is any partial line left from before
                        if self.line_buffer[instance] is not '':
                            lines[0] = self.line_buffer[instance] + lines[0]
                            self.line_buffer[instance] = ''
                        

                        for l in lines:                    

                            #Full Line - can do a check on it
                            if l.find('\n') != -1:
                                
                                
                                if instance == 'a':
                                    print l

                                if 'Engine andrei/{0} started'.format(instance) in l:
                                    print l
                                    started = True

                                    #Engine FAILED TO START
                                    if listener_exited:
                                        print "Failed"
                                        fail = True
                                        self.kill_instance(instance)
                                        listener_exited = False
                                    #Engine SUCCESSFULLY STARTED
                                    else:
                                        print 'Host: {0} | Node: {1} STARTED'.format(self.hostname,instance)
                                        self.thread_started[instance] = True
                                        self.started += 1
                                        if self.started == self.to_start:
                                            'All engines started on: {0}'.format(self.hostname)
                                            self.controller.signal_start()
                                        fail = False

                                if 'McastTopologyMonitor:Listener exiting' in l:
                                    print l
                                    listener_exited = True 
                                        
                            

                            #Partial line - need to pass it into the next loop
                            else:
                                self.line_buffer[instance] = l 



    def stop(self):
        print "Thread for {0} has stopped".format(self.hostname)
        stdin, stdout, stderr = self.client.exec_command('$PROJECT_HOME/clear_engines.sh')
        self.stopped = True
        return self.states,self.sent_messages,self.received_messages
    
                            
    def kill_instance(self,instance):
        cmd = "$PROJECT_HOME/clear_instance.sh {0}".format(instance)
        stdin,stdout,stderr = self.client.exec_command(cmd)
        print stderr.readlines()
        print stdout.readlines()
        for line in stdout:
            print line

if __name__ == "__main__":
    monitor = Controller(2,2)

    t1 = PhysicalNodeController('edge09.doc.ic.ac.uk','ap3012','andrei',['a'], '$PROJECT_HOME/simple_example.dsmr',monitor)
    t2 = PhysicalNodeController('edge10.doc.ic.ac.uk','ap3012','andrei',['d'], '$PROJECT_HOME/simple_example.dsmr',monitor)
    try:
        t1.start()
        t2.start()
        print 'threads started'

        t1.join()
        t2.join()
        print "done"

        
    except KeyboardInterrupt:
        t1.stop()
        t2.stop()
