import sys
import socket
from lt import encode, decode
import argparse

"""
The running scripts as the client and server.
Because we need the lt-code library which runs only under python3.
"""


def run_client(args):
    pass


def run_server(args):
    pass


def parse_cli(args):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='command', dest='command')

    # client
    client_parser = subparsers.add_parser('client', help='run the client')

    # server
    server_parser = subparsers.add_parser('server', help='run the server')

    return parser.parse_args(args)


def main():
    args = parse_cli(sys.argv[1:])
    command = args.command
    if command == 'client':
        run_client(args)
    elif command == 'server':
        run_server(args)
    else:
        print('Unknown command')


if __name__ == '__main__':
    main()
