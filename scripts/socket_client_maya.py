#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import numpy as np
import socket
import time
import json
import sys

num_joint = 93
num_frames = 8000    # ys has 39730 frames total or ~5.5 minutes (at 120fps). I am using a subset.

def formatData(array):
    string = np.array2string(array)
    string = string.replace('[', '')
    string = string.replace(']', '')
    string = string.replace('\n', '')
    return string

print("Loading in data...")
full_ys = np.load('denormalised_y_full.npz')
ys = full_ys['Y']

print("Extracting relevant data...")
joint_pos_full = np.ndarray(shape=(num_frames, num_joint))
xz_vel_full    = np.ndarray(shape=(num_frames, 2))
for i in range(num_frames):
    y = ys[i]
    joint_positions = y[32:32+num_joint]
    joint_pos_full[i] = joint_positions

    x_vel = y[0]
    z_vel = y[1]
    xz_vel_full[i] = [x_vel, z_vel]

print("Formatting data...")
joint_pos_strings = np.ndarray(num_frames, dtype=object)
xz_vel_strings    = np.ndarray(num_frames, dtype=object)
for i in range(num_frames):
    joint_pos_strings[i] = formatData(joint_pos_full[i])
    xz_vel_strings[i]    = formatData(xz_vel_full[i])

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
maya_address = ("localhost", 12345)
print "Connecting to %s port %s" % maya_address
sock.connect(maya_address)

try:
    for i in range(num_frames):
        req_type = "PUT"
        json_request = json.dumps({"RequestType": req_type, "JointPos": joint_pos_strings[i], "RootXformVels": xz_vel_strings[i]})
        sock.sendall(json_request)
        data = sock.recv(4096)
        print "Received %s" % data
        time.sleep(0.05)
finally:
    print "Closing socket"
    sock.close()
