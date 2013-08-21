from optparse import OptionParser

if __name__ == "__main__":

    parser = OptionParser()
    '''MAYBE LATER
    parser.add_option("-c", "--config", dest="config",\
                     help="xml file to load configuration")
    '''                 

    parser.add_option("-p", "--parallel_topology", action="store_true",\
                      dest = 'parallel_topology', default=False,\
                      help="make the topology inserting parallel")
    (options,args) = parser.parse_args()
    print options.parallel_topology
