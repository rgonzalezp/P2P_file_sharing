#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import socket
import sys
import thread

from library.library import configuration_load
from library.library import configuration_save
from library.library import send_message


configuration_file = ""
configuration = {}
clients = {}


def converse(connection, client, incoming_buffer, previous_command):
    global configuration_file
    global configuration
    global clients

    if "\0" not in incoming_buffer:
        return "", previous_command
    else:
        index = incoming_buffer.index("\0")
        message = incoming_buffer[0:index-1]
        incoming_buffer = incoming_buffer[index+1:]
    # DEBUG
    print("message received:")
    print(message)
    print()

    lines = message.split('\n')
    fields = lines[0].split()
    command = fields[0]
    #na diorthwsoume bug, otan mpainei deuteri fora o idios na min ton
    #ksanavazei sti lista clients, mono na enimwrnei ta arxeia 
    if command == 'HEY':
        client_id = fields[1]
        if client_id == "-":
            configuration["max_id_offset"] += 1
            configuration_save(configuration_file, configuration)
            client_id = "user_{0:0>4}".format(configuration["max_id_offset"])
        send_message(connection, "WELCOME " + client_id + "\n\0")
        return converse(connection, client, incoming_buffer, "WELCOME")

    elif command == 'LIST':
        number_of_files = int(fields[1])
        if number_of_files != (len(lines) - 1):
            print("error, wrong number of files")
            #to reply den to xrisimopoioume kapou, logika tha eprepe na to epistrefoume kai na to anagnwrizei o client
            reply = "ERROR\n\0"
        else:
            clients[client]["files"] = lines[1:]
        send_message(connection, "OK\n\0")
        return incoming_buffer, "OK"

    elif command == 'NAME':
        print(fields)
        clients[client]["name"] = fields[1]
        send_message(connection, "OK\n\0")

        # DEBUG
        print("clients:")
        print(clients)

        return incoming_buffer, "OK"

    #elif command == 'SENDLIST':
    #stelnei tin lista ston client

    elif command == 'OK' and previous_command == "WELCOME":
        return incoming_buffer, "OK"

    else:
        # TODO
        # handle invalid commands
        print("error, invalid command")
        sys.exit(-1)


def client_thread(connection, address):
    global clients

    clients[address] = {"name": "", "files": []}

    # start with an empty incoming messages buffer
    incoming_buffer = ""
    previous_command = ""

    while True:
        incoming = connection.recv(4096)
        if len(incoming) == 0:
            break
        else:
            incoming_buffer += incoming

        incoming_buffer, previous_command = converse(connection, address, incoming_buffer, previous_command)


def serve(host, port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('error, socket.socket')
        sys.exit(-1)

    # TODO
    # replace with the equivalent code without using an offset
    while True:
        try:
            server_socket.bind( (host, port) )
            break
        except socket.error:
            # DEBUG
            print("port {} in use, trying the next one".format(port))
            port += 1

    # listen for incoming connections
    server_socket.listen(5)
    print('server listening on port: ' + str(port))
    print()

    # handle incoming connections
    while True:
        connection, address = server_socket.accept()
        # DEBUG
        print('a client connected with ' + address[0] + ':' + str(address[1]))

        thread.start_new_thread(client_thread, (connection, address))


def server():
    global configuration_file
    global configuration
    global clients

    configuration_file = "configuration.json"

    if os.path.isfile(configuration_file):
        configuration = configuration_load(configuration_file)
    else:
        configuration["host"] = "localhost"
        configuration["port"] = 5000
        configuration['max_id_offset'] = 0
        configuration_save(configuration_file, configuration)
    # DEBUG
    print("configuration:")
    print(configuration)
    print()


    serve(configuration["host"], configuration["port"])

if __name__ == "__main__":
    server()
