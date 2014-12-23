#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import socket


def send_message(connection, message):
    try:
        connection.sendall(message)
    except socket.error:
        print('error, send_message')
        sys.exit(-1)
    # DEBUG
    print("message sent:")
    print(message)


def configuration_load(configuration_file):
    with open(configuration_file, 'rb') as file_:
        configuration = json.load(file_)

    return configuration


def configuration_save(configuration_file, configuration):
    with open(configuration_file, 'wb+') as file_:
        json.dump(configuration, file_, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    print("This file is meant to be imported, not run.")
