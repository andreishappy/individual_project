from fabric.api import *

env.user = 'ap3012'
env.hosts = ['edge27.doc.ic.ac.uk']
#env.shell = '/bin/bash'

def dsmengine():
    with settings(warn_only=True):
        result = run('nohup dsmengine -namespace andrei -instance a $PROJECT_HOME/simple_examples.dsmr >& $PROJECT_HOME/27.out < $PROJECT_HOME/27.out ')
        
        result = run('uptime')
        print result
