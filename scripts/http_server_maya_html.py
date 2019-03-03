#################################################################
# Testing http networking.
# This script should be run from the Python script editor in Maya.
# Trying to convert http_server_maya_html.mel into python -
#                       UNFINISHED and BROKEN.
# Not going to finish as I don't need html, instead moving to
# http_server_maya.py to work without html
#################################################################
import maya.cmds as cmds
import pymel.core as pm

#cmds.commandPort(name=":12345", sourceType="mel")
#cmds.commandPort(name=":12346", sourceType="python")
pm.general.commandPort(name=":12345")

def returnPage(message):
    head = "HTTP/1.0 200 OK\n" + "Content-length: " + str(len(message)) + "\n" + "Content-type: text/html\n" + "\n"
    return head + message

def toLinks(strings):
    temp = ""
    for item in strings:
        temp += "<a href=\"" + item + "\">" + item + "</a><br>\n"
    return temp

def myServer(str):
    buffer = str.split(" ")
    numTokens = len(buffer)

    # If we have a GET request
    if buffer[0]=="GET":
        if buffer[1]=="/":
            mess = "<!DOCTYPE HTML PUBLIC "+"\"-//W3C//DTD HTML 3.2 Final//EN\">\n"+"<HTML>\n"+"  <HEAD>\n"+"    <TITLE>Serving</TITLE>\n"+"  </HEAD>\n"+"  <BODY>\n"+"    <h1>Listing:</h1>\n"+"  </BODY>\n"+"<HTML>\n"
            return returnPage(mess)
        else:
            pth = "oh god"

#pm.general.commandPort(name=":12345", cl=True)
