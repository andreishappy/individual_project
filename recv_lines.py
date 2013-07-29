if __name__ == "__main__":
    string = '''Hello
                My Name is 
                Andrei'''

    strings = string.splitlines(True)
    for string in strings:
        if string.find('\n') is not -1:
            print "Full line {0}".format(string)
        else:
            print "Partial line {0}".format(string)
