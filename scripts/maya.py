#################################################################
# Runs from inside Maya.
#################################################################

import maya.cmds as cmds
import maya.mel as mel
import json

anim_frames = 800
server_on = False

# Names of joints stored here
class Character():
    def __init__(self):
        self.root = getRootName()
        self.joints = getJointNames([self.root], self.root)

########## Server functions ##########

# May want to add bufferSize flag, size of buffer for commands and results. Default 4096.
if server_on:
    cmds.commandPort(name=":12345", pre="myServer", sourceType="mel", eo=True)

# commandPort can only accept a MEL procedure as a prefix, so this acts as a wrapper for the python function myServer below.
melproc = """
global proc string myServer(string $str){
    string $formatted = substituteAllString($str, "\\"", "'");
    string $result = python(("myServer(\\"" + $formatted + "\\")"));
    return $result;
}
"""

mel.eval(melproc)

def myServer(str):
    json_str = str.replace("'", '"')
    request = json.loads(json_str)

    if request["RequestType"] == "GET":
        response = doGet()
        return response
    elif request["RequestType"] == "BUFF":
        doBuff(request)
        return "cheese, gromit!"

########## GET requests ##########

def doGet():
    # Get path info
    path_pos = getPathPos()
    path_dir = getPathDir()
    path_heights = getPathHeight()
    # Get character info
    joint_pos = getJointPos()
    joint_vel = getJointVel()
    # Get gait info
    path_gaits = getGait()
    # Format as JSON
    response = formatGetJson(path_pos, path_dir, path_heights, joint_pos, joint_vel, path_gaits)
    return response

# Returns a list of WORLD SPACE [pos x, pos z] pairs
def getPathPos():
    path = getPathName()
    point_dist = 1.0/anim_frames
    path_pos = []

    for i in range(anim_frames):
        param = i * point_dist
        pos = cmds.pointOnCurve(path, parameter=param, turnOnPercentage=True, position=True)
        path_pos.append([pos[0], pos[2]])

    return path_pos

# Returns a list of WORLD SPACE [dir x, dir z] pairs
def getPathDir():
    path = getPathName()
    point_dist = 1.0/anim_frames
    path_dir = []

    for i in range(anim_frames):
        param = i * point_dist
        tangent = cmds.pointOnCurve(path, parameter=param, turnOnPercentage=True, normalizedTangent=True)
        path_dir.append([tangent[0], tangent[2]])

    return path_dir

# TODO: implement properly later
# Returns a list of WORLD SPACE [r, c, l] heights of the left, central and right sample points of the path
def getPathHeight():
    # path = getPathName()
    # point_dist = 1.0/anim_frames
    # path_norms = []
    #
    # for i in range(anim_frames):
    #     param = i * point_dist
    #     norm = cmds.pointOnCurve(path, parameter=param, turnOnPercentage=True, normalizedNormal=True)

    # Right now can't be bothered to do this properly, so just going to set everything to 0 for testing
    # for future: 25cm l/r in the test skeleton is roughly 10 units (guesstimate)
    path_heights = []
    for i in range(anim_frames):
        path_heights.append([0, 0, 0])
    return path_heights

# Returns a list of WORLD SPACE joint positions
def getJointPos():
    root_xform_pos = getRootXformPos()
    joints_pos = []

    for joint in character.joints:
        pos = cmds.xform(joint, worldSpace=True, query=True, translation=True)
        for i in range(len(pos)):
            joints_pos.append(pos[i])

    return joints_pos

# TODO: full implementation
# Returns a list of WORLD SPACE joint velocities
def getJointVel():
    velocities = []
    for i in range(len(character.joints)*3):
        velocities.append(0)
    return velocities

# TODO: full implementation from user input
def getGait():
    # For gait, 0=stand, 1=walk, 2=jog, 4=crouch, 5=jump, 6=unused (in pfnn)
    # Want gait at each point along path - i.e. at each frame
    # For now just set these to one of the values for testing, at a later date change this to get input from user
    gait = []
    for i in range(anim_frames):
        gait.append(1)
    return gait

def formatGetJson(path_pos, path_dir, path_heights, joint_pos, joint_vel, path_gaits):
    root_xform_pos = getRootXformPos()
    root_xform_dir = getRootXformDir()
    response = json.dumps({"AnimFrames": anim_frames,
                           "PathPos": path_pos,
                           "PathDir": path_dir,
                           "PathHeight": path_heights,
                           "JointPos": joint_pos,
                           "JointVel": joint_vel,
                           "Gait": path_gaits,
                           "RootPos": root_xform_pos,
                           "RootDir": root_xform_dir})
    return response

########## BUFF requests ##########

