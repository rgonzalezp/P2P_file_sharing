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


#DEBUG = True
DEBUG = False


configuration_file = ""
configuration = {}


def sigint_handler(signal, frame):
    # cli_output
    print()
    logging.info("CTRL-C received, exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)


def converse(server, incoming_buffer, own_previous_command):
    global configuration

    if "\0" not in incoming_buffer:
        incoming_buffer += server.recv(4096)
        return converse(server, incoming_buffer, own_previous_command)
    else:
        index = incoming_buffer.index("\0")
        message = incoming_buffer[0:index-1]
        incoming_buffer = incoming_buffer[index+1:]

    logging.info("message received: " + message)

    lines = message.split("\n")
    fields = lines[0].split()
    command = fields[0]

    if command == "WELCOME":
        id_ = fields[1]
        configuration["id"] = id_
        json_save(configuration_file, configuration)
        send_message(server, "OK\n\0")
        return incoming_buffer

    elif command == "FULLLIST" and own_previous_command == "SENDLIST":
        number_of_files = int(fields[1])

        if number_of_files != (len(lines) - 1):
            logging.warning("invalid FULLLIST message, wrong number of files")
            # TODO
            # send an error message, handle it in the server
            reply = "ERROR\n\0"
        else:
            # cli_output
            print()
            print("full list of clients' files")
            for line in lines[1:]:
                print(line)
            send_message(server, "OK\n\0")

    elif command == "OK" and own_previous_command in ("LIST", "NAME"):
        return incoming_buffer

    else:
        # TODO
        # handle invalid commands
        logging.warning('an invalid command was received: "{}"'.format(command))
        sys.exit(-1)


def connection_init(address):
    ip, port = address

    try:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logging.error("socket.socket error")
        sys.exit(-1)

    # TODO
    # replace with the equivalent code without using an offset
    while True:
        try:
            connection.connect( (ip, port) )
            # cli_output
            logging.info("connected to server {}:{}".format(ip, port))
            break
        except socket.error:
            # TODO
            # this will be an error in production, i.e. the port must be specific
            logging.debug("failed to connect to port {}, trying the next one".format(port))
            port += 1

    return connection


def get_name(configuration_file, configuration):
    # cli_output
    print('Specify a user name (press enter for the default "{}"): '.format(configuration["id"]))
    name = raw_input()

    if name == "":
        name = configuration["id"]

    configuration["name"] = name
    json_save(configuration_file, configuration)


def peer_function(connection, address):
    """
    connection : connection socket
    address : (IP_address, port)
    """
    pass


def listen(listening_ip, listening_port):
    try:
        listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logging.error("socket.socket error")
        sys.exit(-1)

    # TODO
    # replace with the equivalent code without using an offset
    while True:
        try:
            listening_socket.bind( (listening_ip, listening_port) )
            break
        except socket.error:
            # TODO
            # this will be an error in production, i.e. the port must be specific
            logging.debug("port {} in use, trying the next one".format(listening_port))
            listening_port += 1

    # listen for incoming connections
    listening_socket.listen(5)
    # cli_output
    logging.info("client listening on {}:{}".format(listening_ip, str(listening_port)))


    # TODO
    # NEXT
    # send the listening_ip and listening_port to the server via the main thread


    # handle incoming peer connections
    peer_counter = 0
    while True:
        connection, address = listening_socket.accept()
        # cli_output
        logging.info("a peer connected from {}:{}".format(address[0], str(address[1])))

        peer_thread = Thread(name="peer {}".format(peer_counter),
                target=peer_function, args=(connection, address))
        # TODO
        # handle differently, terminate gracefully
        peer_thread.daemon = True
        peer_thread.start()

        peer_counter += 1


def main():
    global configuration
    global configuration_file

    # check if an argument was passed
    if len(sys.argv) < 2:
        # cli_output
        print("please pass the working directory")
        sys.exit(-1)

    argument = sys.argv[1]

    configuration = {}

    working_directory = argument

    logging.basicConfig(level=logging.DEBUG,
            format="[%(levelname)s] (%(threadName)s) %(message)s",
            filename=working_directory + "/client.log",
            filemode="w")
    console = logging.StreamHandler()
    if DEBUG:
        console.setLevel(logging.DEBUG)
    else:
        console.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] (%(threadName)s) %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)


    configuration_file = working_directory + "/configuration.json"

    if os.path.isfile(configuration_file):
        configuration = json_load(configuration_file)
    else:
        configuration["server_host"] = "localhost"
        configuration["server_port"] = 5000
        configuration["listening_ip"] = "localhost"
        configuration["listening_port"] = 10000 + (int(argument[-4:]) * 1000)
        configuration["id"] = "-"
        configuration["share_directory"] = "share"
        json_save(configuration_file, configuration)

    logging.debug("configuration: " + str(configuration))

    share_directory = working_directory + "/" + configuration["share_directory"]
    files_list = [ file_ for file_ in os.listdir(share_directory) if os.path.isfile(os.path.join(share_directory, file_)) ]

    logging.debug("files_list: " + str(files_list))

    server_address = (configuration["server_host"], configuration["server_port"])
    server = connection_init(server_address)


    # start with an empty incoming message buffer
    incoming_buffer = ""


    # send HEY command
    ############################################################################
    send_message(server, "HEY " + configuration["id"] + "\n\0")

    incoming_buffer = converse(server, incoming_buffer, "HEY")


    # send NAME command
    ############################################################################
    if "name" not in configuration:
        get_name(configuration_file, configuration)
    send_message(server, "NAME " + configuration["name"] + "\n\0")

    converse(server, incoming_buffer, "NAME")


    # send LISTENING command
    ############################################################################
    listening_ip = configuration["listening_ip"]
    listening_port = configuration["listening_port"]

    # spawn listening thread
    listening_thread = Thread(name="listening thread", target=listen,
            args=(listening_ip, listening_port))
    # TODO
    # handle differently, terminate gracefully
    listening_thread.daemon = True
    listening_thread.start()


    # send LIST command
    ############################################################################
    list_message = "LIST {}\n".format(len(files_list))
    for file_ in files_list:
        list_message += file_ + "\n"
    list_message += "\0"
    send_message(server, list_message)

    converse(server, incoming_buffer, "LIST")


     # send SENDLIST command
    ############################################################################
    send_message(server, "SENDLIST " + "\n\0")

    converse(server, incoming_buffer, "SENDLIST")


    # options menu/loop
    ############################################################################
    while True:
        print()
        print("options:")
        print("1: SENDLIST / s : request the list of clients and shared files")
        print("2: QUIT / q : exit the program")

        option = raw_input()
        if option in ["1", "s", "S", "sendlist", "SENDLIST"]:
            send_message(server, "SENDLIST " + "\n\0")

            converse(server, incoming_buffer, "SENDLIST")

        elif option in ["2", "q", "Q", "quit", "QUIT"]:
            sys.exit(0)

        else:
            print("invalid option, try again")


if __name__ == "__main__":
    main()
