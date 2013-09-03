import string

if __name__ == "__main__":
    f = open("experiment_data","r")
    r = open("result",'w')
    
    for line in f:
        start = string.find(line,": ")
        end = string.find(line,", ")
        while start != -1 and end != -1:
            to_write = line[start+2:end]
            r.write(to_write + ' & ')
            line = line[end+1:]
            print line
            start = string.find(line,": ")
            print end
            end = string.find(line,", ")
      
        r.write('\n')
      
    f.close()
    r.close()
