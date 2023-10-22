from imutils.video import VideoStream
from imutils.video import FPS
import imutils
import picar
from picar import front_wheels, back_wheels
from picar.SunFounder_PCA9685 import Servo
import picar
import argparse
import time
import cv2
import numpy as np
import os

""" 
---------------------------------------------------
Initial Setup
---------------------------------------------------
"""
# How to run?: python real_time_object_detection.py --prototxt MobileNetSSD_deploy.prototxt.txt --model MobileNetSSD_deploy.caffemodel
# python real_time.py --prototxt MobileNetSSD_deploy.prototxt.txt --model MobileNetSSD_deploy.caffemodel
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--prototxt", default="MobileNetSSD_deploy.prototxt.txt",
	help="path to Caffe 'deploy' prototxt file")
ap.add_argument("-m", "--model", default="MobileNetSSD_deploy.caffemodel",
	help="path to Caffe pre-trained model")
ap.add_argument("-c", "--confidence", type=float, default=0.2,
	help="minimum probability to filter weak predictions")
args = vars(ap.parse_args())

CLASSES = ["aeroplane", "background", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

# The model from Caffe: MobileNetSSD_deploy.prototxt.txt; MobileNetSSD_deploy.caffemodel;
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])

print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
# warm up the camera for a couple of seconds
time.sleep(2.0)

# Setup Picar and arguments
picar.setup()
show_image_enable   = True
draw_circle_enable  = False
scan_enable         = True
rear_wheels_enable  = True
front_wheels_enable = True
pan_tilt_enable     = True

if (show_image_enable or draw_circle_enable) and "DISPLAY" not in os.environ:
    print('Warning: Display not found, turn off "show_image_enable" and "draw_circle_enable"')
    show_image_enable   = False
    draw_circle_enable  = False

kernel = np.ones((5,5),np.uint8)
    
# Get screen size, centerpoint, etc
SCREEN_WIDTH = 160
SCREEN_HEIGHT = 120
CENTER_X = SCREEN_WIDTH/2
CENTER_Y = SCREEN_HEIGHT/2
OBJ_SIZE_MIN = 0.1
OBJ_SIZE_MAX = 0.5


""" 
---------------------------------------------------
Camera scanning and general car setup
---------------------------------------------------
"""

# 0 = step by step(slow, stable), 1 = calculate the step(fast, unstable)
follow_mode = 1

CAMERA_STEP = 2
CAMERA_X_ANGLE = 20
CAMERA_Y_ANGLE = 20

MIDDLE_TOLERANT = 5
PAN_ANGLE_MAX   = 170
PAN_ANGLE_MIN   = 10
TILT_ANGLE_MAX  = 150
TILT_ANGLE_MIN  = 70
FW_ANGLE_MAX    = 90+30
FW_ANGLE_MIN    = 90-30

SCAN_POS = [[20, TILT_ANGLE_MIN], [50, TILT_ANGLE_MIN], [90, TILT_ANGLE_MIN], [130, TILT_ANGLE_MIN], [160, TILT_ANGLE_MIN], 
            [160, 80], [130, 80], [90, 80], [50, 80], [20, 80]]

bw = back_wheels.Back_Wheels()
fw = front_wheels.Front_Wheels()
pan_servo = Servo.Servo(1)
tilt_servo = Servo.Servo(2)
picar.setup()

fw.offset = 0
pan_servo.offset = 10
tilt_servo.offset = 0

bw.speed = 0
fw.turn(90)
pan_servo.write(90)
tilt_servo.write(90)

motor_speed = 60

def nothing(x):
    pass

def get_centerpoint(detection_box):
    x_center = (detection_box[1] + detection_box[3]) / 2
    y_center = (detection_box[0] + detection_box[2]) / 2
    center = [x_center, y_center]
    return center

def get_box_size(detection_box):
    x_length = detection_box[3] - detection_box[1]
    y_length = detection_box[2] - detection_box[0]
    area = x_length * y_length
    return area

# Reads frame and finds centerpoint and size if cat is found
def find_cat(net):
    size = 0
    center = [0, 0]
    # Load webcam image
    frame = vs.read()
    frame = imutils.resize(frame, width=400)
    (h, w) = frame.shape[:2]
	# Resize each frame
    resized_image = cv2.resize(frame, (300, 300))

    # Run inference and find centerpoint/size if cat is detected
    blob = cv2.dnn.blobFromImage(resized_image, (1/127.5), (300, 300), 127.5, swapRB=True)

    net.setInput(blob)
	# Predictions:
    predictions = net.forward()

    for i in np.arange(0, predictions.shape[2]):
        confidence = predictions[0, 0, i, 2]
        if confidence > args["confidence"]:
            if int(predictions[0, 0, i, 1]) == 7:
                box = predictions[0, 0, i, 3:7] * np.array([w, h, w, h])
                detection_box = box.astype("int")
                center = get_centerpoint[detection_box]
                size = get_box_size(detection_box)
    return center, size


