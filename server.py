#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
# {client_id: {name: name, files: [shared files], listening_IP_address: listening_IP_address, listening_port: listening_port}}
clients = {}

# {(IP_address, port): client_id}
connected_clients = {}


def sigint_handler(signal, frame):
    # cli_output
    print()
    logging.info("CTRL-C received, exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)


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

    logging.info("message received: " + str(message))

    lines = message.split("\n")
    fields = lines[0].split()
    command = fields[0]

    if command == "HELLO":
        client_id = fields[1]
        if client_id == "-":
            configuration["max_id_offset"] += 1
            json_save(configuration_file, configuration)
            client_id = "user_{0:0>4}".format(configuration["max_id_offset"])

            clients[client_id] = {"name": "", "files": [], "listening_ip": "", "listening_port": None}
            json_save(clients_file, clients)

        connected_clients[client] = client_id

        logging.debug("connected_clients: " + str(connected_clients))

        send_message(connection, "WELCOME " + client_id + "\n\0")
        return converse(connection, client, incoming_buffer, "WELCOME")

    elif command == "NAME":
        clients[connected_clients[client]]["name"] = fields[1]
        json_save(clients_file, clients)
        send_message(connection, "OK\n\0")

        logging.debug("clients: " + str(clients))

        return incoming_buffer, "OK"

    elif command == "LISTENING":
        clients[connected_clients[client]]["listening_ip"] = fields[1]
        clients[connected_clients[client]]["listening_port"] = fields[2]
        json_save(clients_file, clients)

        logging.debug("clients: " + str(clients))

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
        send_message(connection, "OK\n\0")
        return incoming_buffer, "OK"

    elif command == "SENDLIST":
        number_of_all_clients_files = 0
        for client in clients:
            number_of_all_clients_files += len(clients[client]["files"])
        fulllist_message = "FULLLIST {}\n".format(number_of_all_clients_files)
        for client in clients:
            for file_ in clients[client]["files"]:
                fulllist_message += clients[client]["name"] + " " + file_ + "\n"

        fulllist_message += "\0"

        send_message(connection, fulllist_message)

        return converse(connection, client, incoming_buffer, "FULLLIST")

    elif command == "WHERE":
        peer = fields[1]

        if peer in [value["name"] for value in clients.values()]:
            for peer_id in clients:
                if peer == clients[peer_id]["name"]:
                    peer_ip = clients[peer]["listening_ip"]
                    peer_port = clients[peer]["listening_port"]

            at_message = "AT {} {}\n\0".format(peer_ip, peer_port)
            send_message(connection, at_message)

            return incoming_buffer, "WHERE"
        else:
            send_message(connection, "ERROR\n\0")
            sys.exit(-1)

    elif command == "OK" and own_previous_command in ["WELCOME", "FULLLIST"]:
        return incoming_buffer, "OK"

    elif command == "ERROR":
        logging.warning("ERROR message received, exiting")
        sys.exit(-1)

    else:
        # TODO
        # handle invalid commands
        logging.warning('an invalid command was received: "{}"'.format(command))
        sys.exit(-1)


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
        console.setLevel(logging.DEBUG)
    else:
        console.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] (%(threadName)s) %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)

    configuration_file = "configuration.json"
    clients_file = "clients.json"

    if os.path.isfile(configuration_file):
        configuration = json_load(configuration_file)
    else:
        configuration["host"] = "localhost"
        configuration["port"] = 5000
        configuration["max_id_offset"] = 0
        json_save(configuration_file, configuration)

    logging.debug("configuration: " + str(configuration))


    if os.path.isfile(clients_file):
        clients = json_load(clients_file)
    else:
        json_save(clients_file, clients)

    logging.debug("clients: " + str(clients))


    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logging.error("socket.socket error")
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
            # TODO
            # this will be an error in production, i.e. the port must be specific
            logging.debug("port {} in use, trying the next one".format(port))
            port += 1

    # listen for incoming connections
    server_socket.listen(5)
    # cli_output
    logging.info("server listening on {}:{}".format(host, str(port)))

    # handle incoming client connections
    client_counter = 0
    while True:
        connection, address = server_socket.accept()
        # cli_output
        logging.info("a client connected from {}:{}".format(address[0], str(address[1])))

        client_thread = Thread(name="client {}".format(client_counter),
                target=client_function, args=(connection, address))
        # TODO
        # handle differently, terminate gracefully
        client_thread.daemon = True
        client_thread.start()

        client_counter += 1


if __name__ == "__main__":
    main()
