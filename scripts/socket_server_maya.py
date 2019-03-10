#################################################################
# Runs from inside Maya.
#################################################################

import pymel.core as pm
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

def myServer(str):
    json_str = str.replace("'", '"')
    request = json.loads(json_str)

    if request["RequestType"] == "GET":
        print("Request is a GET!")
        return "GET received"
    elif request["RequestType"] == "PUT":
        print("Request is a PUT!")
        return "PUT received"

#pm.general.commandPort(name=":12345", cl=True)
