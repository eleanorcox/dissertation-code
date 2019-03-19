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
    joint_pos = parsePut(request)
    moveJoints(joint_pos)
    setJointKeyframes()
    updateFrame()

def parsePut(request):
    pos = request["JointPos"]
    pos = pos.split()
    joint_pos = []

    for i in range(len(pos)):
        joint_pos.append(float(pos[i]))

    return joint_pos

def moveJoints(joint_pos):
    global character
    root_xform = getRootXform()

    for i in range(len(character.joints)):
        x_offset = joint_pos[i*3]
        y_offset = joint_pos[i*3+1]
        z_offset = joint_pos[i*3+2]
        x_xform = root_xform[0] + x_offset
        y_xform = root_xform[1] + y_offset
        z_xform = root_xform[2] + z_offset
        cmds.move(x_xform, y_xform, z_xform, character.joints[i], worldSpace=True)

def setJointKeyframes():
    for joint in character.joints:
        cmds.setKeyframe(joint, attribute="translate")

def updateFrame():
    now = cmds.currentTime(query=True)
    cmds.currentTime(now + 1)

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

def getRootXform():
    ### HARDCODED NAMES
    left_hip = "JOINT_LHipJoint"
    right_hip = "JOINT_RHipJoint"
    left_toe = "JOINT_LeftToeBase"
    right_toe = "JOINT_RightToeBase"

    left_world_xform = cmds.xform(left_hip, worldSpace=True, query=True, translation=True)
    right_world_xform = cmds.xform(right_hip, worldSpace=True, query=True, translation=True)
    hip_world_xform = [0,0,0]
    for i in range(len(left_world_xform)):
        hip_world_xform[i] = (left_world_xform[i]+right_world_xform[i]) / 2

    l_toe_world_xform = cmds.xform(left_toe, worldSpace=True, query=True, translation=True)
    r_toe_world_xform = cmds.xform(right_toe, worldSpace=True, query=True, translation=True)
    floor_height = 0
    if l_toe_world_xform[1] > r_toe_world_xform[1]:
        floor_height = l_toe_world_xform[1]
    else:
        floor_height = r_toe_world_xform[1]

    root_x = hip_world_xform[0]
    root_y = floor_height
    root_z = hip_world_xform[2]

    return [root_x, root_y, root_z]

character = Character()
#pm.general.commandPort(name=":12345", cl=True)
