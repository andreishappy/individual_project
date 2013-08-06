import time
import optparse
import sys

def print_pause(message):
    print message
    time.sleep(1)

    
if __name__ == "__main__":

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    if len(args) != 2:
        sys.stderr.write("arg1: .xml config file\narg2: .xml result output file")
        exit(-1)

    config_file = args[0]
    output_file = args[1]
        
    print_pause('Starting 15 engines and installing rules')
    number_started = [3,5,8,12,15]
    for started in number_started:
        print_pause('{0} engines started'.format(started))

    print_pause('Starting simulation')

    print_pause('Doing tuple inserts before topology')
    print_pause('Setting up topology')
    print_pause('Doing tuple inserts after topology')

    print_pause('Simulation done')

    print_pause('Now returning simulation data')
    
