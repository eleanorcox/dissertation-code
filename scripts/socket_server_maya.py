#################################################################
# Runs from inside Maya.
#################################################################

import pymel.core as pm
import maya.mel as mel
import json

#pm.general.commandPort(name=":12345", pre="myServer", sourceType="mel", eo=True)

# commandPort can only accept a MEL procedure as a prefix, so this acts as a wrapper for the python function myServer below.
melproc = """
global proc string myServer(string $str){
    string $formatted = substituteAllString($str, "\\"", "'");
    print($formatted);

    string $result = python(("myServer(\\"" + $formatted + "\\")"));
    return $result;
}
"""

mel.eval(melproc)

def myServer(str):
    json_str = str.replace("'", '"')
    request = json.loads(json_str)
    print(request)
    return "good"
    # if buffer[0]=="GET":        # GET request
    #     if buffer[1]=="/":
    # elif buffer[0]=="POST":     # POST request
    #     if buffer[1]=="/":

#pm.general.commandPort(name=":12345", cl=True)
