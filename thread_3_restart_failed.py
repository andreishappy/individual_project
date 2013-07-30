from threading import *
import paramiko
import select
import time
from logger_tools import *

class HostController(Thread):
    #No controller yet
    def __init__(self,hostname,user,namespace,instances,rule):
        super(HostController,self).__init__()
        
        #Information for the ssh session - could save some memory here
        self.user = user
        self.namespace = namespace
        self.hostname = hostname
        self.client = self.start_ssh_session()
        self.channels = {}

        #Keep track of number of started threads
        self.started = 0
        self.to_start = len(instances)
        
        #Line buffer for recv
        self.line_buffer = {}
        for instance in instances:
            self.line_buffer[instance] = ''

        self.rule = rule
        self.instances = instances


    def start_ssh_session(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.hostname, username=self.user, password='')
        return client


    def run(self):
        self.start_threads()

    def kill_instance(self,instance):
        cmd = "$PROJECT_HOME/clear_instance.sh {0}".format(instance)
        stdin,stdout,stderr = self.client.exec_command(cmd)
        print stderr.readlines()
        print stdout.readlines()
        for line in stdout:
            print line

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
                                
                                

                                if 'Engine andrei/{0} started'.format(instance) in l:
                                    print l
                                    started = True
                                    if listener_exited:
                                        print "Failed"
                                        fail = True
                                        self.kill_instance(instance)
                                        listener_exited = False
                                    else:
                                        print "Did not fail, move to the next"
                                        fail = False

                                if 'McastTopologyMonitor:Listener exiting' in l:
                                    print l
                                    listener_exited = True 
                                        
                            

                            #Partial line - need to pass it into the next loop
                            else:
                                self.line_buffer[instance] = l 

                

if __name__ == '__main__':
    h = HostController('edge17.doc.ic.ac.uk','ap3012','andrei',['a','b','c','d','e','f'],'/homes/ap3012/individual_project/home/simple_example.dsmr')
    h.start_engines()
