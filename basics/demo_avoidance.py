import cv2
import time
import L1_motor as m
import L2_vision as vision

# --- DRIVING CONSTANTS ---
SPEED = 0.5

def move_forward():
    m.set_speeds(SPEED, SPEED)

def avoid_obstacle(reason):
    print(f"🛑 [ALERT] {reason} detected! Taking evasive action.")
    
    m.stop()
    time.sleep(0.5)
    
    # Back up
    m.set_speeds(-SPEED, -SPEED)
    time.sleep(1.0)
    
    # Turn right to evade
    m.set_speeds(SPEED, -SPEED)
    time.sleep(1.0)
    
    m.stop()
    print("✅ Evasion complete. Resuming forward movement.")
    time.sleep(0.5)

def run_avoidance_demo(camera_left, camera_right):
    """
    Pass your initialized left and right cameras into this function.
    """
    print("🎬 Starting Dual-Camera Obstacle Avoidance Demo...")
    print("Driving forward in 3 seconds. Step in front of either camera!")
    time.sleep(3)
    
    try:
        while True:
            # Read frames from both cameras
            ret_l, frame_left = camera_left.read()
            ret_r, frame_right = camera_right.read()
            
            if not ret_l or not ret_r:
                continue

            # --- 1. CHECK LEFT CAMERA ---
            if vision.detect_dynamic_obstacles(frame_left):
                avoid_obstacle("Left Camera: Dynamic Obstacle")
            elif vision.detect_static_obstacles(frame_left):
                avoid_obstacle("Left Camera: Static Obstacle")
            elif vision.detect_yellow_tape(frame_left):
                avoid_obstacle("Left Camera: Yellow Tape")
            
            # --- 2. CHECK RIGHT CAMERA ---
            elif vision.detect_dynamic_obstacles(frame_right):
                avoid_obstacle("Right Camera: Dynamic Obstacle")
            elif vision.detect_static_obstacles(frame_right):
                avoid_obstacle("Right Camera: Static Obstacle")
            elif vision.detect_yellow_tape(frame_right):
                avoid_obstacle("Right Camera: Yellow Tape")
            
            # --- 3. PATH IS CLEAR ---
            # If we get here, neither camera saw an obstacle. Safe to drive.
            else:
                move_forward()
            
            # Small delay to prevent overwhelming the Pi's CPU
            time.sleep(0.05)

    except KeyboardInterrupt:
        # Allows you to press Ctrl+C to safely stop the robot
        print("\n🛑 Demo manually stopped.")
    
    finally:
        m.stop()

if __name__ == "__main__":
    print("Initializing cameras for standalone test...")
    # NOTE: Adjust port numbers (0 and 2) to whatever your actual physical ports are!
    cam_left = cv2.VideoCapture(0) 
    cam_right = cv2.VideoCapture(2)
    
    # Run the demo loop
    run_avoidance_demo(cam_left, cam_right)
    
    # Clean up hardware connections
    cam_left.release()
    cam_right.release()