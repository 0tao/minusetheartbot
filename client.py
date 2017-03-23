#!/usr/bin/env python
# This client program is used for testing the main.py by manually typing in the message
import tty
import sys
from socket import *

x = 0

serverName = '10.209.11.115'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))
while x != "exit": # ESC
    x = raw_input("Input: ")
    clientSocket.send(x)
    serverStatus = clientSocket.recv(1024)
    print 'Server:', serverStatus

clientSocket.close()
termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)    
