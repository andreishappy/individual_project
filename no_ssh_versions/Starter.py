from threading import *
import subprocess

class Starter(Thread):
    def __init__(self, to_start, rule, process_dict,lock):
        Thread.__init__(self)
        print "Thread constructor with instances {0}"\
               .format(to_start)
        self.rule = rule
        self.to_start = to_start
        self.process_dict = process_dict

        self.started = 0
        self.goal_nr = len(to_start)

        self.out_buffer = {}
        self.err_buffer = {}
        for instance in to_start:
            self.out_buffer[instance] = ''
            self.err_buffer[instance] = ''

        self.lock = lock

    def all_started(self):
        return self.started == self.goal_nr

    def run(self):
        print 'In run'
        for instance in self.to_start:
            cmd = 'dsmengine -namespace andrei -instance {0} {1}'\
                   .format(instance,self.rule)
                   

            print "Calling command {0}".format(cmd)
            with self.lock:
                self.process_dict[instance] = subprocess.Popen(cmd, shell=True,\
                                              stdout=subprocess.PIPE,\
                                              stderr=subprocess.PIPE,\
                                              executable = '/bin/bash')
    
        to_analyse = ''
        while not self.all_started():
            for instance in self.to_start:
                err_out = self.process_dict[instance].stderr.read(1)
                out_out = self.process_dict[instance].stdout.read(1)
                
                if err_out == '' and out_out == '': #and process.poll() != None
                    continue
                
                if err_out != '':
                    self.err_buffer[instance] += err_out
             
                if out_out != '':
                    self.out_buffer[instance] += out_out

                if '\n' in self.err_buffer[instance]:
                    '''if instance == 'n001':
                        print self.err_buffer[instance]'''
                    to_analyse = self.err_buffer[instance]
                    self.err_buffer[instance] = ''
                
                if '\n' in self.out_buffer[instance]:
                    '''if instance == 'n001':
                        print self.out_buffer[instance]'''
                    to_analyse = self.out_buffer[instance]
                    self.out_buffer[instance] = ''
                
                if to_analyse != '':
                    if instance == 'n001':
                        print "Analysing: {0}".format(to_analyse)
                        
                    if 'Engine andrei/{0} started'.format(instance) in to_analyse:
                        print to_analyse
                        self.started += 1
                        
                    if 'exiting' in to_analyse:
                        print "BUG IS BACK!!!!!!!!!!!!!",to_analyse
                
                    to_analyse = ''
