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

if test_maya_get:
    maya_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to Maya: %s port %s" % maya_address)
    maya_sock.connect(maya_address)

    json_request = json.dumps({"RequestType": "GET"})
    maya_sock.sendall(json_request)

    full_response = False
    response = ""
    while not full_response:
        resp = maya_sock.recv(4096)
        response = response + resp
        if '}' in resp:
            full_response = True

    # Maya appends "\n\x00" to the end of anything it sends back, the following removes this
    response = response.replace("\n", '')
    response = response.replace("\x00", '')
    print("Received %s" % response)

    # Checking we've received a JSON object
    json_response = json.loads(response)
    json_pfnn = json.dumps(json_response)

if test_pfnn_send:
    pfnn_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to PFNN: %s port %s" % pfnn_address)
    pfnn_sock.connect(pfnn_address)
    pfnn_sock.sendall(json_pfnn)

    all_responses = False
    responses = ""
    while not all_responses:
        resp = pfnn_sock.recv(4096)
        responses = responses + resp
        if '#' in resp:
            all_responses = True
    print("Closing socket to PFNN")
    pfnn_sock.close()

    # Separates out and correctly formats the responses
    responses = responses.replace("#", "")
    responses = responses.split('}')
    for i in range(len(responses)):
        responses[i] = responses[i] + '}'
    responses = responses[:-1]

if test_maya_put:
    print("Sending data to Maya\n")

    for response in responses:
        # print(repr(response))
        json_response = json.loads(response)
        json_response["RequestType"] = "BUFF"
        json_request = json.dumps(json_response)

        maya_sock.sendall(json_request)
        data = maya_sock.recv(4096)
        print("Received %s" % data)
        time.sleep(0.1)

    maya_sock.close()
