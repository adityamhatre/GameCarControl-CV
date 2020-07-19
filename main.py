#!/usr/bin/env python

import cv2.cv2 as cv2
import imutils
import numpy as np
from imutils.video import VideoStream
from pynput.keyboard import Controller, Key

keyboard = Controller()

video = VideoStream(src=0).start()
frame = None

lb = [40, 100, 0]
rb = [255, 255, 255]


def set_lb(i, v):
    lb[i] = v


def set_rb(i, v):
    rb[i] = v


actions = ["", ""]

cv2.namedWindow('mask')

# use this for getting your own threshold values for whatever color
# cv2.createTrackbar('lower_b_0', 'mask', lb[0], 255, (lambda a: set_lb(0, a)))
# cv2.createTrackbar('lower_b_1', 'mask', lb[1], 255, (lambda a: set_lb(1, a)))
# cv2.createTrackbar('lower_b_2', 'mask', lb[2], 255, (lambda a: set_lb(2, a)))
# cv2.createTrackbar('upper_b_0', 'mask', rb[0], 255, (lambda a: set_rb(0, a)))
# cv2.createTrackbar('upper_b_1', 'mask', rb[1], 255, (lambda a: set_rb(1, a)))
# cv2.createTrackbar('upper_b_2', 'mask', rb[2], 255, (lambda a: set_rb(2, a)))


def press_key(key):
    keyboard.press(key)


def straighten():
    keyboard.release(Key.left)
    keyboard.release(Key.right)


def neutral():
    keyboard.release(Key.up)
    keyboard.release(Key.down)


def steer(slope):
    if 70 <= slope <= 105:
        actions[1] = "straight"
        straighten()
    elif slope > 105:
        actions[1] = "left"
        press_key(Key.left)
    elif slope < 70:
        actions[1] = "right"
        press_key(Key.right)


def gas(y):
    if 200 <= y <= 250:
        actions[0] = "Coasting"
        neutral()
    elif y < 200:
        actions[0] = "Accelerating"
        press_key(Key.up)
    elif y > 250:
        actions[0] = "Braking"
        press_key(Key.down)


def get_action():
    return "{} {}".format(actions[0], actions[1])


def process_wheel():
    global frame
    wheel_frame = frame.copy()

    hsv = cv2.cvtColor(wheel_frame, cv2.COLOR_BGR2HSV)

    lower_blue = np.array(lb.copy())  # [35, 100, 0]
    upper_blue = np.array(rb.copy())  # [255, 255, 255])

    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    anded_res = cv2.bitwise_and(wheel_frame, wheel_frame, mask=mask)
    contours, _ = cv2.findContours(cv2.Canny(anded_res, 255 / 3, 255), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    area_threshold = 400
    inds = []
    for i, c in enumerate(contours):
        a = cv2.contourArea(c)
        if a > area_threshold and len(inds) < 2:
            inds.append(i)

    if not inds or len(inds) != 2:
        cv2.imshow('wheel', wheel_frame)  # [165:200, 326:500])
        # cv2.imshow('mask', mask)  # [165:200, 326:500])
        return

    if cv2.contourArea(contours[inds[0]]) < cv2.contourArea(contours[inds[1]]):
        inds[0], inds[1] = inds[1], inds[0]

    moments1 = cv2.moments(contours[inds[0]])
    moments2 = cv2.moments(contours[inds[1]])

    p1 = [int(moments1["m10"] / moments1["m00"]), int(moments1["m01"] / moments1["m00"])]
    p2 = [int(moments2["m10"] / moments2["m00"]), int(moments2["m01"] / moments2["m00"])]

    cv2.circle(wheel_frame, (p1[0], p1[1]), 3, (255, 255, 255), -1)
    cv2.circle(wheel_frame, (p2[0], p2[1]), 3, (255, 255, 255), -1)

    cv2.line(wheel_frame, (p1[0], p1[1]), (p2[0], p2[1]), (0, 255, 0), 2)
    if p2[0] - p1[0] == 0:
        slope = 90
    else:
        slope = -np.rad2deg(np.arctan2((p2[1] - p1[1]), (p2[0] - p1[0]))) % 360

    cv2.drawContours(wheel_frame, contours, inds[0], (0, 0, 255), 2)
    cv2.drawContours(wheel_frame, contours, inds[1], (0, 255, 0), 2)

    cv2.putText(wheel_frame, "Steering angle: {}".format(np.round(slope)), (10, 100), cv2.FONT_HERSHEY_PLAIN, 2,
                (255, 255, 0), 2)
    cv2.putText(wheel_frame, "{}".format(get_action()), (10, 140), cv2.FONT_HERSHEY_PLAIN, 2,
                (255, 255, 0), 2)

    cv2.line(wheel_frame, (0, 200), (600, 200), (255, 255, 255), 1)
    cv2.line(wheel_frame, (0, 250), (600, 250), (255, 255, 255), 1)
    steer(slope)
    gas(p1[1])
    cv2.imshow('wheel', wheel_frame)  # [165:200, 326:500])
    # cv2.imshow('mask', mask)  # [165:200, 326:500])


while True:
    # Capture frame-by-frame
    frame = video.read()

    frame = cv2.flip(frame, 1)
    frame = cv2.medianBlur(frame, 5)
    frame = imutils.resize(frame, width=600, height=400)

    process_wheel()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
video.stop()
cv2.destroyAllWindows()
