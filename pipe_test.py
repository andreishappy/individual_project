import subprocess

if __name__ == "__main__":

    cmd = "dsmengine -namespace andrei -instance a $DSM_HOME/simple_example.dsmr 1>engine.out 2>1"
    engine = subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr = subprocess.STDOUT)
    
