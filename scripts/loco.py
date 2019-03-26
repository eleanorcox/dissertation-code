#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import numpy as np
import socket
import time
import json
import sys

test_maya_get = True
test_pfnn_send = False
test_maya_put = False
XDIM = 342

def createX(json):
    X = np.zeros(XDIM)
    w = 12
    jn = 31

    # Trajectory positions and directions
    for i in range(w/2):
        past_posx = json["PathPos"][0][0]
        posx = json["PathPos"][i][0]
        past_posz = json["PathPos"][0][1]
        posz = json["PathPos"][i][1]
        X[i+0*w/2] = past_posx
        X[i+1*w/2] = posx
        X[i+2*w/2] = past_posz
        X[i+3*w/2] = posz

        past_dirx = json["PathDir"][0][0]
        dirx = json["PathDir"][i][0]
        past_dirz = json["PathDir"][0][1]
        dirz = json["PathDir"][i][1]
        X[i+4*w/2] = past_dirx
        X[i+5*w/2] = dirx
        X[i+6*w/2] = past_dirz
        X[i+7*w/2] = dirz

    # Gait
    for i in range(w):
        gait_index = json["Gait"][i]
        if gait_index == 0: # Stand
            X[i+4*w] = 1.0
        if gait_index == 1: # Walk
            X[i+5*w] = 1.0
        if gait_index == 2: # Jog
            X[i+6*w] = 1.0
        if gait_index == 3: # Crouch
            X[i+7*w] = 1.0
        if gait_index == 4: # Jump
            X[i+8*w] = 1.0
        if gait_index == 5: # Unused
            pass

    X[10*w : 10*w + jn*3] = json["JointPos"]        # Joint positions
    X[10*w + jn*3: 10*w + jn*6] = json["JointVel"]  # Joint velocities

    # Trajectory heights
    for i in range(w):
        height_r = json["PathHeight"][i][0]
        height_m = json["PathHeight"][i][1]
        height_l = json["PathHeight"][i][2]
        X[10*w + jn*6 + i] = height_r
        X[11*w + jn*6 + i] = height_m
        X[12*w + jn*6 + i] = height_l

    X = X.tolist()
    return X

def createJsonPfnn(js, initial_X):
    j = json.dumps({"AnimFrames": js["AnimFrames"],
                    "PathPos": js["PathPos"],
                    "PathDir": js["PathDir"],
                    "PathHeight": js["PathHeight"],
                    "Gait": js["Gait"],
                    "X": initial_X})
    return j

if test_maya_get:
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    maya_address = ("localhost", 12345)
    print "Connecting to %s port %s" % maya_address
    sock.connect(maya_address)

    req_type = "GET"
    json_request = json.dumps({"RequestType": req_type})
    sock.sendall(json_request)
    response = sock.recv(4096)
    print "Received %s" % response
    print "Closing socket to Maya"
    sock.close()

    # Maya appends "\n\x00" to the end of anything it sends back, the following removes this so the json can be extracted
    response = response.replace("\n", '')
    response = response.replace("\x00", '')
    json_response = json.loads(response)
    initial_X = createX(json_response)
    json_pfnn = createJsonPfnn(json_response, initial_X)

if test_pfnn_send:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pfnn_address = ("localhost", 54321)
    print "Connecting to %s port %s" % pfnn_address
    sock.connect(pfnn_address)

    sock.sendall(json_pfnn)
    response = sock.recv(4096)
    print "Received %s" % response
    print "Closing socket to PFNN"
    sock.close()

# if test_maya_put:
#     for i in range(num_frames):
#         req_type = "PUT"
#         json_request = json.dumps({"RequestType": req_type, "JointPos": joint_pos_lists[i], "RootXformVels": xz_vel_lists[i]})
#         sock.sendall(json_request)
#         data = sock.recv(4096)
#         print "Received %s" % data
#         time.sleep(0.1)
