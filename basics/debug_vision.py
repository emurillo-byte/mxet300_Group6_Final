import cv2
import L1_camera
import L2_vision

def main():
    # Initialize the stereo camera pair from L1
    stereo_cam = L1_camera.StereoCamera()
    
    print("Starting Stereo Vision Debugger. Press 'q' to quit.")
    
    try:
        while True:
            # Grab synchronized frames from both cameras
            frame_left, frame_right = stereo_cam.get_frames()
            
            if frame_left is None or frame_right is None:
                continue

            # We will draw our overlays on a copy of the left camera's frame
            display_frame = frame_left.copy()

            # --- 1. Detect Target Object & Display Distance ---
            target_object_center, target_object_dist = L2_vision.get_stereo_target_distance(
                frame_left, frame_right, L2_vision.find_target_object
            )
            
            if target_object_center:
                cx, cy = target_object_center
                cv2.circle(display_frame, (cx, cy), 10, (0, 255, 0), -1)  # Green circle for target object
                
                if target_object_dist != float('inf'):
                    cv2.putText(display_frame, f"Target Object: {target_object_dist:.1f} mm", (cx - 50, cy - 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    cv2.putText(display_frame, "Target Object: Dist Error", (cx - 50, cy - 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # --- 2. Detect Target Area & Display Distance ---
            target_area_center, target_area_dist = L2_vision.get_stereo_target_distance(
                frame_left, frame_right, L2_vision.find_target_area
            )
            
            if target_area_center:
                cx, cy = target_area_center
                cv2.circle(display_frame, (cx, cy), 10, (255, 255, 0), -1)  # Cyan circle for target area
                
                if target_area_dist != float('inf'):
                    cv2.putText(display_frame, f"Target Area: {target_area_dist:.1f} mm", (cx - 50, cy - 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                else:
                    cv2.putText(display_frame, "Target Area: Dist Error", (cx - 50, cy - 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # --- 3. Detect and Label Obstacles ---
            # We only need one camera's perspective to warn about obstacles
            y_offset = 30 

            if L2_vision.detect_yellow_tape(frame_left):
                cv2.putText(display_frame, "WARNING: YELLOW TAPE", (10, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                y_offset += 30

            if L2_vision.detect_dynamic_obstacles(frame_left):
                cv2.putText(display_frame, "WARNING: DYNAMIC OBSTACLE", (10, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2) 
                y_offset += 30

            if L2_vision.detect_static_obstacles(frame_left):
                cv2.putText(display_frame, "WARNING: STATIC OBSTACLE", (10, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # --- 4. Display the Output Windows ---
            # Show the annotated left view, and the raw right view so you can see the stereo shift
            cv2.imshow("Stereo Left (Annotated)", display_frame)
            cv2.imshow("Stereo Right (Raw)", frame_right)

            # Wait for 1 ms and check if the user pressed the 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Debugger stopped by user.")
    finally:
        stereo_cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()