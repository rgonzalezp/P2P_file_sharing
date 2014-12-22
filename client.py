#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import socket
import sys

from library.library import configuration_load
from library.library import configuration_save


def create_message(command, arguments):
    if command == "HEY":
        id_ = arguments
        message = "HEY " + id_ + "\n\0"

    elif command == "LIST":
        files_list = arguments
        message = "LIST\n"
        for file_ in files_list:
            message += file_ + '\n'
        message += '\0'

    elif command == "OK":
        message = "OK\n\0"

    else:
        print("error, wrong message type")
        sys.exit()

    # DEBUG
    print("created message:")
    print(message)

    return message


def send_message(socket_, message):
    try:
        socket_.sendall(message)
    except socket.error:
        print('error, socket.sendall')
        sys.exit()


def connection_init(address):
    ip, port = address

    try:
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('error, socket.socket')
        sys.exit()

    # TODO
    # replace with the equivalent code without using an offset
    while True:
        try:
            socket_.connect( (ip, port) )
            # DEBUG
            print("connected to peer {}:{}".format(ip, port))
            print()
            break
        except socket.error:
            # DEBUG
            print("failed to connect to port {}, trying the next one".format(port))
            port += 1

    return socket_


def get_name(configuration_file, configuration):
    print('Specify a user name (press enter for default "{}"): '.format(configuration["id"]))
    name = raw_input()

    if name == "":
        name = configuration["id"]

    configuration['name'] = name
    configuration_save(configuration_file, configuration)


def client():
    # check if an argument was passed
    if len(sys.argv) < 2:
        print("please pass one of the following arguments: {1, 2, 3}")
        sys.exit()

    argument = sys.argv[1]

    configuration = {}

    working_directory = argument

    configuration_file = working_directory + "/configuration.json"

    if os.path.isfile(configuration_file):
        configuration = configuration_load(configuration_file)
    else:
        configuration["server_host"] = "localhost"
        configuration["server_port"] = 5000
        configuration["listening_port"] = 10000 + (int(argument) * 1000)
        configuration["id"] = "-"
        configuration["share_directory"] = "share"
        configuration_save(configuration_file, configuration)
    # DEBUG
    print("configuration:")
    print(configuration)
    print()

    share_directory = working_directory + "/" + configuration["share_directory"]
    files_list = [ file_ for file_ in os.listdir(share_directory) if os.path.isfile(os.path.join(share_directory, file_)) ]
    # DEBUG
    print("files_list:")
    print(files_list)
    print()

    server_address = (configuration["server_host"], configuration["server_port"])
    server_socket = connection_init(server_address)

    send_message(server_socket, create_message("HEY", configuration["id"]))

    send_message(server_socket, create_message("LIST", files_list))

    if "name" not in configuration:
        get_name(configuration_file, configuration)

    send_message(server_socket, create_message("NAME", configuration["name"]))


if __name__ == "__main__":
    client()
