####################################################################
# Testing http networking.
# Code run from inside Maya, so Maya acts as the http server.
# GET and POST requests receved and replied to, although POST is not
# currently working properly (i.e. changing whatever it is requested to)
####################################################################

import maya.cmds as cmds
import pymel.core as pm
import maya.mel as mel

pm.general.commandPort(name=":12345", pre="myServer", sourceType="mel", eo=True)

# commandPort can only accept a MEL procedure as a prefix, so this acts as a wrapper for the python function myServer below.
melproc = """
global proc string myServer(string $str){
    $str = match( "^[^(\\r\\n)]*", $str );
    string $result = python(("myServer(\\"" + $str + "\\")"));
    return $result;
}
"""

mel.eval(melproc)

# Ensures messages are sent in correct http format
def returnPage(message):
    head = "HTTP/1.1 200 OK\n" + "Content-length: " + str(len(message)) + "\n" + "Content-type: text/plain\n" + "\n"
    return head + message

def myServer(str):
    buffer = str.split(" ")
    #numTokens = len(buffer)

    if buffer[0]=="GET":        # GET request
        if buffer[1]=="/":
            return returnPage("Hello There!")
    elif buffer[0]=="POST":     # POST request
        if buffer[1]=="/":
            return returnPage("General Kenobi")

#pm.general.commandPort(name=":12345", cl=True)
