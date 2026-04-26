import time
import L1_camera
import L2_vision

def run_vision_test():
    stereo_cam = L1_camera.StereoCamera()
    
    print("--- TARGET LOCATOR TEST ---")
    print("Move targets in front of the cameras. Press Ctrl+C to stop.\n")
    
    # Matching the threshold from your L3 script
    TARGET_REACHED_DIST = 150.0 

    try:
        while True:
            frame_left, frame_right = stereo_cam.get_frames()
            if frame_left is None:
                continue

            # 1. Test Object Location (For APPROACH/PICKUP states)
            obj_x, obj_y = L2_vision.process_target_location(
                frame_left, frame_right, L2_vision.find_target_object
            )

            # 2. Test Drop Zone Location (For NAVIGATE_TO_DROP/DROP states)
            # Note: Using the function name 'find_landing_zone' from our L2 script
            area_x, area_y = L2_vision.process_target_location(
                frame_left, frame_right, L2_vision.find_landing_zone 
            )

            print("\n" + "="*40)
            
            # --- EVALUATE TARGET OBJECT ---
            if obj_x is not None and obj_x != float('inf'):
                print(f"[TARGET OBJECT] Found at X: {int(obj_x)}mm | Y: {int(obj_y)}mm")
                if obj_x < TARGET_REACHED_DIST:
                    print("   -> STATE TRIGGER: Robot would execute PICKUP()")
                else:
                    if abs(obj_y) > 40: # Your CENTER_TOLERANCE
                        print("   -> STATE TRIGGER: Robot would steer to align (APPROACH)")
                    else:
                        print("   -> STATE TRIGGER: Robot would drive straight (APPROACH)")
            else:
                print("[TARGET OBJECT] Not visible.")
                print("   -> STATE TRIGGER: Robot would SEARCH (Spin/Scan)")

            print("-" * 40)

            # --- EVALUATE DROP ZONE ---
            if area_x is not None and area_x != float('inf'):
                print(f"[DROP ZONE] Found at X: {int(area_x)}mm | Y: {int(area_y)}mm")
                if area_x < TARGET_REACHED_DIST:
                    print("   -> STATE TRIGGER: Robot would execute DROP()")
                else:
                    print("   -> STATE TRIGGER: Robot would align/drive (NAVIGATE_TO_DROP)")
            else:
                print("[DROP ZONE] Not visible.")

            # Slow down the terminal output so it is easy to read
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTest aborted by user.")
    finally:
        stereo_cam.release()
        print("Cameras released safely.")

if __name__ == "__main__":
    run_vision_test()