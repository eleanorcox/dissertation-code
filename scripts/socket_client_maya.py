#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import socket
import json
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect the socket to the port where Maya is listening
maya_address = ("localhost", 12345)
print "connecting to %s port %s" % maya_address
sock.connect(maya_address)

try:
    req_type = "PUT"
    #command = "polyCube -w 1 -h 1 -d 1 -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;"
    command = "[1 2 3 4 5 6 7 8 9 10]"
    json_request = json.dumps({"RequestType": req_type, "Y_Output": command})

    sock.sendall(json_request)
    # MAYBE better to use send but fix this l8r

    data = sock.recv(4096)
    print "received %s" % data

finally:
    print "closing socket"
    sock.close()
