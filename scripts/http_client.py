#################################################################
# Testing http networking.
# This is the CLIENT, run from a terminal.
# Currently makes a GET request then a POST request
#################################################################
import httplib
import sys

connection = httplib.HTTPConnection('localhost', 12345)
print(connection)
connection.request("GET", "/")
response = connection.getresponse()
data = response.read()
print(data)
connection.close()


connection = httplib.HTTPConnection('localhost', 12345)
#body = "CMD #polyCube -w 1 -h 1 -d 1 -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;" #MEL
body = "polyCube -w 1 -h 1 -d 1 -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;" #Python
headers = {"Content-Type": "text/plain"}
connection.request("POST", "/", body, headers)
response2 = connection.getresponse()
data2 = response2.read()
print(data2)

connection.close()