def doBuff(request):
    setJointKeyframes()
    updateFrame()

    joint_pos, root_xform_x_vel, root_xform_z_vel = parseBuff(request)
    moveRootXform(root_xform_x_vel, root_xform_z_vel)
    moveJoints(joint_pos)
    # setJointKeyframes()
    # updateFrame()

def parseBuff(request):
    joint_pos = request["JointPos"]
    root_xform_x_vel = request["RootX"]
    root_xform_z_vel = request["RootZ"]
    return joint_pos, root_xform_x_vel, root_xform_z_vel

def moveRootXform(root_xform_x_vel, root_xform_z_vel):
    root_xform_pos = getRootXformPos()
    new_x = positionFromVelocity(root_xform_pos[0], root_xform_x_vel)
    new_y = 0       # TODO: Hardcoded
    new_z = positionFromVelocity(root_xform_pos[2], root_xform_z_vel)
    cmds.move(new_x, new_y, new_z, character.root, worldSpace=True)

def moveJoints(joint_pos):
    root_xform_pos = getRootXformPos()

    for i in range(len(character.joints)):
        x_offset = joint_pos[i*3+0]
        y_offset = joint_pos[i*3+1]
        z_offset = joint_pos[i*3+2]
        x_pos = root_xform_pos[0] + x_offset
        y_pos = root_xform_pos[1] + y_offset
        z_pos = root_xform_pos[2] + z_offset
        cmds.move(x_pos, y_pos, z_pos, character.joints[i], worldSpace=True)

def setJointKeyframes():
    for joint in character.joints:
        cmds.setKeyframe(joint, attribute="translate")

def updateFrame():
    now = cmds.currentTime(query=True)
    cmds.currentTime(now + 1)

########## Helper functions ##########

### Joints ###

def getRootName():
    joints = cmds.ls(type='joint')
    root = joints[0]
    found = False

    while not found:
        parent = cmds.listRelatives(root, parent=True)
        if parent is not None:
            root = parent[0]
        elif parent is None:
            found = True
    return root

def getJointNames(joints, joint):
    children = cmds.listRelatives(joint)
    if children is not None:
        for child in children:
            joints.append(child)
            joints = getJointNames(joints, child)
    return joints

### Path ###

# TODO: get from user input
def getPathName():
    path = "curve1"     # Hardcoded
    return path

### Root Xform ###

def getRootXformPos():
    ### TODO: HARDCODED NAMES
    left_hip = "JOINT_LeftUpLeg"
    right_hip = "JOINT_RightUpLeg"
    l_hip_global_pos = cmds.xform(left_hip, worldSpace=True, query=True, translation=True)
    r_hip_global_pos = cmds.xform(right_hip, worldSpace=True, query=True, translation=True)

    mid_global_pos = [0,0,0]
    for i in range(len(l_hip_global_pos)):
        mid_global_pos[i] = (l_hip_global_pos[i] + r_hip_global_pos[i]) / 2

    root_x = mid_global_pos[0]
    root_y = 0                  # TODO: Hardcoded
    root_z = mid_global_pos[2]

    return [root_x, root_y, root_z]

def getRootXformDir():
    ### TODO: HARDCODED NAMES
    left_hip = "JOINT_LeftUpLeg"
    right_hip = "JOINT_RightUpLeg"
    left_shoulder = "JOINT_LeftArm"
    right_shoulder = "JOINT_RightArm"
    l_hip_global_pos = cmds.xform(left_hip, worldSpace=True, query=True, translation=True)
    r_hip_global_pos = cmds.xform(right_hip, worldSpace=True, query=True, translation=True)
    l_shoulder_global_pos = cmds.xform(left_shoulder, worldSpace=True, query=True, translation=True)
    r_shoulder_global_pos = cmds.xform(right_shoulder, worldSpace=True, query=True, translation=True)

    v1 = []    # vector between the hips
    v2 = []    # vector between the shoulders
    for i in range(3):
        v1.append(l_hip_global_pos[i] - r_hip_global_pos[i])
        v2.append(l_shoulder_global_pos[i] - r_shoulder_global_pos[i])

    v3 = []    # average of hip and shoulder vectors
    for i in range(3):
        v3.append((v1[i] + v2[i])/2)

    # Facing direction: cross product between v3 and upward direction (0,1,0)
    root_xform_dir = crossProduct(v3, [0, 1, 0])

    return root_xform_dir

### Other ###

def crossProduct(a, b):
    c = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]]
    return c

def positionFromVelocity(initial_pos, velocity):
    time = 1    # maybe need frames? so 1/60?
    new_pos = (velocity * time) + initial_pos
    return new_pos

character = Character()

#pm.general.commandPort(name=":12345", cl=True)
