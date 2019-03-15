#################################################################
# Runs from inside Maya.
#################################################################

import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
import json

pm.general.commandPort(name=":12345", pre="myServer", sourceType="mel", eo=True)

# commandPort can only accept a MEL procedure as a prefix, so this acts as a wrapper for the python function myServer below.
melproc = """
global proc string myServer(string $str){
    string $formatted = substituteAllString($str, "\\"", "'");
    string $result = python(("myServer(\\"" + $formatted + "\\")"));
    return $result;
}
"""

mel.eval(melproc)

class Character():
    def __init__(self):
        self.root = getRoot()
        self.joints = getJoints([self.root], self.root)

def myServer(str):
    json_str = str.replace("'", '"')
    request = json.loads(json_str)

    if request["RequestType"] == "GET":
        print("Request is a GET!")
        return "GET received"
    elif request["RequestType"] == "PUT":
        print("Request is a PUT!")
        doPut(request)
        return "PUT received"

def doPut(request):
    joint_pos, joint_ang = parsePut(request)
    #moveJoints(character, joint_pos, joint_ang)
    pass

# Assuming Y_Out is in full (i.e. 311 output array)
def parsePut(request):
    Y_out = request["Y_Output"]
    p = Y_out.replace('[', '')
    q = p.replace(']', '')
    r = q.split()

    joint_pos = []
    joint_ang = []

    # Hard coded numbers. Thinking of changing this so only the needed info is sent to maya
    # i.e. not all of Y_Out but only the joint positions and angles
    for i in range(24, 118):
        joint_pos.append(r[i])
    for i in range(211, 304):
        joint_ang.append(r[i])

    print(joint_pos[0])
    print(len(joint_pos))
    print(joint_ang[0])
    print(len(joint_ang))
    return joint_pos, joint_ang

def moveJoints(character, joint_pos, joint_ang):
    pass

def getJoints(joints, joint):
    children = cmds.listRelatives(joint)
    if children is not None:
        for child in children:
            joints.append(child)
            joints = getJoints(joints, child)
    return joints

def getRoot():
    joints = cmds.ls(type='joint')
    x = joints[0]
    found = False

    while not found:
        parent = cmds.listRelatives(x, parent=True)
        if parent is not None:
            x = parent[0]
            root = parent[0]
        elif parent is None:
            found = True

    return root

character = Character()
#pm.general.commandPort(name=":12345", cl=True)
