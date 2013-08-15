import subprocess
import sys

class Starter():
    def __init__(self):
        self.stdout_buffer = ''
        self.stderr_buffer = ''

    def start(self):
        cmd = 'dsmengine -namespace andrei -instance a simple_example.dsmr'
        process = subprocess.Popen(cmd, shell=True,\
                            stdout=subprocess.PIPE,\
                            stderr=subprocess.PIPE,\
                            executable = '/bin/bash')

        while True:
            err_out = process.stderr.read(1)
            out_out = process.stdout.read(1)
            if err_out == '' or out_out == '': #and process.poll() != None
                pass
            if err_out != '':
                self.stderr_buffer += err_out
                if '\n' in self.stderr_buffer:
                    print self.stderr_buffer
                    if 'FINE:' in self.stderr_buffer:
                        print 'returned from starter'
                        return process
                    self.stderr_buffer = ''
                    
            if out_out != '':
                self.stdout_buffer += out_out
                if '\n' in self.stdout_buffer:
                    print self.stdout_buffer
                    if 'FINE:' in self.stdout_buffer:
                        print 'returned from starter'
                        return process
                    self.stdout_buffer = ''









if __name__ == "__main__":
    starter = Starter()
    process = starter.start()



    '''
    cmd = 'dsmengine -namespace andrei -instance a simple_example.dsmr'
    process = subprocess.Popen(cmd, shell=True,\
                            stdout=subprocess.PIPE,\
                            stderr=subprocess.PIPE,\
                            executable = '/bin/bash')
                            '''
    stderr_buffer = ''
    stdout_buffer = ''
    
    while True:
        err_out = process.stderr.read(1)
        out_out = process.stdout.read(1)
        if err_out == '' or out_out == '': #and process.poll() != None
            pass
        if err_out != '':
            stderr_buffer += err_out
            if '\n' in stderr_buffer:
                print stderr_buffer
                stderr_buffer = ''

        if out_out != '':
            stdout_buffer += out_out
            if '\n' in stdout_buffer:
                print stdout_buffer
                stdout_buffer = ''
