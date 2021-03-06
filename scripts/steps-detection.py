# -*- coding: utf-8 -*-
"""
Created on Wed Sep  7 15:34:11 2016

Assignment A1 : Step Detection

@author: cs390mb

This Python script receives incoming accelerometer data through the
server, detects step events and sends them back to the server for
visualization/notifications.

Refer to the assignment details at ... For a beginner's
tutorial on coding in Python, see goo.gl/aZNg0q.

"""

import socket
import sys
import json
import threading
import numpy as np

user_id = "b9.49.29.1f.91.78.ea.3d.e9.35"

count = 0
xBuffer = []
yBuffer = []
zBuffer = []
windowStartTime = 0
windowLength = 2000
marginError = 0

'''
    This socket is used to send data back through the data collection server.
    It is used to complete the authentication. It may also be used to send
    data or notifications back to the phone, but we will not be using that
    functionality in this assignment.
'''
send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_socket.connect(("none.cs.umass.edu", 9999))

def onStepDetected(timestamp):
    """
    Notifies the client that a step has been detected.
    """
    send_socket.send(json.dumps({'user_id' : user_id, 'sensor_type' : 'SENSOR_SERVER_MESSAGE', 'message' : 'SENSOR_STEP', 'data': {'timestamp' : timestamp}}) + "\n")

def detectSteps(timestamp, filteredValues):
    """
    Accelerometer-based step detection algorithm.

    In assignment A1, you will implement your step detection algorithm.
    This may be functionally equivalent to your Java step detection
    algorithm if you like. Remember to use the global keyword if you
    would like to access global variables such as counters or buffers.
    When a step has been detected, call the onStepDetected method, passing
    in the timestamp.
    """
    # TODO: Step detection algorithm
    global xBuffer
    global yBuffer
    global zBuffer
    global windowStartTime
    global windowLength
    global marginError

    if not xBuffer:
        windowStartTime = timestamp
    
    xBuffer.append((filteredValues[0],timestamp))
    yBuffer.append((filteredValues[1],timestamp))
    zBuffer.append((filteredValues[2],timestamp))

    if abs(timestamp - windowStartTime) > windowLength:
        xRange=findMax(xBuffer) - findMin(xBuffer)
        yRange=findMax(yBuffer) - findMin(yBuffer)
        zRange=findMax(zBuffer) - findMin(zBuffer)
        maxRange = max(xRange,yRange,zRange)
        if maxRange == xRange:
            buff = xBuffer
        elif maxRange == yRange:
            buff = yBuffer
        else:
            buff = zBuffer
            
        maxB = findMax(buff)
        minB = findMin(buff)
        
        marginError = 0.05*(maxB-minB)
        average = (maxB+minB)/2
        upperBound = (average + marginError)
        lowerBound = (average - marginError)
        isHigher = (buff[0][0] >= upperBound)
        lastTimestamp = buff[0][1]
        temp = buff[1:]
        for elem in temp:
            if isHigher:
                if elem[0] < lowerBound and abs(lastTimestamp - elem[1]) > 0.3:
                    print (maxB-minB)                    
                    if (maxB - minB) > 3.60:                  
                        isHigher = False
                        print "step"
                        onStepDetected(elem[1])
                        lastTimestamp = elem[1]
                    
            else:
                if elem[0] > upperBound:
                    isHigher = True
                    
                    
        xBuffer = []    
        yBuffer = []    
        zBuffer = []   
        
        
def findMax(arr):
    curMax = arr[0][0]
    for (point,time) in arr:
        if point > curMax:
            curMax = point
    return curMax
    
def findMin(arr):
    curMin = arr[0][0]
    for (point,time) in arr:
        if point < curMin:
            curMin = point
    return curMin
    



#################   Server Connection Code  ####################

'''
    This socket is used to receive data from the data collection server
'''
receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_socket.connect(("none.cs.umass.edu", 8888))
# ensures that after 1 second, a keyboard interrupt will close
receive_socket.settimeout(1.0)

msg_request_id = "ID"
msg_authenticate = "ID,{}\n"
msg_acknowledge_id = "ACK"

def authenticate(sock):
    """
    Authenticates the user by performing a handshake with the data collection server.

    If it fails, it will raise an appropriate exception.
    """
    message = sock.recv(256).strip()
    if (message == msg_request_id):
        print("Received authentication request from the server. Sending authentication credentials...")
        sys.stdout.flush()
    else:
        print("Authentication failed!")
        raise Exception("Expected message {} from server, received {}".format(msg_request_id, message))
    sock.send(msg_authenticate.format(user_id))

    try:
        message = sock.recv(256).strip()
    except:
        print("Authentication failed!")
        raise Exception("Wait timed out. Failed to receive authentication response from server.")

    if (message.startswith(msg_acknowledge_id)):
        ack_id = message.split(",")[1]
    else:
        print("Authentication failed!")
        raise Exception("Expected message with prefix '{}' from server, received {}".format(msg_acknowledge_id, message))

    if (ack_id == user_id):
        print("Authentication successful.")
        sys.stdout.flush()
    else:
        print("Authentication failed!")
        raise Exception("Authentication failed : Expected user ID '{}' from server, received '{}'".format(user_id, ack_id))


try:
    print("Authenticating user for receiving data...")
    sys.stdout.flush()
    authenticate(receive_socket)

    print("Authenticating user for sending data...")
    sys.stdout.flush()
    authenticate(send_socket)

    print("Successfully connected to the server! Waiting for incoming data...")
    sys.stdout.flush()

    previous_json = ''

    while True:
        try:
            message = receive_socket.recv(1024).strip()
            json_strings = message.split("\n")
            json_strings[0] = previous_json + json_strings[0]
            for json_string in json_strings:
                try:
                    data = json.loads(json_string)
                except:
                    previous_json = json_string
                    continue
                previous_json = '' # reset if all were successful
                sensor_type = data['sensor_type']
                if (sensor_type == u"SENSOR_ACCEL"):
                    t=data['data']['t']
                    x=data['data']['x']
                    y=data['data']['y']
                    z=data['data']['z']

                    processThread = threading.Thread(target=detectSteps, args=(t,[x,y,z]))
                    processThread.start()

            sys.stdout.flush()
        except KeyboardInterrupt:
            # occurs when the user presses Ctrl-C
            print("User Interrupt. Quitting...")
            break
        except Exception as e:
            # ignore exceptions, such as parsing the json
            # if a connection timeout occurs, also ignore and try again. Use Ctrl-C to stop
            # but make sure the error is displayed so we know what's going on
            if (e.message != "timed out"):  # ignore timeout exceptions completely
                print(e)
            pass
except KeyboardInterrupt:
    # occurs when the user presses Ctrl-C
    print("User Interrupt. Quitting...")
finally:
    print >>sys.stderr, 'closing socket for receiving data'
    receive_socket.shutdown(socket.SHUT_RDWR)
    receive_socket.close()

    print >>sys.stderr, 'closing socket for sending data'
    send_socket.shutdown(socket.SHUT_RDWR)
    send_socket.close()
