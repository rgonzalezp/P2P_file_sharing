#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Dimitrios Paraschas
# 1562
# Dimitrios Greasidis
# 1624
# Stefanos Papanastasiou
# 1608


from __future__ import print_function
import logging
import os
import signal
import socket
import sys
from threading import Thread

from library.library import json_load
from library.library import json_save
from library.library import send_message


DEBUG = True
#DEBUG = False


configuration_file = ""
configuration = {}

clients_file = ""
# {username: {files: [shared files], listening_IP_address: listening_IP_address, listening_port: listening_port}}
clients = {}

# {(IP_address, port): username}
connected_clients = {}

# handle ctrl-c
def sigint_handler(signal, frame):
    # cli_output
    print()
    logging.info("CTRL-C received, exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)

# Handle messages, uses recursion if there are more incoming commands
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
    # info message
    logging.info("message received: " + str(message))

    # split message into lines for easier handle
    lines = message.split("\n")
    fields = lines[0].split()
    command = fields[0]

    if command == "HELLO":
        # checks if there is a username after the command or not
        if len(fields) == 1:
            configuration["username_offset"] += 1
            json_save(configuration_file, configuration)

            # create available username for the new client
            username = "u{}".format(configuration["username_offset"])
            # send answer to client and call converse recursively
            send_message(connection, "AVAILABLE " + username + "\n\0")
            return converse(connection, client, incoming_buffer, "AVAILABLE")
        else:
            username = fields[1]
            if username in clients:
                # save username at dictionary
                connected_clients[client] = username
                logging.debug("connected_clients: " + str(connected_clients))

                # send message WELCOME to client and call converse recursively
                send_message(connection, "WELCOME " + username + "\n\0")
                return converse(connection, client, incoming_buffer, "WELCOME")
            else:
                # otherwise send ERROR to client, dont need recursion here cause
                # we dont wait for an incoming command from the client
                send_message(connection, "ERROR\n\0")
                return incoming_buffer, "ERROR"

    elif command == "IWANT":
        username = fields[1]
        # checks if username is valid
        if username in clients:
            configuration["username_offset"] += 1
            json_save(configuration_file, configuration)

            username = "u{}".format(configuration["username_offset"])
            # send answer to client and call converse recursively
            send_message(connection, "AVAILABLE " + username + "\n\0")
            return converse(connection, client, incoming_buffer, "AVAILABLE")
        else:
            clients[username] = {"files": [], "listening_ip": "", "listening_port": None}
            json_save(clients_file, clients)

            logging.debug("clients: " + str(clients))

            connected_clients[client] = username
            logging.debug("connected_clients: " + str(connected_clients))
            # send answer to client
            send_message(connection, "WELCOME " + username + "\n\0")

            return incoming_buffer, "WELCOME"

    elif command == "LISTENING":
        clients[connected_clients[client]]["listening_ip"] = fields[1]
        clients[connected_clients[client]]["listening_port"] = fields[2]
        json_save(clients_file, clients)

        logging.debug("clients: " + str(clients))
        # send answer to client
        send_message(connection, "OK\n\0")
        return incoming_buffer, "OK"

    elif command == "LIST":
        number_of_files = int(fields[1])
        if number_of_files != (len(lines) - 1):
            logging.warning("invalid LIST message, wrong number of files")
            send_message(connection, "ERROR\n\0")
            sys.exit(-1)
        else:
            clients[connected_clients[client]]["files"] = lines[1:]
            json_save(clients_file, clients)

        # send answer to client and call converse recursively
        send_message(connection, "OK\n\0")
        return incoming_buffer, "OK"

    elif command == "SENDLIST":
        number_of_all_clients_files = 0
        for client_ in clients:
            number_of_all_clients_files += len(clients[client_]["files"])
        fulllist_message = "FULLLIST {}\n".format(number_of_all_clients_files)
        for client_ in clients:
            for file_ in clients[client_]["files"]:
                fulllist_message += client_ + " " + file_ + "\n"

        fulllist_message += "\0"
        # sends list of clients and their files to the client that requested them
        send_message(connection, fulllist_message)

        return converse(connection, client, incoming_buffer, "FULLLIST")

    elif command == "WHERE":
        peer = fields[1]
        # searche for peer client in our dictionary
        # if valid, we sent to client the ip and port of him
        if peer in clients:
            # get from dictionary ip and port
            peer_ip = clients[peer]["listening_ip"]
            peer_port = clients[peer]["listening_port"]

            # send message to client with ip and port of the client that 
            # he wants to connect
            at_message = "AT {} {}\n\0".format(peer_ip, peer_port)
            send_message(connection, at_message)
            return incoming_buffer, "WHERE"
        else:
            send_message(connection, "UNKNOWN\n\0")
            return incoming_buffer, "UNKNOWN"

    elif command == "ERROR":
        logging.warning("ERROR message received, exiting")
        sys.exit(-1)

    else:
        # TODO
        # handle invalid commands
        logging.warning('an invalid command was received: "{}"'.format(command))
        sys.exit(-1)

# Receives messages and calls function converse to handle them
def client_function(connection, address):
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


def main():
    global configuration_file
    global configuration
    global clients_file
    global clients

    logging.basicConfig(level=logging.DEBUG,
            format="[%(levelname)s] (%(threadName)s) %(message)s",
            filename="server.log",
            filemode="w")
    console = logging.StreamHandler()
    if DEBUG:
        # Debug message
        console.setLevel(logging.DEBUG)
    else:
        # info message
        console.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] (%(threadName)s) %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)
    # create json files to save dictionaries
    configuration_file = "configuration.json"
    clients_file = "clients.json"
    # load from json file if exists, else create and initialize it
    if os.path.isfile(configuration_file):
        configuration = json_load(configuration_file)
    else:
        configuration["host"] = "localhost"
        configuration["port"] = 45000
        configuration["username_offset"] = 0
        json_save(configuration_file, configuration)

    logging.debug("configuration: " + str(configuration))

    # load list of clients from data base(json file) and save
    if os.path.isfile(clients_file):
        clients = json_load(clients_file)
    else:
        json_save(clients_file, clients)

    logging.debug("clients: " + str(clients))

    # create socket for connection
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logging.error("socket.socket error")
        sys.exit(-1)

    host = configuration["host"]
    port = configuration["port"]
    # bind socket
    try:
        server_socket.bind( (host, port) )
    except socket.error:
        logging.error("port {} in use, exiting".format(port))
        sys.exit(-1)

    # listen for incoming connections
    server_socket.listen(5)
    # output message
    logging.info("server listening on {}:{}".format(host, str(port)))

    # handle incoming client connections
    client_counter = 0
    while True:
        connection, address = server_socket.accept()
        # output message
        logging.info("a client connected from {}:{}".format(address[0], str(address[1])))

        # create thread and call client_function throught it
        client_thread = Thread(name="client {}".format(client_counter),
                target=client_function, args=(connection, address))

        client_thread.daemon = True
        client_thread.start()

        client_counter += 1


if __name__ == "__main__":
    main()
