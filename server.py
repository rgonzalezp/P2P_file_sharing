import socket
from thread import *

clients = {}


def parse_msg(client, msg):
    msg_lines = msg.split('\n')
    fields = msg_lines[0].split()
    msg_id = fields[0]

    if msg_id == 'HEY':
        #client_ip = fields[1]
        #client_port = fields[2]
        pass
    elif msg_id == 'LIST':
        #print 'Len:' +str(len(msg_lines))
        #print fields
        if int(fields[1]) != (len(msg_lines) - 1):
            print "Error, incompatibility of number of files"
        clients[client]["files"] = msg_lines[1:]
    elif msg_id == 'NAME':
        print fields
        clients[client]["name"] = fields[1]
    else:
        print("this shouldn't have happened")

    print 'LIST OF CLIENTS AND THEIR FILES:\n{}'.format(clients)

 
def client_thread(client, conn):
    while True:
        data = conn.recv(1024)
        parse_msg(client, data)
        print('Data just received:')
        print (data)
        print ''

Clients_List = []

host = ''   # Symbolic name meaning all available interfaces
port = 5000 # Arbitrary non-privileged port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'
 
#Bind socket to local host and port
while True:
    try:
        s.bind((host, port))
        break
    except socket.error , msg:
        port = port + 1
        print 'changing port to an available port ' + str(port)
        
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]

print 'Socket bind complete'
 
#Start listening on socket
s.listen(10)
print 'Socket now listening'

while True:
    conn, addr = s.accept()
    print ('Connected with ' + addr[0] + ':' + str(addr[1]))
    
    clients[(addr[0], addr[1])] = {"name": "", "files": []}
    print(clients)
    start_new_thread(client_thread, ((addr[0], addr[1]),conn))