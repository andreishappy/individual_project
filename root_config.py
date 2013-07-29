if __name__ == "__main__":
    f = open("/root/.bashrc", "a")
    towrite = '''export PATH=$PATH:/homes/ap3012/individual_project/unzipped5/bin
export DSM_HOME=/homes/ap3012/individual_project/unzipped5
export OPINIONS=/homes/ap3012/individual_project/unzipped5/samples/com/ibm/watson/dsm/samples/opinions
export SAMPLES=/homes/ap3012/individual_project/unzipped5/samples/com/ibm/watson/dsm/samples/'''
    f.write(towrite)
    f.close
