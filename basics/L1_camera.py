import cv2

class StereoCamera:
    def __init__(self, port_left=0, port_right=2, width=320, height=240):
        self.cap_left = cv2.VideoCapture(port_left)
        print("Left camera connected")
        self.cap_right = cv2.VideoCapture(port_right)
        print("Right camera connected")
        self.target_width = width
        self.target_height = height
        
        # Lower resolution is critical for 2 USB cameras on a Pi
        for cap in [self.cap_left, self.cap_right]:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
    def get_frames(self):
        # Grab simultaneously to minimize time delay between the two frames
        ret_l, frame_l = self.cap_left.read()
        ret_r, frame_r = self.cap_right.read()
        
        if not ret_l or not ret_r:
            return None, None
        
        # --- THE FIX: FORCE IDENTICAL RESOLUTIONS ---
        # This guarantees both coordinate planes are exactly 320x240 (or your chosen size)
        # regardless of what the physical hardware sensors captured.
        frame_l_resized = cv2.resize(frame_l, (self.target_width, self.target_height))
        frame_r_resized = cv2.resize(frame_r, (self.target_width, self.target_height))

        # ROTATE THE IMAGES 90 DEGREES TO MATCH THE PHYSICAL ORIENTATION OF THE CAMERAS ---
        frame_l_rotated = cv2.rotate(frame_l, cv2.ROTATE_90_CLOCKWISE)
        frame_r_rotated = cv2.rotate(frame_r, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        return frame_l_rotated, frame_r_rotated
        
    def release(self):
        self.cap_left.release()
        self.cap_right.release()