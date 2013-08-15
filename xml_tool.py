try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import string

#Could use
#    for elem in tree.iter(tag='node'):
#        print elem.tag, elem.attrib
#To find all the nodes in the whole document
class MyXMLParser:
    def __init__(self, filename):
        self.tree = ET.ElementTree(file=filename)
        self.tree = self.tree.getroot()
        self.nodes = {}
        self.hosts = {}
        self.limit = 0
        self.topology = []
        self.pre_inputs = []
        self.post_inputs = []
        for element in self.tree:
            if element.tag == 'hosts':
                hosts = element
            elif element.tag == 'nodes':
                nodes = element
            elif element.tag == 'limit':
                self.limit=int(element.attrib['lim'])
            elif element.tag == 'topology':
                topology = element
            elif element.tag == 'pre_inputs':
                pre_inputs = element
            elif element.tag == 'post_inputs':
                post_inputs = element
            elif element.tag == 'rule':
                self.rule=element.attrib['filename']

        for inp in post_inputs:
            input_result = {}
            for key in inp.attrib:
                input_result[key] = inp.attrib[key]
            self.post_inputs.append(input_result)

        for inp in pre_inputs:
            input_result = {}
            for key in inp.attrib:
                input_result[key] = inp.attrib[key]
            self.pre_inputs.append(input_result)
            
        for link in topology:
            link_result = (link.attrib['node1'],link.attrib['node2'])
            self.topology.append(link_result)
                           
        for node in nodes:
            attributes = {}
            for attr in [a for a in node.attrib if not a == 'name']:
                if attr == 'links':
                    if node.attrib['links'] == '':
                        attributes['links'] = []
                    else:
                        attributes['links'] = string.split(node.attrib['links'],',')
                else:
                    attributes[attr] = node.attrib[attr]
                    
            self.nodes[node.attrib['id']] = attributes

        for host in hosts:
            attributes = {}
            for attr in [a for a in host.attrib if not a == 'hostname']:
                attributes[attr] = host.attrib[attr]
            
            self.hosts[host.attrib['hostname']] = attributes

if __name__ == '__main__':
    config = XMLParser('topology.xml')
    print 'nodes are \n',config.nodes
    print 'hosts are \n',config.hosts
    print 'limit is ', config.limit
