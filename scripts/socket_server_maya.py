#################################################################
# Runs from inside Maya.
#################################################################

import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
import json

#pm.general.commandPort(name=":12345", pre="myServer", sourceType="mel", eo=True)

# commandPort can only accept a MEL procedure as a prefix, so this acts as a wrapper for the python function myServer below.
melproc = """
global proc string myServer(string $str){
    string $formatted = substituteAllString($str, "\\"", "'");
    string $result = python(("myServer(\\"" + $formatted + "\\")"));
    return $result;
}
"""

mel.eval(melproc)

# Names of joints stored here for easy access
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
    moveJoints(joint_pos, joint_ang)

def parsePut(request):
    pos = request["JointPos"]
    pos = pos.replace('[', '')
    pos = pos.replace(']', '')
    pos = pos.replace(',', '')
    pos = pos.split()
    joint_pos = []

    ang = request["JointAngles"]
    ang = ang.replace('[', '')
    ang = ang.replace(']', '')
    ang = ang.replace(',', '')
    ang = ang.split()
    joint_ang = []

    for i in range(len(pos)):
        joint_pos.append(float(pos[i]))
    for j in range(len(ang)):
        joint_ang.append(float(ang[j]))

    return joint_pos, joint_ang

def moveJoints(joint_pos, joint_ang):
    global character

    ### PROBLEM: This moves the joints but the skeleton moves weirdly.
    ### Check whether I am using the wrong outputs, whether need the angles
    ### Have set it up so can use angles but not surrently using)
    for i in range(len(character.joints)):
        cmds.move(joint_pos[i*3], joint_pos[i*3+1], joint_pos[i*3+2], character.joints[i])

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
