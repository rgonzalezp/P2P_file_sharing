import socket
import sys
from thread import *
import time

def create_list_msg (list_of_files):
    print list_of_files
    print len(list_of_files)
    list_msg = "LIST {}".format(len(list_of_files))

    for f in list_of_files :
        #print 'before' + list_msg
        list_msg += '\n' + f 
        #print 'after' + list_msg
    return list_msg

def send_message (message):
	try :
	    #Set the whole string
	    s.sendall(message)
	except socket.error:
	    #Send failed
	    print 'Send failed'
	    sys.exit()
	time.sleep( 1 )
path = "/home/jim/Desktop/filesclient/" + sys.argv[1]
print path
from os import listdir
from os.path import isfile, join
List_of_files = [ f for f in listdir(path) if isfile(join(path,f)) ]

print(List_of_files)


try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "INFO OF CLIENT: "
    print s
except socket.error:
    print ('Failed to create socket')
    sys.exit()
     
print ('Socket Created')
 
host = 'localhost'
port = 5000
 
try:
    remote_ip = socket.gethostbyname( host )
except socket.gaierror:
    #could not resolve
    print ('Hostname could not be resolved. Exiting')
    sys.exit()
 
#Connect to remote server
while True:
    try:
        s.connect((remote_ip , port))
    except socket.error:
        port = port + 1
        print 'Finding new port ' + str(port)
        continue
    break

print 'Socket Connected to ' + host + ' on ip ' + remote_ip
message = "HEY 192.168.1.6 {}".format(str(port))
message1 = create_list_msg(List_of_files)
print 'Your name is ??????'
message2 = 'NAME ' + raw_input()
#Send some data to remote server
send_message(message)
send_message(message1)
send_message(message2)


 
print 'Message send successfully'
 
#Now receive data
reply = s.recv(4096)
 
print reply