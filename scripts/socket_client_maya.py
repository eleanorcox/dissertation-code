#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import socket
import json
import sys

# Numbers of things in the output from the model
num_traj = 12
num_joint = 93
num_root = 1
num_phase = 1
num_contact = 4

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect the socket to the port where Maya is listening
maya_address = ("localhost", 12345)
print "connecting to %s port %s" % maya_address
sock.connect(maya_address)

""" This deals with reading in string data from a text file. Will not need/
will need to edit when I am reading directly from the nn because the data
will already be in the correct format"""
file_name = "sample_y_train.txt"
print("Reading file '%s'" % file_name)
f = open(file_name, "r")
p = f.read()
q = p.replace('[', '')
r = q.replace(']', '')
s = r.replace('\n', '')
t = s.split()
for i in range(len(t)):
    value = t[i]
    floated = float(value)
    t[i] = floated

### Definitely a nicer way to do this
trajectory_positions = str(t[0:num_traj])
trajectory_directions = str(t[12:12+num_traj])
joint_positions = str(t[24:24+num_joint])
joint_velocities = str(t[117:117+num_joint])
joint_angles = str(t[210:210+num_joint])
root_trans_x_velocity = str(t[303:303+num_root])
root_trans_z_velocity = str(t[304:304+num_root])
root_trans_angular_velocity = str(t[305:305+num_root])
phase_change = str(t[306:306+num_phase])
foot_contact = str(t[307:307+num_contact])

try:
    req_type = "PUT"
    json_request = json.dumps({"RequestType": req_type, "JointPos": joint_positions, "JointAngles": joint_angles})

    sock.sendall(json_request)
    # MAYBE better to use send but fix this l8r

    data = sock.recv(4096)
    print "received %s" % data

finally:
    print "closing socket"
    sock.close()
