#################################################################
# Testing socket networking. The CLIENT.
# For this, Maya is the server, using a commandPort at address
# localhost:12345.
#################################################################
import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
maya_address = ('localhost', 12345)
print 'connecting to %s port %s' % maya_address
sock.connect(maya_address)

try:
    # Send data. Creates a cube in the scene
    command = 'polyCube -w 1 -h 1 -d 1 -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;'
    print 'sending "%s"' % command
    sock.sendall(command)

    data = sock.recv(1024)
    print 'received "%s"' % data

finally:
    print 'closing socket'
    sock.close()
