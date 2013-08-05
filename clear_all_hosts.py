import paramiko
from optparse import OptionParser
from xml_tool import XMLParser

if __name__ == "__main__":
    parser = OptionParser()
    (options,args) = parser.parse_args()

    config = XMLParser(args[0])
    hosts = config.hosts


    for host in hosts:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=hosts[host]['username'], password='')
        stdin,stdout,stderr = ssh.exec_command('/homes/ap3012/individual_project/home/clear_engines.sh')
        out = stdout.readlines()
        err = stderr.readlines()

        for line in out:
            print line
            

        for line in err:
            print err
    
