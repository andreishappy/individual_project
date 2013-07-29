from threading import *
import paramiko
import select
import time

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

        #used to tell when all the threads have started all their engines
        self.started_lock = Lock()
        self.threads_started = 0
        self.to_start = nr_of_hosts

    #Monitor function which ensures mutual exclusion
    def evaluation_done(self):
        with self.evaluation_lock:
            self.evaluations += 1


    def hit_limit(self):
        with self.evaluation_lock:
            if self.evaluations >= self.limit:
                return True
            else:
                return False

    def get_evaluations(self):
        with self.evaluation_lock:
            return self.evaluations

    #Could need mutual exclusion here but I don't think so
    def signal_start(self):
        with self.started_lock:
            self.threads_started += 1

    def all_threads_started(self):
        return self.threads_started == self.to_start


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

        self.instances = instances

        #Used to take output line by line
        self.line_buffer = {}
        for instance in instances:
            self.line_buffer[instance] = ''
        
        
        

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
        print "in run"
        #Start the SSH session
        #client = self.start_ssh_session()
        #Transport object is multiplexed across multiple channels
        #(one for each engine)
        transport = self.client.get_transport()

        for instance in self.instances:
            print "starting instance {0} in {1}".format(instance, self.hostname)
            channel = transport.open_session()
            channel.set_combine_stderr(True)
            #Add it to the dict
            self.channels[instance] = channel
            
            cmd = 'dsmengine -namespace {0} -instance {1} {2}'.format(self.namespace,instance,self.rule)
            #print "before command"
            channel.exec_command(cmd)
            #print 'after command'

        try:
            while True:
                for instance in self.channels:
                    channel = self.channels[instance]
                    
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
                                
                                #TESTING
                                if instance == 'id4':
                                    print l
                                
                                if 'After complete evaluation...Application' in l:
                                    print 'Instance {0} has done an evaluation'.format(instance)
                                    self.controller.evaluation_done()
                                    print "So far there have been {0} evaluations".\
                                        format(self.controller.get_evaluations())

                                    
                                
                                #Check if the engine has started and signal controller
                                elif 'Engine andrei/{0} started'.format(instance) in l:
                                    print 'Host: {0} | Node: {1} STARTED'.format(self.hostname,instance)
                                    self.started += 1
                                    if self.started == self.to_start:
                                        'All engines started on: {0}'.format(self.hostname)
                                        self.controller.signal_start()

                            #Partial line - need to pass it into the next loop
                            else:
                                self.line_buffer[instance] = l

        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def stop(self):
        print "Thread for {0} has stopped".format(self.hostname)
        stdin, stdout, stderr = client.exec_command('$PROJECT_HOME/clear_engines.sh')
    
    
                            


if __name__ == "__main__":
    monitor = Controller(2)

    t1 = PhysicalNodeController('edge09.doc.ic.ac.uk','ap3012','andrei',['a','b','c'], '$PROJECT_HOME/simple_example.dsmr',monitor)
    t2 = PhysicalNodeController('edge10.doc.ic.ac.uk','ap3012','andrei',['d','e','f','g','h','j','k','l','m','n','o'], '$PROJECT_HOME/simple_example.dsmr',monitor)
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
