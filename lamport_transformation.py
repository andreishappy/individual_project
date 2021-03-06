from logger_tools import *

#Iterates through received messages to find the one
#we are looking for
def has_received(state,mess):
    for received in state.received:
        if mess == received:
            return True
    return False

#Starts from one sent message and moves down list of
#the receiving node. If it finds any sent messages by
#the receiving node, then it moves donw the tree of
#that one
def two_way_recurse(node_state_dict, node_state_list, current_time):
    for src_state in node_state_list:
        src = node_state_list[0].instance
        #print "In the list for {0}".format(src)

        if current_time > src_state.state_nr:
            #print "incrementing state_nr of {0} | {1} ==> {2}"\
            #       .format(src,src_state.state_nr,current_time)
            src_state.state_nr = current_time
        elif current_time == src_state.state_nr:
            break
        else:
            #print 'broke here'
            break
        for sent_message in src_state.sent:
            #print "Checking message"
            #print sent_message
            dest = sent_message.dest
            try:
                dest_node_state_list = node_state_dict[dest]
            except KeyError:
                pass
            
            for i in range(0,len(dest_node_state_list)):
                if has_received(dest_node_state_list[i],sent_message):
                    #print 'calling two_way_recurse on destination {0} with current time {1}'\
                    #       .format(dest,current_time)
                    two_way_recurse(node_state_dict,dest_node_state_list[i:],current_time+1)
        current_time += 1


#Changes the dict in place
def lamport_transformation(node_state_dict):
    for src in node_state_dict:
        #print "TOP LEVEL SRC is {0}".format(src)
        #print "============"
        #Iterate through every state looking for sent messages
        src_state_list = node_state_dict[src]
    
        for src_state in src_state_list:

            #For every sent message find the receiver state and
            #change the state number accordingly
            for sent_message in src_state.sent:
                dest = sent_message.dest
                try:
                    dest_state_list = node_state_dict[dest]
                except KeyError:
                    pass

                #Iterate through states until 
                for i in range(0,len(dest_state_list)):
                    if has_received(dest_state_list[i],sent_message):
                        #print "Going down for mess to {0} at time {1}".format(dest,src_state.state_nr)
                        two_way_recurse(node_state_dict,dest_state_list[i:],src_state.state_nr+1)   

if __name__ == '__main__':

    A = []
    B = []
    C = []
    D = []
    ABCD = {'A':A, 'B':B, 'C':C, 'D':D}

    for i in range(0,5):
        for let in ['A','B','C','D']:

            state = State(let,i)
            ABCD[let].append(state)

   

    messBA = Message(0,'advertise','B','A','2013-08-05 11:36:58.124','')
    messAB = Message(0,'advertise','A','B','2013-08-05 11:36:58.300','')
    messAC = Message(0,'advertise','A','C','2013-08-05 11:36:59.123','')
    messCD = Message(0,'advertise','C','D','2013-08-05 11:36:59.133','') 
    messDC = Message(0,'advertise','D','C','2013-08-05 11:33:32.155','') 
    messDA = Message(0,'advertise','D','A','2013-08-05 11:33:32.178','') 


    A[1].received.append(messBA)
    A[1].sent.append(messAC)
    A[4].sent.append(messAB)

    B[2].sent.append(messBA)
    B[3].received.append(messAB)

    C[2].received.append(messAC)
    C[4].sent.append(messCD)
    C[3].received.append(messDC)
    
    D[1].sent.append(messDC)
    D[2].received.append(messCD)
    

    D[4].sent.append(messDA)
    A[2].received.append(messDA)

    for let in ABCD:
        print "States of {0}".format(let)
        for state in ABCD[let]:
            print state

    lamport_transformation(ABCD)

    for let in ABCD:
        print "States of {0}".format(let)
        for state in ABCD[let]:
            print state
