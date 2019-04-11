#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import numpy as np
import socket
import time
import json
import sys

test_maya_get = False
test_pfnn_send = True
test_maya_put = False
XDIM = 342

maya_address = ("localhost", 12345)
# pfnn_address = ("35.246.116.151", 54321) # google compute engine addr
pfnn_address = ("localhost", 54321)

def createX(json):
    X = np.zeros(XDIM)
    w = 12
    j = 31
    root_xform_pos = json["RootPos"]  # [x, y, z] worldspace coords
    root_xform_dir = json["RootDir"]  # [x, y, z] worldspace directions

    theta = np.arctan2(root_xform_dir[0], root_xform_dir[2])     # arctan(x/z)
    rotation_matrix = np.array([np.cos(theta), -(np.sin(theta)), np.sin(theta), np.cos(theta)]).reshape(2,2)

    # Trajectory positions and directions
    for i in range(w/2):
        past_posx = json["PathPos"][0][0] - root_xform_pos[0]
        posx = json["PathPos"][i*10][0] - root_xform_pos[0]
        past_posz = json["PathPos"][0][1] - root_xform_pos[2]
        posz = json["PathPos"][i*10][1] - root_xform_pos[2]
        X[i+0*w/2] = past_posx
        X[i+1*w/2] = posx
        X[i+2*w/2] = past_posz
        X[i+3*w/2] = posz

        past_dirx = json["PathDir"][0][0]
        past_dirz = json["PathDir"][0][1]
        pasts = np.array([past_dirx, past_dirz])
        localised_pasts = np.matmul(rotation_matrix, pasts)

        dirx = json["PathDir"][i*10][0]
        dirz = json["PathDir"][i*10][1]
        dirs = np.array([dirx, dirz])
        localised_dirs = np.matmul(rotation_matrix, dirs)

        X[i+4*w/2] = localised_pasts[0]
        X[i+5*w/2] = localised_dirs[0]
        X[i+6*w/2] = localised_pasts[1]
        X[i+7*w/2] = localised_dirs[1]

    # Gait
    for i in range(w):  ##WILL NEED TO FIX LATER
        gait_index = json["Gait"][i]    # FINE while all set to test value, change to i*10 for full implementation
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
            X[i+9*w] = 1.0

    X[10*w       : 10*w + j*3] = json["JointPos"]  # Joint positions
    X[10*w + j*3 : 10*w + j*6] = json["JointVel"]  # Joint velocities

    # Trajectory heights
    for i in range(w/2):
        past_h_r = json["PathHeight"][0][0] - root_xform_pos[1]
        past_h_m = json["PathHeight"][0][1] - root_xform_pos[1]
        past_h_l = json["PathHeight"][0][2] - root_xform_pos[1]
        height_r = json["PathHeight"][i*10][0] - root_xform_pos[1]
        height_m = json["PathHeight"][i*10][1] - root_xform_pos[1]
        height_l = json["PathHeight"][i*10][2] - root_xform_pos[1]

        X[10*w + j*6 + i] = past_h_r
        X[11*w + j*6 + i] = past_h_m
        X[12*w + j*6 + i] = past_h_l
        X[10*w + j*6 + i + w/2] = height_r
        X[11*w + j*6 + i + w/2] = height_m
        X[12*w + j*6 + i + w/2] = height_l

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
    print("Connecting to %s port %s" % maya_address)
    sock.connect(maya_address)

    req_type = "GET"
    json_request = json.dumps({"RequestType": req_type})
    sock.sendall(json_request)

    full_response = False
    response = ""
    while not full_response:
        resp = sock.recv(4096)
        response = response + resp
        if '}' in resp:
            full_response = True
    print("Received %s" % response)
    print("Closing socket to Maya\n")
    sock.close()

    # Maya appends "\n\x00" to the end of anything it sends back, the following removes this so the json can be extracted
    response = response.replace("\n", '')
    response = response.replace("\x00", '')
    # json_response = json.loads(response)
    # initial_X = createX(json_response)
    # json_pfnn = createJsonPfnn(json_response, initial_X)
    json_pfnn = response

if test_pfnn_send:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to %s port %s" % pfnn_address)
    sock.connect(pfnn_address)

    sock.sendall(json_pfnn)

    all_responses = False
    while not all_responses:
        full_response = False
        response = ""
        while not full_response:
            resp = sock.recv(4096)
            response = response + resp
            if '}' in resp:
                full_response = True
                print("Received: %s" % response)
            if '#' in resp:
                full_response = True
                all_responses = True
    print("Closing socket to PFNN")
    sock.close()

    # json_response = json.loads(response)

if test_maya_put:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to %s port %s" % maya_address)
    sock.connect(maya_address)

    json_response["RequestType"] = "BUFF"
    json_request = json.dumps(json_response)

    sock.sendall(json_request)
    data = sock.recv(4096)
    print("Received %s" % data)
    time.sleep(0.1)
