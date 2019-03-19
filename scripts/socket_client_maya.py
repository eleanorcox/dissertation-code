#################################################################
# Socket client to Maya. Runs in terminal.
#################################################################
import socket
import json
import sys

num_joint = 93

#This deals with reading in string data from a text file. Will not need/
#will need to edit when I am reading directly from the nn because the data
#will already be in the correct format
def process_file(file_name):
    print("Reading file '%s'" % file_name)
    f = open(file_name, "r")
    y = f.read()
    y = y.replace('[', '')
    y = y.replace(']', '')
    y = y.replace('\n', '')
    y = y.split()
    for i in range(len(y)):
        value = y[i]
        floated = float(value)
        y[i] = floated
    joint_positions = str(y[32:32+num_joint])
    return joint_positions

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect the socket to the port where Maya is listening
maya_address = ("localhost", 12345)
print "connecting to %s port %s" % maya_address
sock.connect(maya_address)

file_name_1 = "denormalised_y_1.txt"
file_name_2 = "denormalised_y_2.txt"
joint_positions_1 = process_file(file_name_1)
joint_positions_2 = process_file(file_name_2)

try:
    req_type = "PUT"
    json_request = json.dumps({"RequestType": req_type, "JointPos": joint_positions_1})
    sock.sendall(json_request)    # MAYBE better to use send but fix this l8r
    data = sock.recv(4096)
    print "received %s" % data

    json_request_2 = json.dumps({"RequestType": req_type, "JointPos": joint_positions_2})
    sock.sendall(json_request_2)
    data = sock.recv(4096)
    print "received %s" % data

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
