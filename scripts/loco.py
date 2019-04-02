#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import numpy as np
import socket
import time
import json
import sys

test_maya_get = True
test_pfnn_send = True
test_maya_put = True
XDIM = 342

maya_address = ("localhost", 12345)
pfnn_address = ("35.246.116.151", 54321) # google compute engine addr
# pfnn_address = ("localhost", 54321)

def createX(json):
    X = np.zeros(XDIM)
    w = 12
    jn = 31

    # Trajectory positions and directions
    for i in range(w/2):
        past_posx = json["PathPos"][0][0]
        posx = json["PathPos"][i*10][0]
        past_posz = json["PathPos"][0][1]
        posz = json["PathPos"][i*10][1]
        X[i+0*w/2] = past_posx
        X[i+1*w/2] = posx
        X[i+2*w/2] = past_posz
        X[i+3*w/2] = posz

        past_dirx = json["PathDir"][0][0]
        dirx = json["PathDir"][i*10][0]
        past_dirz = json["PathDir"][0][1]
        dirz = json["PathDir"][i*10][1]
        X[i+4*w/2] = past_dirx
        X[i+5*w/2] = dirx
        X[i+6*w/2] = past_dirz
        X[i+7*w/2] = dirz

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
            pass

    X[10*w : 10*w + jn*3] = json["JointPos"]        # Joint positions
    X[10*w + jn*3: 10*w + jn*6] = json["JointVel"]  # Joint velocities

    # Trajectory heights
    for i in range(w/2):
        past_h_r = json["PathHeight"][0][0]
        height_r = json["PathHeight"][i*10][0]
        past_h_m = json["PathHeight"][0][1]
        height_m = json["PathHeight"][i*10][1]
        past_h_l = json["PathHeight"][0][2]
        height_l = json["PathHeight"][i*10][2]

        X[10*w + jn*6 + i] = past_h_r
        X[10*w + jn*6 + i + w/2] = height_r
        X[11*w + jn*6 + i] = past_h_m
        X[11*w + jn*6 + i + w/2] = height_m
        X[12*w + jn*6 + i] = past_h_l
        X[12*w + jn*6 + i + w/2] = height_l
        
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
    json_response = json.loads(response)
    initial_X = createX(json_response)
    json_pfnn = createJsonPfnn(json_response, initial_X)

# json_pfnn = '{"PathDir": [[-3.916666666666667, 8.472222222222223], [0.583333333333333, 4.6388888888888875], [2.583333333333334, 2.6388888888888893], [2.4969135802469133, 2.212962962962962], [1.9783950617283943, 2.324074074074076], [1.4413580246913584, 2.712962962962962], [0.8827160493827169, 3.253086419753089], [0.2901234567901234, 3.4382716049382687], [-0.33950617283950635, 3.141975308641978], [-1.0246913580246915, 2.5493827160493865], [-1.8395061728395055, 2.401234567901227], [-2.8024691358024696, 2.882716049382722], [-3.3456790123456766, 3.90123456790122], [-1.1975308641975326, 5.086419753086432], [0, 0]], "Gait": [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], "PathHeight": [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]], "X": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -3.916666666666667, -3.333333333333334, -0.75, 1.7469135802469133, 3.7253086419753076, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.472222222222223, 13.11111111111111, 15.75, 17.962962962962962, 20.287037037037038, -3.916666666666667, -3.916666666666667, -3.916666666666667, -3.916666666666667, -3.916666666666667, -3.916666666666667, -3.916666666666667, 0.583333333333333, 2.583333333333334, 2.4969135802469133, 1.9783950617283943, 1.4413580246913584, 8.472222222222223, 8.472222222222223, 8.472222222222223, 8.472222222222223, 8.472222222222223, 8.472222222222223, 8.472222222222223, 4.6388888888888875, 2.6388888888888893, 2.212962962962962, 2.324074074074076, 2.712962962962962, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.3630000000000004, -1.7950000000000004, 0.8390000000000003, 3.811000000000003, -8.521000000000003, 0.8390000000000013, 6.373000000000007, -15.561000000000003, 0.8390000000000027, 6.531000000000005, -15.994000000000007, 3.1620000000000017, 0.0, 0.0, 0.0, -1.306, -1.7950000000000002, 0.839, -3.8479999999999963, -8.781, 0.838999999999991, -6.416999999999989, -15.837000000000003, 0.8389999999999862, -6.581999999999991, -16.290000000000003, 3.2019999999999857, 0.0, 0.0, 0.0, 0.028000000000000684, 2.036, -0.1929999999999997, 0.0850000000000014, 4.084999999999999, -0.23600000000000151, 0.0850000000000014, 4.084999999999999, -0.23600000000000151, 0.031000000000002158, 5.8309999999999995, -0.0640000000000028, 0.1350000000000031, 7.591999999999998, -0.18800000000000494, 0.0850000000000014, 4.084999999999999, -0.23600000000000151, 3.4470000000000005, 5.285999999999997, -0.5470000000000009, 8.43, 5.285999999999998, -0.5469999999999983, 11.913999999999998, 5.285999999999998, -0.5469999999999964, 11.913999999999998, 5.285999999999998, -0.5469999999999964, 12.628999999999998, 5.285999999999998, -0.5469999999999959, 11.913999999999998, 5.285999999999998, -0.5469999999999964, 0.0850000000000014, 4.084999999999999, -0.23600000000000151, -3.051999999999997, 5.459, -0.6410000000000036, -8.293999999999997, 5.458999999999999, -0.6410000000000053, -11.737999999999996, 5.458999999999998, -0.6410000000000069, -11.737999999999996, 5.458999999999998, -0.6410000000000069, -12.360999999999997, 5.458999999999998, -0.6410000000000072, -11.737999999999996, 5.458999999999998, -0.6410000000000069, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "PathPos": [[0.0, 0.0], [-3.916666666666667, 8.472222222222223], [-3.333333333333334, 13.11111111111111], [-0.75, 15.75], [1.7469135802469133, 17.962962962962962], [3.7253086419753076, 20.287037037037038], [5.166666666666666, 23.0], [6.049382716049383, 26.25308641975309], [6.339506172839506, 29.691358024691358], [6.0, 32.833333333333336], [4.9753086419753085, 35.38271604938272], [3.135802469135803, 37.78395061728395], [0.3333333333333335, 40.66666666666667], [-3.012345679012343, 44.56790123456789], [-4.209876543209876, 49.65432098765432]], "AnimFrames": 15}'

if test_pfnn_send:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to %s port %s" % pfnn_address)
    sock.connect(pfnn_address)

    sock.sendall(json_pfnn)

    full_response = False
    response = ""
    while not full_response:
        resp = sock.recv(4096)
        response = response + resp
        if '}' in resp:
            full_response = True

    print("Received: %s" % response)
    print("Closing socket to PFNN")
    sock.close()

    json_response = json.loads(response)

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
