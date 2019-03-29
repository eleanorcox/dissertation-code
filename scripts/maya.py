#################################################################
# Runs from inside Maya.
#################################################################

import maya.cmds as cmds
import maya.mel as mel
import json

# May want to add bufferSize flag, size of buffer for commands and results. Default 4096.
cmds.commandPort(name=":12345", pre="myServer", sourceType="mel", eo=True)

anim_frames = 15

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
        self.root = getRootName()
        self.joints = getJointNames([self.root], self.root)
        self.velocities = initialiseVels()

def myServer(str):
    json_str = str.replace("'", '"')
    request = json.loads(json_str)

    if request["RequestType"] == "GET":
        response = doGet()
        return response
    elif request["RequestType"] == "PUT":
        doPut(request)
        return "PUT acknowledged"
    elif request["RequestType"] == "BUFF":
        doBuff(request)
        return "cheese, gromit!"

def doGet():
    # Get path info
    full_path_pos, path_middle_heights = getPathPos()
    full_path_dir = getPathDir(full_path_pos)
    full_path_height = getPathHeight(full_path_pos, full_path_dir, path_middle_heights)
    # Get character info
    initial_joint_pos = getJointPos()
    initial_joint_vel = character.velocities
    # Get gait info
    full_gait = getGait()
    # Format as JSON
    response = formatGetJson(full_path_pos, full_path_dir, full_path_height, initial_joint_pos, initial_joint_vel, full_gait)
    return response

# Returns a list of [pos x, pos z] pairs
def getPathPos():
    # path = getPathName()
    path = "curve1"             # Hardcoded
    num_spans = cmds.getAttr(path + ".spans")
    points_per_span = anim_frames / num_spans

    # Assumes curve is uniformly parameterised (in most cases this is true)
    full_path_pos = []
    path_middle_heights = []
    for i in range(num_spans):
        for j in range(points_per_span):
            param = i + float(j)/float(points_per_span)
            pos = cmds.pointOnCurve(path, parameter=param, position=True)
            full_path_pos.append([pos[0], pos[2]])  # Only x and z coords needed
            path_middle_heights.append(pos[1])      # For use later in GetHeights function

    return full_path_pos, path_middle_heights

### THINK this is how directions are used in pfnn, not sure
def getPathDir(full_path_pos):
    full_path_dir = []
    for i in range(len(full_path_pos) - 1):
        x_dir = full_path_pos[i+1][0] - full_path_pos[i][0]
        z_dir = full_path_pos[i+1][1] - full_path_pos[i][1]
        direction = [x_dir, z_dir]
        full_path_dir.append(direction)

    full_path_dir.append([0,0]) # For final point on trajectory
    return full_path_dir

def getPathHeight(full_path_pos, full_path_dir, path_middle_heights):
    # With high enough sampling for path (which is needed anyway for good animation) the
    # left and right points are orthogonal to the direction of a point
    # Right now can't be bothered to do the actual maths for this, so just going to set everything to 0 for testing
    # TODO: implement properly later

    full_path_height = []
    for i in range(len(full_path_pos)):
        full_path_height.append([0, 0, 0])
    return full_path_height

# Returns a list of joint positions local to root xform
def getJointPos():
    root_xform = getRootXform()
    joint_pos = []

    for joint in character.joints:
        joint_xform = cmds.xform(joint, worldSpace=True, query=True, translation=True)
        for i in range(len(joint_xform)):
            joint_pos.append(root_xform[i] - joint_xform[i])

    return joint_pos

# TODO: full implementation from user input
def getGait():
    # For gait, 0=stand, 1=walk, 2=jog, 4=crouch, 5=jump, 6=unused (in pfnn)
    # Want gait at each point along path - i.e. at each frame
    # For now just set these to one of the values for testing, at a later date change this to get input from user
    # Will need to format for X properly in loco.py
    gait = []
    for i in range(anim_frames):
        gait.append(2)
    return gait

def formatGetJson(full_path_pos, full_path_dir, full_path_height, initial_joint_pos, initial_joint_vel, full_gait):
    response = json.dumps({"AnimFrames": anim_frames, "PathPos": full_path_pos, "PathDir": full_path_dir, "PathHeight": full_path_height, "JointPos": initial_joint_pos, "JointVel": initial_joint_vel, "Gait": full_gait})
    return response

def doPut(request):
    joint_pos, root_xform_x_vel, root_xform_z_vel = parsePut(request)
    moveRootXform(root_xform_x_vel, root_xform_z_vel)
    moveJoints(joint_pos)
    setJointKeyframes()
    updateFrame()

def doBuff(request):
    setJointKeyframes()
    updateFrame()
    joint_pos, root_xform_x_vel, root_xform_z_vel = parseBuff(request)
    moveRootXform(root_xform_x_vel, root_xform_z_vel)
    moveJoints(joint_pos)
    setJointKeyframes()
    updateFrame()

def parsePut(request):
    joint_pos = request["JointPos"]

    vel = request["RootXformVels"]
    root_xform_x_vel = float(vel[0])
    root_xform_z_vel = float(vel[1])

    return joint_pos, root_xform_x_vel, root_xform_z_vel

def parseBuff(request):
    joint_pos = request["JointPos"]
    root_xform_x_vel = request["RootX"]
    root_xform_z_vel = request["RootZ"]

    return joint_pos, root_xform_x_vel, root_xform_z_vel

def positionFromVelocity(initial_pos, velocity):
    # time = 1/120    # frames?
    time = 1
    new_pos = (velocity * time) + initial_pos
    return new_pos

def moveRootXform(root_xform_x_vel, root_xform_z_vel):
    root_xform = getRootXform()
    new_x = positionFromVelocity(root_xform[0], root_xform_x_vel)
    new_y = 0       # TODO: Hardcoded
    new_z = positionFromVelocity(root_xform[2], root_xform_z_vel)
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

def getJointNames(joints, joint):
    children = cmds.listRelatives(joint)
    if children is not None:
        for child in children:
            joints.append(child)
            joints = getJointNames(joints, child)
    return joints

def getRootName():
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
    ### TODO: HARDCODED NAMES
    left_hip = "JOINT_LHipJoint"
    right_hip = "JOINT_RHipJoint"

    left_world_xform = cmds.xform(left_hip, worldSpace=True, query=True, translation=True)
    right_world_xform = cmds.xform(right_hip, worldSpace=True, query=True, translation=True)
    hip_world_xform = [0,0,0]
    for i in range(len(left_world_xform)):
        hip_world_xform[i] = (left_world_xform[i]+right_world_xform[i]) / 2

    root_x = hip_world_xform[0]
    root_y = 0                  # TODO: Hardcoded
    root_z = hip_world_xform[2]

    return [root_x, root_y, root_z]

def initialiseVels():
    velocities = []
    for i in range(93):
        velocities.append(0)
    return velocities

character = Character()

#pm.general.commandPort(name=":12345", cl=True)
