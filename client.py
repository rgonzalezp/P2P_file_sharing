#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import socket
import sys
import time
import cPickle as pickle


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


def send_message(server, message):
    server_ip, server_port = server

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('error, failed to create socket')
        sys.exit()

    offset = 0
    while True:
        try:
            s.connect((server_ip, server_port + offset))
            print()
            print("DEBUG connected:")
            print(s)
            print()
        except socket.error:
            offset += 1
            continue
        break

    try:
        s.sendall(message)
    except socket.error:
        print('Send failed')
        sys.exit()

    reply = s.recv(1024)
    print(reply)

    # close the socket
    s.close()


def client():
    # check if an argument was passed
    if len(sys.argv) < 2:
        print("please pass one of the arguments: {1, 2, 3}")
        sys.exit()

    configuration = {}

    working_directory = sys.argv[1]
    print("working_directory: " + working_directory)

    configuration_path = working_directory + "/configuration.txt"
    if os.path.isfile(configuration_path):
        with open(configuration_path, 'rb') as f:
            configuration = pickle.load(f)
        print("configuration: ")
        print(configuration)
    else:
        configuration['id'] = '-'
        with open(configuration_path, 'wb+') as f:
            pickle.dump(configuration, f)


    list_of_files = [ f for f in os.listdir(working_directory + '/sharing') if os.path.isfile(os.path.join(working_directory + '/sharing', f)) ]
    print(list_of_files)


    message = "HEY {}".format(configuration["id"])

    message1 = create_list_msg(list_of_files)

    print('Your name is ??????')
    nickname = raw_input()
    configuration['name'] = nickname
    with open(configuration_path, 'wb+') as f:
        pickle.dump(configuration, f)
    message2 = 'NAME ' + configuration["name"]

    # call function
    send_message(message)
    send_message(message1)
    send_message(message2)


if __name__ == "__main__":
    client()