""" 
---------------------------------------------------
Main running loop
- We start off by scanning the room in front of the car and searching for a cat using the find_cat() function above
- If a cat is found, the location of the cat in the frame is calculated and the wheels are moved such that the car
    "follows" the cat
---------------------------------------------------
"""

def main():
    pan_angle = 90              # initial angle for pan
    tilt_angle = 90             # initial angle for tilt
    fw_angle = 90               # initial angle for front wheels

    scan_count = 0
    print("Begin!")
    while True:
        x = 0             # x initial in the middle
        y = 0             # y initial in the middle
        size = 0             # set initial obj size to 0

        for _ in range(10):
            (tmp_x, tmp_y), tmp_size = find_cat(net)
            if tmp_size > OBJ_SIZE_MIN:
                x = tmp_x
                y = tmp_y
                size = tmp_size
                break
        
        print(x, y, size)

        # Start scanning
        if size < OBJ_SIZE_MIN:
            bw.stop()
            if scan_enable:
                #bw.stop()
                pan_angle = SCAN_POS[scan_count][0]
                tilt_angle = SCAN_POS[scan_count][1]
                if pan_tilt_enable:
                    pan_servo.write(pan_angle)
                    tilt_servo.write(tilt_angle)
                scan_count += 1
                if scan_count >= len(SCAN_POS):
                    scan_count = 0
            else:
                time.sleep(0.1)

        elif size < OBJ_SIZE_MAX:
            if follow_mode == 0:
                if abs(x - CENTER_X) > MIDDLE_TOLERANT:
                    if x < CENTER_X:                              # Cat is to the left
                        pan_angle += CAMERA_STEP
                        #print("Left   ", )
                        if pan_angle > PAN_ANGLE_MAX:
                            pan_angle = PAN_ANGLE_MAX
                    else:                                         # Cat is to the right
                        pan_angle -= CAMERA_STEP
                        #print("Right  ",)
                        if pan_angle < PAN_ANGLE_MIN:
                            pan_angle = PAN_ANGLE_MIN
                if abs(y - CENTER_Y) > MIDDLE_TOLERANT:
                    if y < CENTER_Y :                             # Cat is at the top
                        tilt_angle += CAMERA_STEP
                        #print("Top    " )
                        if tilt_angle > TILT_ANGLE_MAX:
                            tilt_angle = TILT_ANGLE_MAX
                    else:                                         # Cat is at the bottom
                        tilt_angle -= CAMERA_STEP
                        #print("Bottom ")
                        if tilt_angle < TILT_ANGLE_MIN:
                            tilt_angle = TILT_ANGLE_MIN
            else:
                delta_x = CENTER_X - x
                delta_y = CENTER_Y - y
                #print("x = %s, delta_x = %s" % (x, delta_x))
                #print("y = %s, delta_y = %s" % (y, delta_y))
                delta_pan = int(float(CAMERA_X_ANGLE) / SCREEN_WIDTH * delta_x)
                #print("delta_pan = %s" % delta_pan)
                pan_angle += delta_pan
                delta_tilt = int(float(CAMERA_Y_ANGLE) / SCREEN_HEIGHT * delta_y)
                #print("delta_tilt = %s" % delta_tilt)
                tilt_angle += delta_tilt

                if pan_angle > PAN_ANGLE_MAX:
                    pan_angle = PAN_ANGLE_MAX
                elif pan_angle < PAN_ANGLE_MIN:
                    pan_angle = PAN_ANGLE_MIN
                if tilt_angle > TILT_ANGLE_MAX:
                    tilt_angle = TILT_ANGLE_MAX
                elif tilt_angle < TILT_ANGLE_MIN:
                    tilt_angle = TILT_ANGLE_MIN
            
            if pan_tilt_enable:
                pan_servo.write(pan_angle)
                tilt_servo.write(tilt_angle)
            time.sleep(0.01)
            fw_angle = 180 - pan_angle
            if fw_angle < FW_ANGLE_MIN or fw_angle > FW_ANGLE_MAX:
                fw_angle = ((180 - fw_angle) - 90)/2 + 90
                if front_wheels_enable:
                    fw.turn(fw_angle)
                if rear_wheels_enable:
                    bw.speed = motor_speed
                    bw.backward()
            else:
                if front_wheels_enable:
                    fw.turn(fw_angle)
                if rear_wheels_enable:
                    bw.speed = motor_speed
                    bw.forward()
        else:
            bw.stop()

def destroy():
    bw.stop()
    vs.stop()

def test():
    fw.turn(90)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        destroy()
