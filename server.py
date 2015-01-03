#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import socket
import sys
import thread

from library.library import json_load
from library.library import json_save
from library.library import send_message


configuration_file = ""
configuration = {}

clients_file = ""
# {client_id: {'name': name, 'files': [list of shared files], listening_connection: (IP_address, port)}}
clients = {}

# {(IP_address, port): client_id}
connected_clients = {}
# connected_clients[ (old_IP_address, old_port) ] -> client_id
# connected_clients[ (new_IP_address, new_port) ] -> client_id


# NOTE
# (incoming_buffer, own_previous_command) in "state" in FSM
def converse(connection, client, incoming_buffer, own_previous_command):
    global configuration_file
    global configuration
    global clients_file
    global clients
    global connected_clients

    if "\0" not in incoming_buffer:
        return "", own_previous_command
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

    if command == 'HEY':
        client_id = fields[1]
        if client_id == "-":
            configuration["max_id_offset"] += 1
            json_save(configuration_file, configuration)
            client_id = "user_{0:0>4}".format(configuration["max_id_offset"])

            clients[client_id] = {"name": "", "files": [], "listening_connection": None}
            json_save(clients_file, clients)

        connected_clients[client] = client_id

        # DEBUG
        print("connected_clients:")
        print(connected_clients)

        send_message(connection, "WELCOME " + client_id + "\n\0")
        return converse(connection, client, incoming_buffer, "WELCOME")

    elif command == 'LIST':
        number_of_files = int(fields[1])
        if number_of_files != (len(lines) - 1):
            print("error, wrong number of files")
            # TODO
            #to reply den to xrisimopoioume kapou, logika tha eprepe na to epistrefoume kai na to anagnwrizei o client
            reply = "ERROR\n\0"
        else:
            clients[connected_clients[client]]["files"] = lines[1:]
            json_save(clients_file, clients)
        send_message(connection, "OK\n\0")
        return incoming_buffer, "OK"

    elif command == 'NAME':
        print(fields)
        clients[connected_clients[client]]["name"] = fields[1]
        json_save(clients_file, clients)
        send_message(connection, "OK\n\0")

        # DEBUG
        print("clients:")
        print(clients)

        return incoming_buffer, "OK"

    elif command == 'SENDLIST':
        number_of_all_clients_files = 0
        for client in clients:
            number_of_all_clients_files += len(clients[client]["files"])
        fulllist_message = "FULLLIST {}\n".format(number_of_all_clients_files)
        for client in clients:
            for file_ in clients[client]["files"]:
                fulllist_message += clients[client]["name"] + " " + file_ + '\n'

        fulllist_message += '\0'

        send_message(connection, fulllist_message)

        return converse(connection, client, incoming_buffer, "FULLLIST")

    elif command == 'OK' and own_previous_command in ["WELCOME", "FULLLIST"]:
        return incoming_buffer, "OK"

    else:
        # TODO
        # handle invalid commands
        print("error, invalid command")
        sys.exit(-1)


def client_thread(connection, address):
    """
    connection : connection socket
    address : (IP_address, port)
    """

    # start with an empty incoming messages buffer
    incoming_buffer = ""
    own_previous_command = ""

    while True:
        incoming = connection.recv(4096)
        if len(incoming) == 0:
            break
        else:
            incoming_buffer += incoming

        incoming_buffer, own_previous_command = converse(connection, address, incoming_buffer, own_previous_command)


def server():
    global configuration_file
    global configuration
    global clients_file
    global clients

    configuration_file = "configuration.json"
    clients_file = "clients.json"

    if os.path.isfile(configuration_file):
        configuration = json_load(configuration_file)
    else:
        configuration["host"] = "localhost"
        configuration["port"] = 5000
        configuration['max_id_offset'] = 0
        json_save(configuration_file, configuration)
    # DEBUG
    print("configuration:")
    print(configuration)
    print()


    if os.path.isfile(clients_file):
        clients = json_load(clients_file)
    else:
        json_save(clients_file, clients)
    # DEBUG
    print("clients:")
    print(clients)


    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('error, socket.socket')
        sys.exit(-1)

    host = configuration["host"]
    port = configuration["port"]

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


if __name__ == "__main__":
    server()
