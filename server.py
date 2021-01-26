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
import random
import argparse
import errno
import os
import signal
import logzero
import atexit
import time
import sys
from logzero import logger

queueSize = 5

# This function iterates over the max size of the set array
# and it appends the randomly selected number from the pool array
# to the set array
def settingNumbers(poolArray, 
                  setArray, max):
    for i in range(max):
        random.shuffle(poolArray)
        num = random.choice(poolArray) # randomly choose a number from the pool array
        setArray.append(poolArray.pop(poolArray.index(num)))
    setArray.sort()

# This function stores the set of numbers to the ticket array
# and returns that array
def lottoPick(choice, numberOfTickets):
    if choice == 'max':
        ticketArray = []
        for i in range(numberOfTickets): # loop for the amount of tickets to be generated
            tmpArray = []
            for x in range(3):  # loop for the amount of sets of numbers in 1 ticket
                setArray = []
                arr = [int(x) for x in range(1, 51)] # pool array
                settingNumbers(arr, setArray, 7)
                tmpArray.append(setArray)
            ticketArray.append(tmpArray)
    elif choice == '649':
        ticketArray = []                      # array to store total tickets generated
        for i in range(numberOfTickets):
            tmpArray = []                     # temporary array to store set of numbers
            arr = [int(x) for x in range(1,50)]
            settingNumbers(arr, tmpArray, 6)
            ticketArray.append(tmpArray)
    else:
        ticketArray = []
        for i in range(numberOfTickets):
            tmpArray = []
            arr = [int(x) for x in range(1,50)]
            settingNumbers(arr, tmpArray, 5)

            grandNumber = [int(a) for a in range(1,8)] # grand number array
            tmpArray.append(random.choice(grandNumber))
            ticketArray.append(tmpArray)
    return ticketArray

# format the list and convert it into a string before passing data to client
def formatTickets(lottoType, array):
    str = ""
    
    if lottoType == 'max':
        str = "Lotto Max Ticket(s):\n"
    elif lottoType == '649':
        str = "Lotto 649 Ticket(s):\n"
    else:
        str = 'Daily Grand Ticket(s):\n'

    if lottoType == 'max': 
        for index, i in enumerate(array):
            str += "Ticket #{}: {}".format(index + 1, "\n")
            for x in i:
                str += "{}{}".format(x, "\n")
            str += "\n"
    else:
        for i in range(len(array)):
            str += "Ticket #{}: {}{}".format(i + 1, "\n", array[i])
            str += "\n"

    return str

def signalHandler(signalNum, frame):
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
        except OSError:
            return
        if pid == 0:
            return

def generateLotto(amountOfTickets, lottoType, socketConnection):
    lottoTickets = lottoPick(lottoType,  int(amountOfTickets))
    stringForTickets = formatTickets(lottoType,  lottoTickets)
    socketConnection.sendall(bytes(stringForTickets, "utf-8"))

def setupSwitches():
    parser = argparse.ArgumentParser(description='Daemon')

    args = parser.add_mutually_exclusive_group(required=True)
    args.add_argument('-start', action='store_const', dest='arg', 
    const='start',help='Start')
    args.add_argument('-stop', action='store_const', dest='arg', 
    const='stop',help='Stop')

    switches = parser.parse_args()

    return switches

def child():
    logger.info(f"CHILD: {os.getpid()} {childWrites}")

def parent():
    logger.info( f"PARENT: {os.getpid()} is logging")
    
def daemonize(pidfile, *, stdin='/dev/null',
                          stdout = '/dev/null',
                          stderr='/dev/null'):

    if os.path.exists(pidfile):
        raise RuntimeError("Already running")
        
    #first fork
    try:
        if os.fork() > 0:
            raise SystemExit(0)
    except OSError as e:
        raise RuntimeError("fork #1 failed")
        
    os.chdir('/')
    os.umask(0)
    os.setsid()
    id = 1000
    os.setuid(id)
    os.setgid(id)

    #second fork
    try:
        if os.fork() > 0:
            raise SystemExit(0)
    except OSError as e:
        raise RuntimeError("fork #2 failed")
        
    #flush i/o buffers
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open(stdin, 'rb', 0) as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(stdout, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(stderr, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stderr.fileno())

    with open(pidfile, 'w') as f:
        print(os.getpid(), file = f)

    # arrange to have the pid file removed on exit/signal
    atexit.register(lambda: os.remove(pidfile))
    
        # signal handler for termination
    def sigterm_handler(signo, frame):
        raise SystemExit(1)
            
    signal.signal(signal.SIGTERM, sigterm_handler)


# setup the connection from daemon to clients
def setupSocket():
    try:
            #switches = setupSwitches()
            serverAddress = ('', 8080, 0, 0)
            socketObject = socket(AF_INET6, SOCK_STREAM)
            socketObject.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            socketObject.bind(serverAddress)
            socketObject.listen(queueSize)
            signal.signal(signal.SIGCHLD, signalHandler)
            while True:
                try:
                    socketConnection, clientAddress = socketObject.accept()
                except IOError as e:
                    errorCode, msg = e.args
                    # restart 'accept' if it was interrupted
                    if errorCode == errno.EINTR:
                        continue
                    else:
                        raise
                pid = os.fork()
                if pid == 0:
                    try:
                        child()
                        socketObject.close()
                        argsString = socketConnection.recv(128)
                        argsArray = argsString.decode().split('|')
                        amountOfTickets = argsArray[0]
                        lottoType = argsArray[1]
                        
                        generateLotto(amountOfTickets, lottoType, socketConnection)
                        socketObject.close()
                        os._exit(0)
                    except ValueError as val:
                        print(val)
                else:
                    parent()
                    socketConnection.close()
    except Exception as err:
        print(f"Exception: {err}")

def daemonAlive():
    if os.fork() == 0:
        sys.stdout.write(f'Daemon started with pid {os.getpid()}\n')
        while True:
            sys.stdout.write(f'Daemon Alive! {time.ctime()}\n')
            time.sleep(10)

if __name__ == '__main__':
    switches = setupSwitches()
    
    # su - then mkdir daemonDir
    PIDFILE = '/var/run/daemonDir/daemon.pid'
    result = str(switches.arg)
    
    if result == 'start':
        try:
            daemonize(PIDFILE, stdout='/tmp/daemon.log', stderr='/tmp/dameon.log')
            # Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
            logzero.logfile("/tmp/rotating-logfile.log", maxBytes=1e6, backupCount=3,disableStderrLogger=True)
            childWrites = "And now, for something completely different"
            daemonPID=os.getpid()
            logger.info(f"Started {daemonPID}")
            daemonAlive()
            setupSocket() 

        except RuntimeError as e:
            print(e, file=sys.stderr)
            raise SystemExit(1)
    elif result == 'stop':
        if os.path.exists(PIDFILE):
            with open(PIDFILE) as f:
                os.kill(int(f.read()), signal.SIGTERM)
        else:
            print('Not running', file=sys.stderr)
            raise SystemExit(1)