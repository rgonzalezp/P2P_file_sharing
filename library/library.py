#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Dimitrios Paraschas
# 1562
# Dimitrios Greasidis
# 1624
# Stefanos Papanastasiou
# 1608


from __future__ import print_function
import sys
import logging
import json
import socket

def sigint_handler(signal, frame):
    """
    handle keyboard interrupts (CTRL-C)
    """

    # cli_output
    print()
    logging.info("CTRL-C received, exiting")
    sys.exit(0)


def send_message(connection, message):
    try:
        connection.sendall(message)
    except socket.error:
        logging.error("error, send_message")
        sys.exit(-1)

    logging.info("message sent: " + message)


def json_load(json_file):
    with open(json_file, "rb") as file_:
        json_ = json.load(file_)

    return json_


def json_save(json_file, json_):
    with open(json_file, "wb+") as file_:
        json.dump(json_, file_, sort_keys=True, indent=4, separators=(",", ": "))


if __name__ == "__main__":
    print("This file is meant to be imported, not run.")
