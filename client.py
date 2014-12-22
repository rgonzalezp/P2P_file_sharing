#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import socket
import sys
import time
import json


def create_message(message_type, arguments):
    if message_type == "HEY":
        id_ = arguments
        message = "HEY " + id_

    elif message_type == "LIST":
        files_list = arguments
        message = "LIST\n"
        for f in files_list:
            message += f + '\n'

    elif message_type == "OK":
        message = "OK"

    else:
        print("error, wrong message type")
        sys.exit()

    # DEBUG
    print("created message:")
    print(message)
    print()

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
            port += 1

    return socket_


def get_name(configuration_file, configuration):
    print('Specify a user name (press enter for default "{}"): '.format(configuration["id"]))
    name = raw_input()

    if name == "":
        name = configuration["id"]

    configuration['name'] = name
    configuration_save(configuration_file, configuration)


def configuration_load(configuration_file):
    with open(configuration_file, 'rb') as f:
        configuration = json.load(f)

    return configuration


def configuration_save(configuration_file, configuration):
    with open(configuration_file, 'wb+') as f:
        json.dump(configuration, f)


def client():
    # check if an argument was passed
    if len(sys.argv) < 2:
        print("please pass one of the arguments: {1, 2, 3}")
        sys.exit()

    argument = sys.argv[1]

    configuration = {}

    working_directory = argument
    # DEBUG
    print("working_directory:")
    print(working_directory)
    print()

    configuration_file = working_directory + "/configuration.json"

    if os.path.isfile(configuration_file):
        configuration = configuration_load(configuration_file)
        # DEBUG
        print("configuration:")
        print(configuration)
        print()
    else:
        configuration["server_host"] = "localhost"
        configuration["server_port"] = 5000
        configuration["listening_port"] = 10000 + (int(argument) * 1000)
        configuration["id"] = "-"
        configuration["name"] = "-"
        configuration["sharing_directory"] = working_directory + "/sharing"
        configuration_save(configuration_file, configuration)

    files_list = [ f for f in os.listdir(configuration["sharing_directory"]) if os.path.isfile(os.path.join(configuration["sharing_directory"], f)) ]
    # DEBUG
    print("files_list:")
    print(files_list)
    print()

    server_address = (configuration["server_host"], configuration["server_port"])
    server_socket = connection_init(server_address)

    send_message(server_socket, create_message("HEY", configuration["id"]))

    send_message(server_socket, create_message("LIST", files_list))

    get_name(configuration_file, configuration)
    send_message(server_socket, create_message("NAME", configuration["name"]))


if __name__ == "__main__":
    client()
