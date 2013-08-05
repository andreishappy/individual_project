import string

st = '''{talk=TupleSet:TupleSetDescriptor: appDesc=andrei/a, name=talk, [ColumnDescriptor: name=DEST_INTERNAL_, type=String[128], ColumnDescriptor: name=SRC_INTERNAL_, type=String[128], ColumnDescriptor: name=PAYLOAD, type=Integer, ColumnDescriptor: name=TOC_INTERNAL_, type=Timestamp][
Tuple[TupleEntry: value=63f59043-468d-4500-b3e2-f6cbaaf12e57, TupleEntry: value=a, TupleEntry: value=1, TupleEntry: value=2013-07-28 16:25:37.893]
Tuple[TupleEntry: value=c, TupleEntry: value=a, TupleEntry: value=1, TupleEntry: value=2013-07-28 16:25:37.893]
Tuple[TupleEntry: value=d, TupleEntry: value=a, TupleEntry: value=1, TupleEntry: value=2013-07-28 16:25:37.893]
Tuple[TupleEntry: value=b, TupleEntry: value=a, TupleEntry: value=1, TupleEntry: value=2013-07-28 16:25:37.893]
], talk2=TupleSet:TupleSetDescriptor: appDesc=andrei/a, name=talk2, [ColumnDescriptor: name=DEST_INTERNAL_, type=String[128], ColumnDescriptor: name=SRC_INTERNAL_, type=String[128], ColumnDescriptor: name=PAYLOAD, type=Integer, ColumnDescriptor: name=TOC_INTERNAL_, type=Timestamp][
Tuple[TupleEntry: value=63f59043-468d-4500-b3e2-f6cbaaf12e57, TupleEntry: value=a, TupleEntry: value=1, TupleEntry: value=2013-07-28 16:25:37.897]
Tuple[TupleEntry: value=c, TupleEntry: value=a, TupleEntry: value=1, TupleEntry: value=2013-07-28 16:25:37.897]
Tuple[TupleEntry: value=d, TupleEntry: value=a, TupleEntry: value=1, TupleEntry: value=2013-07-28 16:25:37.897]
Tuple[TupleEntry: value=b, TupleEntry: value=a, TupleEntry: value=1, TupleEntry: value=2013-07-28 16:25:37.897]
]}'''

st2 ='''FINE: Appending tuples TupleSet:TupleSetDescriptor: appDesc=andrei/id4, name=advertise, [ColumnDescriptor: name=DEST_INTERNAL_, type=String[128], ColumnDescriptor: name=SRC_INTERNAL_, type=String[128], ColumnDescriptor: name=DEST, type=String[128], ColumnDescriptor: name=PATH, type=String[128], ColumnDescriptor: name=TOC_INTERNAL_, type=Timestamp][
Tuple[TupleEntry: value=id5, TupleEntry: value=id4, TupleEntry: value=id4, TupleEntry: value=id4, TupleEntry: value=2013-07-28 19:00:56.832]
]'''

st3 ='''2013-07-29 16:18:53.015'''

#Takes instance name at initialization

class TupleEntry:
    def __init__(self,value,_type):
        self.value = value
        self.type = _type

class Message:
    def __init__(self,state_nr,table_name,source,destination,timestamp,content):
        self.state_nr = state_nr
        self.table_name = table_name
        self.src = source
        self.dest = destination
        self.time = timestamp
        self.content = content

    def __str__(self):
        result = "Message: Table: {0} State: {1}\nFrom: {2} To: {3} Time: {4}\n"\
                 .format(self.table_name,self.state_nr,self.src,self.dest,self.time)
        result += "Content: {0}".format(self.content)
        return result

class State:
    def __init__(self,instance,state_nr):
        self.tables = []
        self.instance = instance
        self.state_nr = state_nr

    def add_table(self,table):
        self.tables.append(table)

    def __str__(self):
        title = "State for {0} | NR. {1}:\n".format(self.instance,self.state_nr)
        for table in self.tables:
            if 'PREV' not in table.name:
                title += '{0}'.format(table) +'\n'
        return title
            
class Table:

    #NOTE: could use tuples for column_types
    def __init__(self,name):
        self.name = name
        self.column_and_type = []
        self.rows = []
    def add_column(self, name, _type):
        self.column_and_type.append((name,_type))

    #Row is a list
    def add_row(self, row):
        self.rows.append(row)

    def __str__(self):
        result = "Table {0}\n".format(self.name)
        result += "Columns: "
        for column in self.column_and_type:
            result += "{0} --> {1} || ".format(column[0],column[1])
        result += "\nCONTENT\n"
        for row in self.rows:
            result += string.join(row,', ') + '\n'

        return result

#LOGGER TOOLS =====================================
#Returns a list of the names of transport tables
def get_transport_table_name_list(filename):
    f = open(filename, 'r')
        
    result = []
    for line in f:
        words = line.replace('(',' ').split()
        if words and words[0] == 'transport':
            result.append(words[1])

    return result

