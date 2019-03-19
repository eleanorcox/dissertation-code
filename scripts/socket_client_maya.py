#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import numpy as np
import socket
import time
import json
import sys

num_joint = 93
num_frames = 300    # ys has 39730 frames total or ~5.5 minutes (at 120fps). I am using a subset.

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
for i in range(num_frames):
    y = ys[i]
    joint_positions = y[32:32+num_joint]
    joint_pos_full[i] = joint_positions

print("Formatting data...")
joint_pos_strings = np.ndarray(num_frames, dtype=object)
for i in range(num_frames):
    joint_pos_strings[i] = formatData(joint_pos_full[i])

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect the socket to the port where Maya is listening
maya_address = ("localhost", 12345)
print "Connecting to %s port %s" % maya_address
sock.connect(maya_address)

try:
    for i in range(num_frames):
        req_type = "PUT"
        json_request = json.dumps({"RequestType": req_type, "JointPos": joint_pos_strings[i]})
        sock.sendall(json_request)
        data = sock.recv(4096)
        print "received %s" % data
        time.sleep(0.05)
finally:
    print "closing socket"
    sock.close()

### Numbers of things in the output from the model
# num_root = 1
# num_phase = 1
# num_contact = 4
# num_traj = 12

### Definitely a nicer way to do this
# root_trans_x_velocity = str(t[0:num_root])
# root_trans_z_velocity = str(t[1:1+num_root])
# root_trans_angular_velocity = str(t[2:2+num_root])
# phase_change = str(t[3:3+num_phase])
# foot_contact = str(t[4:4+num_contact])
# trajectory_positions = str(t[8:8+num_traj])
# trajectory_directions = str(t[20:20+num_traj])
# joint_positions_1 = str(y1[32:32+num_joint])
# joint_velocities = str(t[125:125+num_joint])
# joint_angles = str(t[218:218+num_joint])
