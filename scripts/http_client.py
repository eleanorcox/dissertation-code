#################################################################
# Testing http networking.
# This is the CLIENT, run from a terminal.
# Makes a GET request then a POST request
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

# After some experimentation it appears I need to open and close the connection
# between each request. (Or, at least, this was a way around a lot of the problems
# I was having)

connection = httplib.HTTPConnection('localhost', 12345)
#body = "CMD #polyCube -w 1 -h 1 -d 1 -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;" #Send to MEL script
body = "polyCube -w 1 -h 1 -d 1 -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;" #Send to Python script
headers = {"Content-Type": "text/plain"}
connection.request("POST", "/", body, headers)
response2 = connection.getresponse()
data2 = response2.read()
print(data2)

connection.close()
