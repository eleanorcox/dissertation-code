#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import numpy as np
import socket
import time
import json
import sys

test_get = False
test_put = True

num_joint = 93
num_frames = 4000    # ys has 39730 frames total or ~5.5 minutes (at 120fps). I am using a subset.

# Number of frames per clip
clip_0, clip_1, clip_2, clip_3, clip_4 = 57,37,50,46,51
clip_5, clip_6, clip_7, clip_8, clip_9 = 35,35,48,32,56
# clip_10, clip_11, clip_12, clip_13     = 27,42,43,56
# clip_14, clip_15, clip_16, clip_17     = 44,49,48,30

# Start frame of clip
start_0, start_1, start_2, start_3, start_4 = 0,570,939,1439,1899
start_5, start_6, start_7, start_8, start_9 = 2409,2759,3109,3589,4202
# start_10, start_11, start_12, start_13     = 4469,4739,5159,5589
# start_14, start_15, start_16, start_17     = 6149,6589,7053,7532

clip_frames = 359

if test_put:
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

    ### Massive hacks
    ### Only using first 8 clips as gives slightly better animation
    ### Hacky because only using for poster day demo
    joint_pos_clips = np.ndarray(shape=(clip_frames, num_joint))
    xz_vel_clips    = np.ndarray(shape=(clip_frames, 2))
    start = 0
    joint_pos_clips[start:start+clip_0] = joint_pos_full[start_0:start_0+clip_0]
    xz_vel_clips[start:start+clip_0] = xz_vel_full[start_0:start_0+clip_0]

    start = start + clip_0
    joint_pos_clips[start:start+clip_1] = joint_pos_full[start_1:start_1+clip_1]
    xz_vel_clips[start:start+clip_1] = xz_vel_full[start_1:start_1+clip_1]

    start = start + clip_1
    joint_pos_clips[start:start+clip_2] = joint_pos_full[start_2:start_2+clip_2]
    xz_vel_clips[start:start+clip_2] = xz_vel_full[start_2:start_2+clip_2]

    start = start + clip_2
    joint_pos_clips[start:start+clip_3] = joint_pos_full[start_3:start_3+clip_3]
    xz_vel_clips[start:start+clip_3] = xz_vel_full[start_3:start_3+clip_3]

    start = start + clip_3
    joint_pos_clips[start:start+clip_4] = joint_pos_full[start_4:start_4+clip_4]
    xz_vel_clips[start:start+clip_4] = xz_vel_full[start_4:start_4+clip_4]

    start = start + clip_4
    joint_pos_clips[start:start+clip_5] = joint_pos_full[start_5:start_5+clip_5]
    xz_vel_clips[start:start+clip_5] = xz_vel_full[start_5:start_5+clip_5]

    start = start + clip_5
    joint_pos_clips[start:start+clip_6] = joint_pos_full[start_6:start_6+clip_6]
    xz_vel_clips[start:start+clip_6] = xz_vel_full[start_6:start_6+clip_6]

    start = start + clip_6
    joint_pos_clips[start:start+clip_7] = joint_pos_full[start_7:start_7+clip_7]
    xz_vel_clips[start:start+clip_7] = xz_vel_full[start_7:start_7+clip_7]

    print("Formatting data...")
    joint_pos_lists = np.ndarray(clip_frames, dtype=object)
    xz_vel_lists    = np.ndarray(clip_frames, dtype=object)
    for i in range(clip_frames):
        joint_pos_lists[i] = joint_pos_clips[i].tolist()
        xz_vel_lists[i]    = xz_vel_clips[i].tolist()

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
maya_address = ("localhost", 12345)
print "Connecting to %s port %s" % maya_address
sock.connect(maya_address)

try:
    if test_get:
        req_type = "GET"
        json_request = json.dumps({"RequestType": req_type})
        sock.sendall(json_request)
        data = sock.recv(4096)
        print "Received %s" % data

    if test_put:
        for i in range(clip_frames):
            req_type = "PUT"
            json_request = json.dumps({"RequestType": req_type, "JointPos": joint_pos_lists[i], "RootXformVels": xz_vel_lists[i]})
            sock.sendall(json_request)
            data = sock.recv(4096)
            print "Received %s" % data
            time.sleep(0.1)
finally:
    print "Closing socket"
    sock.close()
