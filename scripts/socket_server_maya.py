#################################################################
# Runs from inside Maya.
#################################################################

import maya.cmds as cmds
import pymel.core as pm
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
        return "GET acknowledged"
    elif request["RequestType"] == "PUT":
        doPut(request)
        return "PUT acknowledged"

def doPut(request):
    joint_pos, root_xform_x_vel, root_xform_z_vel = parsePut(request)
    moveRootXform(root_xform_x_vel, root_xform_z_vel)
    moveJoints(joint_pos)
    setJointKeyframes()
    updateFrame()

def parsePut(request):
    pos = request["JointPos"]
    pos = pos.split()
    joint_pos = []
    for i in range(len(pos)):
        joint_pos.append(float(pos[i]))

    vel = request["RootXformVels"]
    vel = vel.split()
    root_xform_x_vel = float(vel[0])
    root_xform_z_vel = float(vel[1])

    return joint_pos, root_xform_x_vel, root_xform_z_vel

def calculatePosition(initial_pos, velocity):
    # time = 1/120    # frames?
    time = 1
    new_pos = (velocity * time) + initial_pos
    return new_pos

def moveRootXform(root_xform_x_vel, root_xform_z_vel):
    root_xform = getRootXform()
    new_x = calculatePosition(root_xform[0], root_xform_x_vel)
    new_y = 0       # Hardcoded
    new_z = calculatePosition(root_xform[2], root_xform_z_vel)
    cmds.move(new_x, new_y, new_z, character.root, worldSpace=True)

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

    left_world_xform = cmds.xform(left_hip, worldSpace=True, query=True, translation=True)
    right_world_xform = cmds.xform(right_hip, worldSpace=True, query=True, translation=True)
    hip_world_xform = [0,0,0]
    for i in range(len(left_world_xform)):
        hip_world_xform[i] = (left_world_xform[i]+right_world_xform[i]) / 2

    root_x = hip_world_xform[0]
    root_y = 0                  # Hardcoded
    root_z = hip_world_xform[2]

    return [root_x, root_y, root_z]

character = Character()
#pm.general.commandPort(name=":12345", cl=True)
