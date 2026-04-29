import time
import random
import L2_vision as vision
import L1_motor as m
import L1_camera

# State Definitions
SEARCH = 1
PICKUP = 2
NAVIGATE_TO_DROP = 3
DROP = 4
IDLE = 5

cam = L1_camera.StereoCamera()

searchattempts = 0
state = NAVIGATE_TO_DROP
previous_state = SEARCH
move_counter = 0

# Parameters
PICK_DIST_MAX = 700          # mm distance to stop at for pickup
PICK_DIST_MIN = 500        # mm distance to stop at for pickup

DROP_ZONE_TARGET_DIST_MAX = 500 #mm distance to stop at for dropoff
DROP_ZONE_TARGET_DIST_MIN = 700 #mm distance to stop at for dropoff


# Low level motor functions (replace with L1.py later)
def move_forward(speed=0.2):
    m.sendLeft(0.6)
    m.sendRight(0.9)
    print("Moving forward")


def move_backward(speed=0.2):
    m.sendLeft(-0.6)
    m.sendRight(-0.9)
    print("Moving backward")


def turn_right(speed=0.05):
    m.sendLeft(0.5)
    m.sendRight(-0.5)
    print("Turning right")


def turn_left(speed=0.05):
    m.sendLeft(-0.5)
    m.sendRight(0.5)
    print("Turning left")


def stop():
    m.sendLeft(0)
    m.sendRight(0)
    print("Stopping")


# TOP PRIORITY - Obstacle Handling
def obstacle_detected(f_left): #true if object or false if no object, !!! has bias towards left camera
    return (
        vision.detect_yellow_tape(f_left) or
        vision.detect_yellow_obstacle(f_left)
    )


def avoid_obstacle():
    print("Obstacle detected → avoiding")
    stop()
    time.sleep(1)
    turn_left()
    time.sleep(0.5)
    stop()


# State 1: SEARCH (Find Obj and go near it)
def search_state(f_left,f_right):
    global searchattempts

    obj_x_mm, obj_y_mm = vision.process_target_location(f_left, f_right, vision.find_target_object)
    print(f"obj x: ",obj_x_mm, f", obj y: ", obj_y_mm)

    if obj_y_mm is None or obj_x_mm is None:
        searchattempts += 1
        # Object not visible — rotate in place to search
        print("Object not visible → searching...")
       
        print("Search Attempts:", searchattempts),

        if searchattempts >= 18: #if robot has tried searching 4 times in a row it needs to move
            for move_counter in range(30):
                move_forward()
                if obstacle_detected(f_left):
                    avoid_obstacle()
                move_counter +=1
                time.sleep(0.1)
            searchattempts = 0
            move_counter = 0
        else:
            turn_left()
            time.sleep(0.5)
            stop()
            time.sleep(0.3)
    
    elif obj_y_mm >= 70:
        turn_right(0.03)
        time.sleep(0.05)
        stop()
        time.sleep(0.05)
    elif obj_y_mm <= 45:
        turn_left(0.03)
        time.sleep(0.05)
        stop()
        time.sleep(0.05)
    elif obj_x_mm > PICK_DIST_MAX:
        move_forward()
    elif obj_x_mm < PICK_DIST_MIN:
        move_backward()
    elif obj_y_mm <= 65 and obj_y_mm >= 50 and obj_x_mm <= PICK_DIST_MAX and obj_x_mm >= PICK_DIST_MIN:
        stop()
        return PICKUP

    return SEARCH

# State 2: PICKUP
def pickup_state():
    
    move_forward()
    time.sleep(2)
    stop()
    
    print("Picking up object")
    # pulses the lift to pick up the object reliably
    m.lift(0.7)  # up speed
    time.sleep(0.2)
    m.lift(0)
    time.sleep(0.2)
    m.lift(0.7)
    time.sleep(0.2)
    m.lift(0)
    time.sleep(0.2)
    m.lift(0.7)
    time.sleep(0.2)
    m.lift(0)

    return NAVIGATE_TO_DROP


# State 3: NAVIGATE TO DROP
def navigate_to_drop_state(f_left,f_right):
    global searchattempts

    drop_x_mm, drop_y_mm = vision.process_target_location(f_left, f_right, vision.find_target_area)
    print(f"drop x: ",drop_x_mm, f", drop y: ", drop_y_mm)


    if drop_y_mm is None or drop_x_mm is None:
        searchattempts += 1
        # Drop zone not visible — rotate in place to search
        print("Drop zone not visible → searching...")
        print("Search Attempts:", searchattempts),

        if searchattempts >= 18: #if robot has tried searching 4 times in a row it needs to move
            for move_counter in range(30):
                move_forward()
                if obstacle_detected(f_left):
                    avoid_obstacle()
                move_counter +=1
                time.sleep(0.1)
            searchattempts = 0
            move_counter = 0
        else:
            turn_left()
            time.sleep(0.5)
            stop()
            time.sleep(0.3)
    
    elif drop_y_mm >= 70:
        turn_right(0.03)
        time.sleep(0.05)
        stop()
        time.sleep(0.05)
    elif drop_y_mm <= 40:
        turn_left(0.03)
        time.sleep(0.05)
        stop()
        time.sleep(0.05)

    elif drop_x_mm > DROP_ZONE_TARGET_DIST_MAX:
        move_forward()
    elif drop_x_mm < DROP_ZONE_TARGET_DIST_MIN:
        move_backward()
    elif drop_y_mm <=70 and drop_y_mm >= 40 and drop_x_mm <= DROP_ZONE_TARGET_DIST_MAX and drop_x_mm >= DROP_ZONE_TARGET_DIST_MIN:
        stop()
        return DROP

    return NAVIGATE_TO_DROP

# State 4: DROP
def drop_state():
    print("Dropping object")
    stop()
    
    # pulses the lift to drop the object reliably
    m.lift(-0.4)  # down speed
    time.sleep(0.2)
    m.lift(0)    # stop lift
    time.sleep(0.2)
    m.lift(-0.4)
    time.sleep(0.2)
    m.lift(0)
    time.sleep(0.2)
    m.lift(-0.4)
    time.sleep(0.2)
    m.lift(0)


    move_backward()
    time.sleep(2)
    

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
def main_loop():
    global state, previous_state

    while True:
        frame_left, frame_right = cam.get_frames()
        frametup = (frame_left, frame_right)

        # --- PRIORITY OVERRIDE ---
        if obstacle_detected(frametup[0]):
            previous_state = state
            avoid_obstacle()
            continue


        # --- FSM EXECUTION ---
        if state == SEARCH:
            state = search_state(frametup[0],frametup[1])


        elif state == PICKUP:
            state = pickup_state()


        elif state == NAVIGATE_TO_DROP:
            state = navigate_to_drop_state(frametup[0],frametup[1])


        elif state == DROP:
            state = drop_state()


        elif state == IDLE:
            stop()
            break


        time.sleep(0.05)

# move_forward()
# time.sleep(2)
# move_backward()
# time.sleep(2)
# turn_left()
# time.sleep(2)
# turn_right()
# time.sleep(2)
# stop()


# 570 and 30 (x,y) values for pickup

main_loop()