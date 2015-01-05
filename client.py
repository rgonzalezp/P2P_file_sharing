#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import logging
import os
import signal
import socket
import sys
import Queue
from threading import Thread

from library.library import json_load
from library.library import json_save
from library.library import send_message


DEBUG = True
#DEBUG = False


configuration_file = ""
configuration = {}
full_list_of_files = []


def sigint_handler(signal, frame):
    # cli_output
    print()
    logging.info("CTRL-C received, exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)


def converse(server, incoming_buffer, own_previous_command):
    global configuration
    global full_list_of_files

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
        return None, incoming_buffer

    elif command == "FULLLIST" and own_previous_command == "SENDLIST":
        number_of_files = int(fields[1])

        if number_of_files != (len(lines) - 1):
            logging.warning("invalid FULLLIST message, wrong number of files")
            send_message(server, "ERROR\n\0")
            sys.exit(-1)
        else:
            full_list_of_files = lines[1:]

            # cli_output
            print()
            print("full list of clients' files")
            for line in lines[1:]:
                print(line)
            send_message(server, "OK\n\0")

        return None, incoming_buffer

    elif command == "AT" and own_previous_command =="WHERE":
        peer_ip = fields[1]
        peer_port = int(fields[2])

        return (peer_ip, peer_port), incoming_buffer

    elif command == "OK" and own_previous_command in ("NAME", "LIST", "LISTENING"):
        return None, incoming_buffer

    elif command == "ERROR":
        logging.warning("ERROR message received, exiting")
        sys.exit(-1)

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
            logging.info("connected to server or peer {}:{}".format(ip, port))
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
    incoming_buffer = ""

    while "\0" not in incoming_buffer:
        incoming_buffer += connection.recv(4096)

    index = incoming_buffer.index("\0")
    message = incoming_buffer[0:index-1]
    incoming_buffer = incoming_buffer[index+1:]

    logging.info("message received: " + message)

    fields = message.split()
    command = fields[0]

    if command == "GIVE":
        file_ = fields[1]
        #read filesize
        file_size = os.stat(file_)
        send_message(connection, "TAKE {}\n\0".format(file_size))

        file_directory = open(file_,'rb')
        print('Sending....')
        file_buffer = file_directory.read(1024)
        while (file_buffer):
            print('Sending....')
            connection.send(file_buffer)
            file_buffer = file_directory.read(1024)
        #close to arxeio
        file_directory.close()
        print("Done Sending")
        #with open(file_, "rb") as file_:
        #   json_ = json.load(file_)
        #close to socket
        connection.close()

    elif command == "THANKS":
        pass
    else:
        print('ERROR')




def listen(listening_ip, listening_port, queue):
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

    # pass the listening_ip and listening_port to the main thread
    queue.put( (listening_ip, listening_port) )

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


def give_me(peer):
    print()
    print("file name:")
    file_ = raw_input()

    send_message(peer, "GIVE {}\n\0".format(file_))

    incoming_buffer = ""

    while "\0" not in incoming_buffer:
        incoming_buffer += peer.recv(4096)

    index = incoming_buffer.index("\0")
    message = incoming_buffer[0:index-1]
    incoming_buffer = incoming_buffer[index+1:]

    logging.info("message received: " + message)

    fields = message.split()
    command = fields[0]

    if command == "TAKE":
        file_size = fields[1]

        # get the file
        while len(incoming_buffer) < file_size:
            incoming_buffer += peer.recv(4096)

        while True:
            file_buffer = peer.recv(1024)
            while (file_buffer):
               print("Receiving...")
               file_.write(file_buffer)
               file_buffer = peer.recv(1024)
            file_.close()

        print("Done Receiving")
        send_message(peer, "THANKS\n\0")
        peer.close()

    elif command == "NOTEXIST":
        return

    else:
        # TODO
        # handle invalid commands
        logging.warning('an invalid command was received: "{}"'.format(command))
        sys.exit(-1)


def main():
    global configuration
    global configuration_file
    global full_list_of_files

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


    # send HELLO command
    ############################################################################
    send_message(server, "HELLO " + configuration["id"] + "\n\0")

    unneeded, incoming_buffer = converse(server, incoming_buffer, "HELLO")


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

    queue = Queue.Queue()

    # spawn listening thread
    listening_thread = Thread(name="ListeningThread", target=listen,
            args=(listening_ip, listening_port, queue))
    # TODO
    # handle differently, terminate gracefully
    listening_thread.daemon = True
    listening_thread.start()

    listening_ip, listening_port = queue.get()

    listening_message = "LISTENING {} {}\n\0".format(listening_ip, listening_port)
    send_message(server, listening_message)

    converse(server, incoming_buffer, "LISTENING")


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
        print("2: WHERE / w : request the IP address and port of the specified client")
        print("5: QUIT / q : exit the program")

        option = raw_input()
        if option in ["1", "s", "S", "sendlist", "SENDLIST"]:
            send_message(server, "SENDLIST " + "\n\0")

            converse(server, incoming_buffer, "SENDLIST")

        elif option in ["2", "w", "W", "where", "WHERE"]:
            print("Enter the name of the client:")

            while True:
                client = raw_input()

                if client == configuration["name"]:
                    print("{} is you, try again: ".format(client))
                    continue

                if client in [pair.split()[0] for pair in full_list_of_files]:
                    break

                print("{} is an invalid client name, try again: ".format(client))

            send_message(server, "WHERE " + client + "\n\0")

            (peer_ip, peer_port), incoming_buffer = converse(server, incoming_buffer, "WHEREs")

            peer = connection_init( (peer_ip, peer_port) )

            give_me(peer)

        elif option in ["5", "q", "Q", "quit", "QUIT"]:
            sys.exit(0)

        else:
            print("invalid option, try again")


if __name__ == "__main__":
    main()
