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
        message = "WELCOME " + arguments[0]
    elif message_type == "OK":
        message = "OK"
    else:
        print("error, wrong message type")
        sys.exit()

    return message


def send_message(client, message):
    client_ip, client_port = client

    try:
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('error, failed to create socket')
        sys.exit()

    offset = 0
    while True:
        try:
            socket_.connect((client_ip, client_port + offset))
            print()
            print("DEBUG connected:")
            print(socket_)
            print()
        except socket.error:
            offset += 1
            continue
        break

    try:
        socket_.sendall(message)
    except socket.error:
        print('error, socket.sendall')
        sys.exit()

    socket_.close()



def parse_message(peer_socket, client, message):
    print(message)
    message_lines = message.split('\n')
    fields = message_lines[0].split()
    message_id = fields[0]

    if message_id == 'HEY':
        client_id = fields[1]
        if client_id == "-":
            configuration["max_id"] += 1
            with open(configuration_path, 'wb+') as f:
                pickle.dump(configuration, f)
            client_id = "user_{04}".format(configuration["max_id"])
        message = create_message("WELCOME", (client_id, ))

    elif message_id == 'LIST':
        if int(fields[1]) != (len(message_lines) - 1):
            print("Error, incompatibility of number of files")
        clients[client]["files"] = message_lines[1:]
    elif message_id == 'NAME':
        print(fields)
        clients[client]["name"] = fields[1]
    else:
        print("this shouldn't have happened")

    print("clients:")
    print(clients)


def client_thread(peer_socket, client):
    while True:
        data = peer_socket.recv(1024)
        print('message received:')
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
        configuration["host"] = "localhost"
        configuration["port"] = 5000
        configuration['max_id'] = 0
        with open(configuration_path, 'wb+') as f:
            pickle.dump(configuration, f)


    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')

    #Bind socket to local host and port
    while True:
        try:
            socket_.bind((host, port))
            break
        except socket.error, message:
            port += 1


    #Start listening on socket
    socket_.listen(5)
    print('server listening on port: ' + port)

    while True:
        peer_socket, address = socket_.accept()
        print('client connected with ' + address[0] + ':' + str(address[1]))

        clients[address] = {"name": "", "files": []}
        print(clients)

        thread.start_new_thread(client_thread, (peer_socket, address))


if __name__ == "__main__":
    server()
