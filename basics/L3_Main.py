import time
import random
import L2_vision as vision
import L1_motor as m
# State Definitions
SEARCH = 1
PICKUP = 2
NAVIGATE_TO_DROP = 3
DROP = 4
IDLE = 5


searchattempts = 0
state = SEARCH
previous_state = SEARCH

# Parameters
CENTER_TOLERANCE = 40       # mm of acceptable lateral error
PICK_DIST_MAX = 20          # mm distance to stop at for pickup
PICK_DIST_MIN = 10          # mm distance to stop at for pickup

# FIXED: Added missing constants for the drop zone
DROP_ZONE_CENTER_TOLERANCE = 40
DROP_ZONE_TARGET_DIST_MAX = 150


# #Move around obsticale
# motions = [
#     [0.0, turn_90, 1.5],            # Motion 1
#     [0.4, 0, 1.25],            # Motion 2
#     [0.0, turn_90, 1.5],            # Motion 3
#     [0.4, 0, 1.25],            # Motion 1
#     [0.0, turn_90, 1.5],            # Motion 2
#     [0.4, 0.0, 1.25],
#     [0.0, -turn_90, 1.5],            
#     [0.4, 0.0, 1.25],            
#     [0.0, -turn_90, 1.5],
#     [0.4, 0.0, 1.25],            
# ]



# Low level motor functions (replace with L1.py later)
def move_forward(speed=0.2):
    m.sendLeft(0.8)
    m.sendRight(0.8)
    print("Moving forward")


def move_backward(speed=0.2):
    m.sendLeft(-0.8)
    m.sendRight(-0.8)
    print("Moving backward")


def turn_right(speed=0.2):
    m.sendLeft(0.8)
    m.sendRight(-0.8)
    print("Turning right")


def turn_left(speed=0.2):
    m.sendLeft(-0.8)
    m.sendRight(0.8)
    print("Turning left")


def stop():
    m.sendLeft(0)
    m.sendRight(0)
    print("Stopping")


# Forklift logic placeholders
def lower_fork():
    print("Lowering fork")


def lift_fork():
    print("Lifting fork")


#Utility functions
def get_center_error(cx, frame_width):
    return cx - frame_width // 2


# TOP PRIORITY - Obstacle Handling
def obstacle_detected(frame): #true if object or false if no object
    return (
        vision.detect_yellow_tape(frame) or
        vision.detect_dynamic_obstacles(frame) or
        vision.detect_static_obstacles(frame)
    )


def avoid_obstacle():
    print("Obstacle detected → avoiding")
    stop()
    move_backward()
    time.sleep(0.5)


    if random.random() > 0.5:
        turn_left()
    else:
        turn_right()


    time.sleep(0.5)
    stop()


# State 1: SEARCH (Find Obj and go near it)
def search_state(frame_left, frame_right):
    obj_x_mm, obj_y_mm = vision.process_target_location(cam_left, cam_right, vision.find_target_object(frame)) # change the input of vision.find_target_object()

    if obj_y_mm >= 5:
        turn_right()
    elif obj_y_mm <= -5:
        turn_left()
    elif obj_x_mm > PICK_DIST_MAX :
        move_forward()
    elif obj_x_mm < PICK_DIST_MIN:
        move_backward()
    elif obj_y_mm <= 5 and obj_y_mm >= -5 and obj_x_mm <= PICK_DIST_MAX and drop_x_mm >= PICK_DIST_MIN:
        stop()
        return PICKUP
    else:
        searchattempts += 1
        # Object not visible — rotate in place to search
        print("Object not visible → searching...")
       
        if searchattempts >= 4: #if robot has tried searching 4 times in a row it needs to move
            move_forward()
            if obstacle_detected(frame_left):
                avoid_obstacle()
            searchattempts = 0
        else:
            turn_left()
            time.sleep(2.5)
            stop()

    return SEARCH

# State 2: PICKUP
def pickup_state():
    print("Picking up object")
    stop()

    m.lift(0.4)  # up speed
    time.sleep(2)
    m.lift(0)    # stop lift

    return NAVIGATE_TO_DROP


# State 3: NAVIGATE TO DROP
def navigate_to_drop_state(frame_left, frame_right):
    drop_x_mm, drop_y_mm = vision.process_target_location(cam_left, cam_right, vision.find_target_area(frame)) # change the input of vision.find_target_area()

    if drop_y_mm >= 5:
        turn_right()
    elif drop_y_mm <= -5:
        turn_left()

    elif drop_x_mm > DROP_ZONE_TARGET_DIST_MAX :
        move_forward()
    elif drop_x_mm < DROP_ZONE_TARGET_DIST_MIN:
        move_backward()
    elif drop_y_mm <= 5 and drop_y_mm >= -5 and drop_x_mm <= DROP_ZONE_TARGET_DIST_MAX and drop_x_mm >= DROP_ZONE_TARGET_DIST_MIN:
        stop()
        return DROP
    else:
        searchattempts += 1
        # Drop zone not visible — rotate in place to search
        print("Drop zone not visible → searching...")
       
        if searchattempts >= 4: #if robot has tried searching 4 times in a row it needs to move
            move_forward()
            if obstacle_detected(frame_left):
                avoid_obstacle()
            searchattempts = 0
        else:
            turn_left()
            time.sleep(2.5)
            stop()

    return NAVIGATE_TO_DROP

# State 4: DROP
def drop_state():
    print("Dropping object")
    stop()

    m.lift(-0.4)  # down speed
    time.sleep(2)
    m.lift(0)    # stop lift


    move_backward()
    time.sleep(2)
    turn_right()
    time.sleep(3)   # time taken to make a u-turn

    obj_left -= 1

    if obj_left == 0:
        print("All objects delivered → transitioning to IDLE")
        stop()
        return IDLE
    elif obj_left < 0:
        print("Error: obj_left went negative!")
        stop()
        return IDLE
    else:
        print(f"{obj_left} objects remaining → transitioning to SEARCH")
        return SEARCH


# Main loop
def main_loop(camera_left, camera_right):
    global state, previous_state


    while True:
        ret_l, frame_left = camera_left.read()
        ret_r, frame_right = camera_right.read()


        if not ret_l or not ret_r:
            continue


        # --- PRIORITY OVERRIDE ---
        if obstacle_detected(frame_left):
            previous_state = state
            avoid_obstacle()
            continue


        # --- FSM EXECUTION ---
        if state == SEARCH:
            state = search_state(frame_left, frame_right)


        elif state == PICKUP:
            state = pickup_state()


        elif state == NAVIGATE_TO_DROP:
            state = navigate_to_drop_state(frame_left)


        elif state == DROP:
            state = drop_state()


        elif state == IDLE:
            stop()
            break


        time.sleep(0.05)

move_forward()
time.sleep(2)
move_backward()
time.sleep(2)
turn_left()
time.sleep(2)
turn_right()
time.sleep(2)
stop()
