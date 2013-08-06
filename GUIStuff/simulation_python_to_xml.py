from lxml.etree import *

def do_dec(dic_list,tag):
    result = Element(tag)
    for table_dic in dic_list:
        table_elem = Element('template')
        table_elem.attrib['type'] = table_dic['type']
        table_elem.attrib['separator'] = ';'
        table_elem.attrib['columns'] = table_dic['columns']
        result.append(table_elem)
    return result

def do_mess(dic_list,tag):
    result = Element(tag)

    for mess in dic_list:
        mess_elem = Element('message')
        result.append(mess_elem)
        for attrib in mess:
            mess_elem.attrib[attrib] = mess[attrib]

    return result

def do_content(content):
    result = Element('content')
    for table in content:
        table_elem = Element('table')
        table_elem.attrib['type'] = table
        result.append(table_elem)
        for row in content[table]:
            row_elem = Element('row')
            row_elem.attrib['content'] = row
            table_elem.append(row_elem)

    return result

    
def do_states(state_list):
    result = Element('states')
    
    for state_dic in state_list:
        state_elem = Element('state')
        state_elem.attrib['id'] = state_dic['state_nr']

        sent_messages = state_dic['sent']
        received_messages = state_dic['received']
        state_elem.append(do_mess(sent_messages,'sent'))
        state_elem.append(do_mess(received_messages,'received'))

        content = state_dic['content']
        state_elem.append(do_content(content))
        result.append(state_elem)
        
    return result



def make_xml(input_file, output_file):
    f = open(input_file,'r')
    dic = f.read()
    dic = eval(dic)
    f.close()

    result = Element('result')

    mess_decs = dic['messages']
    mess_dec = do_dec(mess_decs, 'messages')
    result.append(mess_dec)
    
    table_decs = dic['tables']
    table_dec = do_dec(table_decs, 'tables')
    result.append(table_dec)

    node_dic = dic['nodes']
    nodes_elem = Element('nodes')
    result.append(nodes_elem)
    
    for node in node_dic:
        node_elem = Element('node')
        node_elem.attrib['id'] = node
        state_list = node_dic[node]
        node_elem.append(do_states(state_list))
        nodes_elem.append(node_elem)

    f = open(output_file,'w')
    xml_output = tostring(result, xml_declaration=True, pretty_print=True,encoding=None)
    f.write(xml_output)
    f.close()
    

if __name__ == "__main__":
   #make_xml(input_file->python dict, output_file -> .xml)
