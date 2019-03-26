#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import numpy as np
import socket
import time
import json
import sys

# test_get = True
# test_put = False
#
# # Create a TCP/IP socket
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# maya_address = ("localhost", 12345)
# print "Connecting to %s port %s" % maya_address
# sock.connect(maya_address)
#
# req_type = "GET"
# json_request = json.dumps({"RequestType": req_type})
# sock.sendall(json_request)
# response = sock.recv(4096)
# print "Received %s" % response
# print "Closing socket to Maya"
# sock.close()
# json_response = json.loads(response)
#
# initial_X = createX(json_response)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
pfnn_address = ("localhost", 54321)
print "Connecting to %s port %s" % pfnn_address
sock.connect(pfnn_address)

json_request = json.dumps({"X": "x", "FullPath": "path", "Gait": "gait", "Frames": 100})
sock.sendall(json_request)
response = sock.recv(4096)
print "Received %s" % response
print "Closing socket to PFNN"
sock.close()

# if test_put:
#     for i in range(num_frames):
#         req_type = "PUT"
#         json_request = json.dumps({"RequestType": req_type, "JointPos": joint_pos_lists[i], "RootXformVels": xz_vel_lists[i]})
#         sock.sendall(json_request)
#         data = sock.recv(4096)
#         print "Received %s" % data
#         time.sleep(0.1)



def createX(json):
    return "x"
