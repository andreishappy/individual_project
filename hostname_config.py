

if __name__ == "__main__":

    f = open("/etc/hosts","a")
    f.write("10.0.0.20 n1\n")
    f.write("10.0.0.21 n2\n")
    f.close()

