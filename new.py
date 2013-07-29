from optparse import OptionParser

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",\
                     help="xml file to load configuration")

    (options,args) = parser.parse_args()
    print args
