from logger_tools import *
from lxml.etree import *
def state_xml(state_dict):
    pass

#Takes in list of dicts and outputs elemment
def do_declarations(dic_list,tag):
    result = Element(tag)
    for table_dic in dic_list:
        table_elem = Element('template')
        table_elem.attrib['type'] = table_dic['name']
        table_elem.attrib['separator'] = ';'
        table_elem.attrib['columns'] = table_dic['columns']
        result.append(table_elem)
    return result 

def do_state_messages(mess_list,tag):
    result = Element(tag)
    for mess in mess_list:
        mess_elem = Element('message')
        result.append(mess_elem)
        mess_elem.attrib['content'] = mess.content
        mess_elem.attrib['type'] = mess.table_name
        if tag == 'sent':
            mess_elem.attrib['to'] = mess.dest
        elif tag == 'received':
            mess_elem.attrib['from'] = mess.src
    return result

def do_state_content(table_list):
    result = Element('content')
    
    for table in table_list:
        table_elem = Element('table')
        result.append(table_elem)
        table_elem.attrib['type'] = table.name
        for row in table.rows:
            row_elem = Element('row')
            row_elem.attrib['content'] = row
            table_elem.append(row_elem)
    
    return result

def do_one_state(state):
    result = Element('state')
    result.attrib['id'] = str(state.state_nr)
    
    result.append(do_state_messages(state.sent,'sent'))
    result.append(do_state_messages(state.received,'received'))
    result.append(do_state_content(state.tables))

    return result

def do_states(node_state_dic):
    result = Element('nodes')
    
    for node in node_state_dic:
        node_elem = Element('node')
        node_elem.attrib['id'] = node
        state_list = node_state_dic[node]
        states_elem = Element('states')
        node_elem.append(states_elem)
        result.append(node_elem)

        for state in state_list:
            states_elem.append(do_one_state(state))

    return result

if __name__ == "__main__":

    
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

    result_xml = to_xml(ABCD)
    print result_xml

    


