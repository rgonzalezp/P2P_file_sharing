#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import socket
import thread


configuration = {}
clients = {}


def create_message(message_type, arguments):
    if message_type == "WELCOME":
        message = "WELCOME" + arguments[0]
    elif message_type == "OK":
        message = "OK"
    else:
        print("error, wrong message type")
        sys.exit()

    return message


def send_message(client, message):
    client_ip, client_port = client

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('error, failed to create socket')
        sys.exit()

    offset = 0
    while True:
        try:
            s.connect((client_ip, client_port + offset))
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
        print('error')
        sys.exit()

    s.close()



def parse_msg(peer_socket, client, msg):
    print(msg)
    msg_lines = msg.split('\n')
    fields = msg_lines[0].split()
    msg_id = fields[0]

    if msg_id == 'HEY':
        client_id = fields[1]
        if client_id == "-":
            configuration["max_id"] += 1
            with open(configuration_path, 'wb+') as f:
                pickle.dump(configuration, f)
            client_id = "user_{04}".format(configuration["max_id"])
        message = create_message("WELCOME", (client_id, ))
        send_message(peer_socket, message)

    elif msg_id == 'LIST':
        #print('Len:' +str(len(msg_lines)))
        #print(fields)
        if int(fields[1]) != (len(msg_lines) - 1):
            print("Error, incompatibility of number of files")
        clients[client]["files"] = msg_lines[1:]
    elif msg_id == 'NAME':
        print(fields)
        clients[client]["name"] = fields[1]
    else:
        print("this shouldn't have happened")

    print('LIST OF CLIENTS AND THEIR FILES:\n{}'.format(clients))


def client_thread(peer_socket, client):
    while True:
        data = peer_socket.recv(1024)
        parse_msg(peer_socket, client, data)
        print('Data just received:')
        print(data)
        print('')


def server():
    configuration_path = "configuration.txt"

    if os.path.isfile(configuration_path):
        with open(configuration_path, 'rb') as f:
            configuration = pickle.load(f)
        print("configuration: ")
        print(configuration)
    else:
        configuration['id'] = '-'
        configuration['max_id'] = 0
        with open(configuration_path, 'wb+') as f:
            pickle.dump(configuration, f)


    host = 'localhost'
    port = 5000

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')

    #Bind socket to local host and port
    while True:
        try:
            s.bind((host, port))
            break
        except socket.error, msg:
            port += 1


    #Start listening on socket
    s.listen(5)
    print('server listening on port: ' + port)

    while True:
        peer_socket, address = s.accept()
        print('client connected with ' + address[0] + ':' + str(address[1]))

        clients[address] = {"name": "", "files": []}
        print(clients)

        thread.start_new_thread(client_thread, (peer_socket, address))


if __name__ == "__main__":
    server()
