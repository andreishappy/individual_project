from xml.etree.ElementTree import *
import optparse

#Takes in a list of dicts
def do_dec(dic_list,tag):
    result = Element(tag)
    for dic in dic_list:
        template_elem = Element('template')
        template_elem.attrib['type'] = dic['type']
        template_elem.attrib['columns'] = dic['columns']
        template_elem.attrib['separator'] = dic['separator']
        result.append(template_elem)
    print '\n'.join(tostringlist(result))

def make_xml(filename):
    print 'opening ' + filename
    f = open(filename, 'r')
    root_dict = f.read()
    root_dict = eval(root_dict)

    result = ''
    
    
    message_dec = root_dict['messages']
    table_dec = root_dict['tables']
    message_dec = do_dec(message_dec,'messages')
    table_dec = do_dec(table_dec,'tables')

    nodes_dict = root_dict['nodes']

if __name__ == '__main__':
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    if len(args) != 2:
        sys.stderr.write("Usage: python to_xml.py source destination")
        exit(-1)

    xml_data = make_xml(args[0])
