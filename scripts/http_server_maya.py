####################################################################
# Testing http networking.
# Code run from inside Maya, so Maya acts as the http server.
# GET and POST requests recieved. GET requests responded to correctly.
# POST requests perform the correct command, but are not replying
# to the server correctly. This seems to be a problem with commandPort,
# as it interprets newline characters as separating out commands, and
# http requests have newlines baked in.
# To ovrcome this I am going to avoid http and write my own protocol
# that works over sockets and is specific to my needs (e.g. I don't need
# a lot of the information that comes with a http request such as language)
####################################################################

import maya.cmds as cmds
import pymel.core as pm
import maya.mel as mel

posting = False
post_cmd_next = False

pm.general.commandPort(name=":12345", pre="myServer", sourceType="mel", eo=True)

# commandPort can only accept a MEL procedure as a prefix, so this acts as a wrapper for the python function myServer below.
melproc = """
global proc string myServer(string $str){
    $str = match( "^[^(\\r\\n)]*", $str );
    string $result = python(("myServer(\\"" + $str + "\\")"));
    print($result);
    return $result;
}
"""

mel.eval(melproc)

# Ensures messages are sent in correct http format
def returnPage(message):
    head = "HTTP/1.1 200 OK\n" + "Content-length: " + str(len(message)) + "\n" + "Content-type: text/plain\n" + "\n"
    return head + message

def myServer(str):
    global posting
    global post_cmd_next

    buffer = str.split(" ")

    if buffer[0]=="GET":        # GET request
        if buffer[1]=="/":
            return returnPage("Hello There!")
    elif buffer[0]=="POST":     # POST request
        posting = True
        if buffer[1]=="/":
            return returnPage("General Kenobi")
    elif posting and buffer[0]=="":     # Signifies the next input to the commandport is our command
        post_cmd_next = True
    elif posting and post_cmd_next:     # Runs the command
        # str is a MEL COMMAND
        print(str)
        result_list = mel.eval(str)
        result = ""
        for i in result_list:
            result = result + i + " "

        posting = False
        post_cmd_next = False

        return returnPage(result)

#pm.general.commandPort(name=":12345", cl=True)
