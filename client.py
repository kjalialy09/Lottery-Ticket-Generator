#!/usr/bin/env python3 
#==============================================================================
 #   Assignment:  Milestone 3
 #
 #       Author:  Kyle Alialy
 #     Language:  Python3
 #
 #   To Compile:  n/a
 #
 #        Class:  DPI912 - Python for Programmers: Sockets and Security 
 #    Professor:  Harvey Kaduri
 #     Due Date:  November 3, 2020, 11:59PM
 #    Submitted:  November 6, 2020
 #
 #-----------------------------------------------------------------------------
 #
 #  Description:  non-blocking networked lottery ticket generator over TCP/IP handling high concurrency
 #                daemonized daemon
 # 
 #
 #Collaboration:  Used Python Cookbook for reference (Chapter 12)
 #
 #        Input:  It requires command line argument on which lottery game
 #                to generated and the amount of tickets to be generated, maximum number of connections.
 #                maximum number of clients and the filename to store the tickets generated into
 #
 #       Output:  Displays the lottery tickets on the screen and also,
 #                write the output in a text file
 #
 #    Algorithm:  To generate the set of numbers for the ticket, pool
 #                a specific amount of numbers (depending on the lotto game)
 #                for the array, iterate through the total size of the set,
 #                shuffle the pool array, randomly choose a number from the pool,
 #                and add the number to the set.
 #
 #   Required Features Not Included:  n/a
 #
 #   Known Bugs: when creating daemon.pid file in /var/run, have to do su - and create dir
 #   in the directory which allows the server code to create daemon.pid file
 #      
 #
 #   Classification: A
 #
#==============================================================================
from socket import *
import argparse
import errno
import os
import sys
import random
import signal

# validates the number of tickets the user want
def validateNumber(x):
    x = int(x)
    if x < 1:
        raise argparse.ArgumentTypeError("Minimum number of tickets is 1")
    return x

# setup the switches passed through the arguments and return the switches for use in main()
def setupSwitches():
    parser = argparse.ArgumentParser(description='MS1 - Networked Lottery Ticket Generator over TCP/IP')
    parser.add_argument('-c', type=validateNumber, help="Number of lotto tickets to generate",
    required=True)

    parser.add_argument('-ip', type=str, help="IP address (IPV6) | 'debian10vm' (from different machine), '::1' (localhost)",
    required=True)

    parser.add_argument('-con', type=int, default=24, help="Maximum number of connections per client.",required=True)
    parser.add_argument('-n', type=int, default=1, help="Maximum number of clients.",required=False)
    
    parser.add_argument('-file', type=str,  help="Name of the file to save the tickets generated",required=True)
    
    lottoTypes = parser.add_mutually_exclusive_group(required=True)
    lottoTypes.add_argument('-649', action='store_const', dest='lottery', 
    const='649',help='Lotto 649 | Six numbers from 1 to 49')
    lottoTypes.add_argument('-max', action='store_const', dest='lottery', 
    const='max',help='Lotto Max | Seven numbers from 1 to 50 \
        (Generate 3 sets of numbers)')
    lottoTypes.add_argument('-g', action='store_const', dest='lottery', 
    const='g',help='Daily Grand | 5 main numbers from 1 to 49, \
        and one GRAND NUMBER from 1 to 7')

    switches = parser.parse_args()

    return switches

def setupSocket():
    
    if len(sys.argv) > 6 or sys.argv[1] == "-h":
        switches = setupSwitches()
    else:
        print(len(sys.argv))
        sys.exit()
    
    userIdentifier = switches.file
    maxConnection = switches.con
    maxClients = switches.n
    sockets = []
    counter = 0;
    for clientNumber in range(maxClients):
        try:
            pid = os.fork()
        except OSError:
            sys.stderr.write("Could not create a child process\n")
            continue

        if pid == 0:
            for connectionNum in range(maxConnection):
                setBufferSz = 500
                num = str(switches.c)
                lottoType = switches.lottery
                socketObject = socket(AF_INET6, SOCK_STREAM, 0)
                socketObject.connect((switches.ip, 8080, 0, 0))
                sockets.append(socketObject)

                valid = False
                while not valid:
                    if userIdentifier:
                        valid = True
                        argsString = f"{num}|{lottoType}"
                        socketObject.send(bytes(argsString, "utf-8"))

                        tickets = socketObject.recv(setBufferSz * int(num))
                        print(f"\n====Client #{os.getpid()}====")
                        print(tickets.decode())
                        try:
                            counter += 1
                            tmp = f"{userIdentifier}-{os.getpid()}"
                            fileHandler = open(f"{tmp}.txt", "w")
                            fileHandler.write(tickets.decode())
                            print(f"The tickets generated are also in {tmp}.txt file.\nGoodbye!\n")
                        except IOError as e:
                            print("An exception has been caught: Unable to write file ", e)
                        except Exception as e:
                            print(e)
                        else:
                            fileHandler.close()
                        os._exit(0)
                    else:
                        print("ERROR: This prompt cannot be left blank. Please enter the name again.\n")

def main():
    setupSocket()

def signalHandler(signalNum, frame):
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
        except OSError:
            return
        if pid == 0:
            return

if __name__ == "__main__":
    main()
    signal.signal(signal.SIGCHLD, signalHandler);
    sys.exit()