def state_log_to_tables(raw_state,instance,state_nr):
    result = State(instance,state_nr)
    tables = string.split(raw_state,'Table: ')

    for table in tables[1:len(tables)]:
                    #Find out the name of the table
        first_comma_index = table.find(',')
        name = table[0:first_comma_index]
        
        table_result = Table(name)
        
        table_descriptor_start = table.find('[') + 1
        table_descriptor_end = table.find('][')
        table_descriptor = table[table_descriptor_start:table_descriptor_end]
        column_descriptors = string.split(table_descriptor,'ColumnDescriptor: ')

        for column_descriptor in column_descriptors[1:len(column_descriptors)]:
            temp = string.split(column_descriptor,', ')
            name = string.split(temp[0],'=')[1]
            typ  = string.split(temp[1],'=')[1]
            table_result.add_column(name,typ)
                
        tuples = table[table_descriptor_end+3:len(table)]
        tuples = tuples.replace(', ','').replace('Tuple[','').replace(']','').splitlines()
        for tup in tuples:
            if tup == '' or tup == 'null':
                pass

            else:
                tup = string.split(tup,'TupleEntry: ')
                
                columns = []
                
                for column in tup[1:len(tup)]:
                    value = string.split(column,'=')[1]
                    columns.append(value)
                table_result.add_row(columns)
        result.add_table(table_result)
    return result

#Returns a list of message objects in as many tables as present
def sent_message_to_list(raw_message,state_nr):
    result = []

    transport_tables = string.split(raw_message[1:len(raw_message)],'\n], ')
    #Transport tables separated past this point
    for transport_table in transport_tables:
        #Get the name of the table example: talk=Tupleset....
        equals = transport_table.find('=')
        
        table_name = transport_table[0:equals]
        
        #Make a list of the column names and types [(name,type),....]
        column_name_and_type_list = []
        #Get the column descriptors 
        table_descriptor_start = transport_table.find('[') + 1
        table_descriptor_end = transport_table.find('][')
        table_descriptor = transport_table[table_descriptor_start:table_descriptor_end]
        column_descriptors = string.split(table_descriptor,'ColumnDescriptor: ')
                
        for column_descriptor in column_descriptors[1:len(column_descriptors)]:
            temp = string.split(column_descriptor,', ')
            name = string.split(temp[0],'=')[1]
            typ  = string.split(temp[1],'=')[1]
            column_name_and_type_list.append((name,typ))
        #Now the (name,type) list is populated

        #get the individual messages
        tuples = transport_table[table_descriptor_end+3:len(transport_table)]
        tuples = tuples.replace(', ','').replace('Tuple[','').replace(']','').replace('}','').splitlines()
        #Each message corresponds to a tup
        for tup in tuples:
            content = []
            tup = string.split(tup,'TupleEntry: ')
            if tup == ['']:
        
                continue
            for i in range(1,len(tup)):
                _type = column_name_and_type_list[i-1][1]
                _name = column_name_and_type_list[i-1][0]
                value = string.split(tup[i],'=')[1]
                if _name == "DEST_INTERNAL_":
                    dest = value
                elif _name == "SRC_INTERNAL_":
                    src = value
                elif _name == "TOC_INTERNAL_":
                    timestamp = value
                else:
                    content.append((_name,_type,value))
        
        
            #takes out nodes that are not part of the network
            if len(dest) <10:
                message = Message(state_nr,table_name,src,dest,timestamp,content)
                result.append(message)
        
        return result

def has_transport_table(line, tran_names):
    index_start = line.find('name=') + 5
    index_finish = line.find(', [')
    name = line[index_start:index_finish]
    return name in tran_names

def received_messages_to_list(line,state_nr):
    #print 'line =====> ' +line


    result = []

    index_start = line.find('name=') + 5
    index_finish = line.find(', [')
    table_name = line[index_start:index_finish]


    #Make a list of the column names and types [(name,type),....]
    column_name_and_type_list = []
        #Get the column descriptors 
    table_descriptor_start = line.find('[') + 1
    table_descriptor_end = line.find('][')
    table_descriptor = line[table_descriptor_start:table_descriptor_end]
    column_descriptors = string.split(table_descriptor,'ColumnDescriptor: ')
        
    for column_descriptor in column_descriptors[1:len(column_descriptors)]:
        temp = string.split(column_descriptor,', ')
        name = string.split(temp[0],'=')[1]
        typ  = string.split(temp[1],'=')[1]
        column_name_and_type_list.append((name,typ))
        #Now the (name,type) list is populated

    #print column_name_and_type_list
    #get the individual messages
    tuples = line[table_descriptor_end+3:len(line)]
    tuples = tuples.replace(', ','').replace('Tuple[','').replace(']','').replace('}','').splitlines()


    for tup in tuples:
        content = []
        tup = string.split(tup,'TupleEntry: ')
        if tup == ['']:
            
            continue
        for i in range(1,len(tup)):
            _type = column_name_and_type_list[i-1][1]
            _name = column_name_and_type_list[i-1][0]
            value = string.split(tup[i],'=')[1]
            if _name == "DEST_INTERNAL_":
                dest = value
            elif _name == "SRC_INTERNAL_":
                src = value
            elif _name == "TOC_INTERNAL_":
                timestamp = value
            else:
                content.append((_name,_type,value))
        
        
            #takes out nodes that are not part of the network
        if len(dest) <10:
            message = Message(state_nr,table_name,src,dest,timestamp,content)
            result.append(message)
            #print message
        
    return result


if __name__ == "__main__":
    
    print received_messages_to_list(-1,st2)
    '''print get_transport_table_name_list('/homes/ap3012/individual_project/home/BGP_v1.dsmr')


    print transport_table(st2,['hell','on','advertise'])
'''


