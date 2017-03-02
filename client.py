#!/usr/bin/env python
import tty
import sys
import termios
from socket import *

orig_settings = termios.tcgetattr(sys.stdin)
tty.setraw(sys.stdin)
x = 0

serverName = '10.209.11.115'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))
while x != chr(27): # ESC
      x=sys.stdin.read(1)[0]
      clientSocket.send(x)
      serverStatus = clientSocket.recv(1024)
      print 'Server:', serverStatus

clientSocket.close()
termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)    
