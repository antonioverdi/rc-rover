from picar import front_wheels, back_wheels
from picar.SunFounder_PCA9685 import Servo
import picar
from time import sleep
import cv2
import numpy as np
import picar
import os
from rover.models.research.phase1 import *

""" 
---------------------------------------------------
Initial Setup
---------------------------------------------------
"""
PATH_TO_LABELS = 'models/research/object_detection/data/mscoco_label_map.pbtxt'
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)
 
model_name = 'ssd_inception_v2_coco_2017_11_17'
detection_model = load_model(model_name)

picar.setup()
# Show image captured by camera, True to turn on, you will need #DISPLAY and it also slows the speed of tracking
show_image_enable   = False
draw_circle_enable  = False
scan_enable         = False
rear_wheels_enable  = True
front_wheels_enable = True
pan_tilt_enable     = True

if (show_image_enable or draw_circle_enable) and "DISPLAY" not in os.environ:
    print('Warning: Display not found, turn off "show_image_enable" and "draw_circle_enable"')
    show_image_enable   = False
    draw_circle_enable  = False

kernel = np.ones((5,5),np.uint8)
img = cv2.VideoCapture(-1)

# Open webcam
if not img.isOpened:
    print("not open")
else:
    print("open")
    
# Get screen size, centerpoint, etc
SCREEN_WIDTH = 160
SCREEN_HEIGHT = 120
img.set(3,SCREEN_WIDTH)
img.set(4,SCREEN_HEIGHT)
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

# Reads frame and finds centerpoint and size if cat is found
def find_cat():
    size = 0
    center = [0, 0]
    # Load webcam image
    read, image = img.read()
    if read == False:
        print("Failed to read image")

    # Run inference and find centerpoint/size if cat is detected
    output_dict = run_inference_for_single_image(detection_model, image)
    center = [0, 0]
    size = 0

    if contains_cat(output_dict):
        idx = find_index(17, output_dict)
        det_box = output_dict['detection_boxes'][idx]
        center = get_centerpoint(det_box)
        size = get_box_size(det_box)

    cv2.waitKey(5) & 0xFF

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
            (tmp_x, tmp_y), tmp_size = find_cat()
            if tmp_size > OBJ_SIZE_MIN:
                x = tmp_x
                y = tmp_y
                size = tmp_size
                break
        
        print(x, y, s)

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
                sleep(0.1)

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
            sleep(0.01)
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
    img.release()

def test():
    fw.turn(90)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        destroy()
