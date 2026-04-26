import time
import random
import L2_vision as vision
import L1_motors as m
# State Definitions
SEARCH = 1
APPROACH = 2
PICKUP = 3
NAVIGATE_TO_DROP = 4
DROP = 5
IDLE = 6


searchattempts = 0


state = SEARCH
previous_state = SEARCH


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




# Parameters
CENTER_TOLERANCE = 40
TARGET_REACHED_DIST = 150  # mm (experimentally tune later)


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


# State 1: SEARCH
def search_state(frame_left, frame_right):
    center, distance = vision.get_stereo_target_distance(
        frame_left, frame_right, vision.find_target_object
    )


    searchattempts += 1
    if searchattempts >= 4: #if robot has tried searching 4 times in a row it needs to move
        move_forward()
        if obstacle_detected(frame_left):
            avoid_obstacle()
        searchattempts = 0


    if center is not None:
        print("Target found → switching to APPROACH")
        searchattempts = 0
        return APPROACH


    # Rotate to scan environment
    turn_left()
    time.sleep(2.5)
    stop()


    return SEARCH


# State 2: APPROACH
def approach_state(frame_left, frame_right):
    center, distance = vision.get_stereo_target_distance(
        frame_left, frame_right, vision.find_target_object
    )


    if center is None:
        print("Lost target → back to SEARCH")
        return SEARCH


    cx, _ = center
    frame_width = frame_left.shape[1]
    error = get_center_error(cx, frame_width)


    # Steering control
    if abs(error) > CENTER_TOLERANCE:
        if error > 0:
            turn_right()
        else:
            turn_left()
    else:
        move_forward()


    # Stop condition using stereo depth
    if distance is not None and distance < TARGET_REACHED_DIST:
        print("Target reached → PICKUP")
        stop()
        return PICKUP


    return APPROACH


# State 3: PICKUP
def pickup_state():
    print("Picking up object")
    stop()


    lower_fork()
    time.sleep(1)


    move_forward()
    time.sleep(1)
    stop()


    lift_fork()
    time.sleep(1)


    return NAVIGATE_TO_DROP


# State 4: NAVIGATE TO DROP
def navigate_to_drop_state(frame_left, frame_right):
    center, distance_mm = vision.get_stereo_target_distance(
        frame_left, frame_right, vision.find_target_area
    )
    searchattempts += 1
    if center is None:
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


    cx, _ = center
    frame_width = frame_left.shape[1]
    error = get_center_error(cx, frame_width)


    print(f"Drop zone detected | error={error:.1f}px | distance={distance_mm:.0f}mm")


    # Step 1: Align laterally before advancing
    if abs(error) > DROP_ZONE_CENTER_TOLERANCE:
        if error > 0:
            turn_right()
        else:
            turn_left()
        return NAVIGATE_TO_DROP


    # Step 2: Aligned — check depth and move forward or stop
    if distance_mm is None or distance_mm > DROP_ZONE_TARGET_DISTANCE_MM:
        move_forward()
        return NAVIGATE_TO_DROP


    # Step 3: Aligned and close enough — in position
    print("At drop zone → transitioning to DROP")
    stop()
    return DROP


# State 5: DROP
def drop_state():
    print("Dropping object")


    stop()
    lower_fork()
    time.sleep(1)


    move_backward()
    time.sleep(1)


    stop()
    return IDLE


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


        elif state == APPROACH:
            state = approach_state(frame_left, frame_right)


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
