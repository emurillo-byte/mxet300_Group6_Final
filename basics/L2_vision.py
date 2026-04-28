import cv2
import numpy as np

# --- STEREO CALIBRATION CONSTANTS ---
# You must calibrate these for your specific cameras!
BASELINE_MM = 130.0  # Distance between the two camera lenses in mm
FOCAL_LENGTH_PIXELS = 350.0  # Estimated. Requires camera calibration to get exact number.

# HSV Filter Ranges for Calibration
HSV_FILTERS = {
    "target_object": {
        "lower": np.array([130, 20, 255]),  # Example range for red
        "upper": np.array([170, 100, 255]),
    },
    "target_area": {
        "lower": np.array([47, 47, 200]),  # Example range for blue
        "upper": np.array([86, 145, 255]),
    },
    "yellow_tape": {
        "lower": np.array([20, 37, 170]),  # Example range for yellow
        "upper": np.array([45, 90, 255]),
    },
}

# Background subtractor for dynamic obstacles
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=50, detectShadows=False)

def get_physical_coordinates(cx_left, cx_right, frame_width):
    disparity = cx_left - cx_right
    if disparity <= 0:
        return float('inf'), 0.0 
        
    # X: Forward distance in mm
    x_forward_mm = (BASELINE_MM * FOCAL_LENGTH_PIXELS) / disparity
    
    # Y: Lateral offset in mm (Negative = Left, Positive = Right)
    center_pixel = frame_width / 2.0
    pixel_offset = cx_left - center_pixel
    y_lateral_mm = (pixel_offset * x_forward_mm) / FOCAL_LENGTH_PIXELS
    
    return x_forward_mm, y_lateral_mm

def process_target_location(frame_left, frame_right, target_function):
    # Passes frames to your detection function
    center_left = target_function(frame_left)
    center_right = target_function(frame_right)
    
    if center_left and center_right:
        frame_width = frame_left.shape[1]
        x_mm, y_mm = get_physical_coordinates(center_left[0], center_right[0], frame_width)
        return x_mm, y_mm
    return None, None

# --- CORE HSV DETECTION LOGIC ---
def find_color_center(frame, lower_hsv, upper_hsv, min_area=500):
    """
    Converts frame to HSV, masks out the target color, and returns the (x, y) 
    pixel coordinates of the center of the largest object.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > min_area:
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                return (cx, cy)
                
    return None

# --- SPECIFIC TARGET FUNCTIONS ---
def find_target_object(frame):
    return find_color_center(
        frame, 
        HSV_FILTERS["target_object"]["lower"], 
        HSV_FILTERS["target_object"]["upper"], 
        min_area=400
    )

def find_target_area(frame):
    return find_color_center(
        frame, 
        HSV_FILTERS["target_area"]["lower"], 
        HSV_FILTERS["target_area"]["upper"], 
        min_area=1500
    )


# Alias to keep compatibility with older scripts that might still use the old name
find_landing_zone = find_target_area

# --- HAZARD DETECTION ---

def detect_yellow_obstacle(frame):
    h, w = frame.shape[:2]
    
    # Calculate the horizontal crop boundaries
    left_bound = int(w * 0.25)
    right_bound = int(w * 0.75)
    
    # Crop the frame: keep all height (:), crop width to middle 50%
    middle_section = frame[:, left_bound:right_bound]
    
    center = find_color_center(
        middle_section, 
        HSV_FILTERS["yellow_tape"]["lower"], 
        HSV_FILTERS["yellow_tape"]["upper"], 
        min_area=1000
    )
    
    if center is not None:
        return True
        
    return False

def detect_yellow_tape(frame):
    """
    Looks for a large yellow blob, but ONLY in the bottom 15% of the camera view
    where the floor actually is.
    """
    h, w = frame.shape[:2]
    bottom_half = frame[int(h*0.85):h, :]
    
    center = find_color_center(
        bottom_half, 
        HSV_FILTERS["yellow_tape"]["lower"], 
        HSV_FILTERS["yellow_tape"]["upper"], 
        min_area=1000
    )
    
    if center is not None:
        return True
    return False

# def detect_dynamic_obstacles(frame):
#     fg_mask = bg_subtractor.apply(frame)
#     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
#     fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
#     if cv2.countNonZero(fg_mask) > 5000: 
#         return True
#     return False

def detect_static_obstacles(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    h, w = edges.shape
    roi = edges[int(h*0.3):int(h*0.7), int(w*0.2):int(w*0.8)]
    if cv2.countNonZero(roi) > 3000:
        return True
    return False