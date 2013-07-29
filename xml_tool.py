try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import string

#Could use
#    for elem in tree.iter(tag='node'):
#        print elem.tag, elem.attrib
#To find all the nodes in the whole document
class XMLParser:
    def __init__(self, filename):
        self.tree = ET.ElementTree(file=filename)
        self.tree = self.tree.getroot()
        self.nodes = {}
        self.hosts = {}

        for element in self.tree:
            if element.tag == 'hosts':
                hosts = element
            if element.tag == 'nodes':
                nodes = element

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
