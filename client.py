#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import socket
import sys
import time
from os import listdir
from os.path import isfile, join
import os.path

host = 'localhost'
port = 5000

def create_list_msg (list_of_files):
    print(list_of_files)
    print(len(list_of_files))
    list_msg = "LIST {}".format(len(list_of_files))

    for f in list_of_files :
        #print('before' + list_msg)
        list_msg += '\n' + f
        #print('after' + list_msg)
    return list_msg


def send_message(message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("INFO OF CLIENT: ")
        print(s)
    except socket.error:
        print('Failed to create socket')
        sys.exit()

    print('Socket Created')

    try:
        remote_ip = socket.gethostbyname( host )
    except socket.gaierror:
        #could not resolve
        print('Hostname could not be resolved. Exiting')
        sys.exit()

    #Connect to remote server
    global port
    while True:
        try:
            s.connect((remote_ip , port))
        except socket.error:
            port = port + 1
            print('Finding new port ' + str(port))
            continue
        break

    print('Socket Connected to ' + host + ' on ip ' + remote_ip)


    try :
        #Set the whole string
        s.sendall(message)
    except socket.error:
        #Send failed
        print('Send failed')
        sys.exit()

    print('Message send successfully')
    #Now receive data
    #reply = s.recv(4096)
   # print(reply)
    s.close()
    print ('Socket Closed')

def client():
    path = sys.argv[1]
    print(path)
    configuration = {}

    if os.path.isfile(path + '/configuration.txt') :
        configuration_file = open(path + '/configuration.txt', 'w+')
        configuration_string = configuration_file.read()
        configuration_lines = configuration_string.split('\n')
        for line in configuration_lines:
            fields = line.split(':')
            print (fields)
            fields = [field.strip() for field in fields]
            print (fields)
            if fields[0] == 'id':
                configuration['id'] = fields[1]
            elif fields[0] == 'name':
                configuration['name'] = fields[1]
            else:
                print ('error')
    else:
        configuration['id'] = '-'
        configuration_file = open(path + '/configuration.txt', 'w+')
        configuration_file.write('id: -\n')


    list_of_files = [ f for f in listdir(path+'/sharing') if isfile(join(path+'/sharing',f)) ]
    print(list_of_files)


    message = "HEY 192.168.1.6 {}".format(str(port))
    message1 = create_list_msg(list_of_files)
    print('Your name is ??????')
    nickname = raw_input()
    message2 = 'NAME ' + nickname
    configuration['name'] = nickname
    print('configuration dictionary is : ')
    print(configuration)

    #Call function
    send_message(message)
    send_message(message1)
    send_message(message2)

if __name__ == "__main__":
    client()
