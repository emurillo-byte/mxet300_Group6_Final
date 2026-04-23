import cv2
import numpy as np

# --- STEREO CALIBRATION CONSTANTS ---
# You must calibrate these for your specific cameras!
BASELINE_MM = 225.0  # Distance between the two camera lenses in mm
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

# Background subtractor to detect moving (dynamic) obstacles
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=50, detectShadows=False)

def get_color_mask(frame, lower_hsv, upper_hsv):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, lower_hsv, upper_hsv)

def _get_largest_contour_center(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, 0
    
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    if area > 300:  # Minimum size to avoid noise
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy), area
    return None, 0

def find_target_object(frame):
    # Generalized target object detection using HSV filters
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV_FILTERS["target_object"]["lower"], HSV_FILTERS["target_object"]["upper"])
    return _get_largest_contour_center(mask)

def find_target_area(frame):
    # Generalized target area detection using HSV filters
    lower_color = HSV_FILTERS["target_area"]["lower"]
    upper_color = HSV_FILTERS["target_area"]["upper"]
    mask = get_color_mask(frame, lower_color, upper_color)
    return _get_largest_contour_center(mask)

def detect_yellow_tape(frame):
    lower_yellow = HSV_FILTERS["yellow_tape"]["lower"]
    upper_yellow = HSV_FILTERS["yellow_tape"]["upper"]
    mask = get_color_mask(frame, lower_yellow, upper_yellow)
    
    # Only check the bottom half of the image (ground)
    h, w = mask.shape
    bottom_half = mask[int(h * 0.6):h, :]
    if cv2.countNonZero(bottom_half) > 1000:  # Trigger threshold for tape
        return True
    return False

def detect_dynamic_obstacles(frame):
    fg_mask = bg_subtractor.apply(frame)
    # Filter noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
    
    # If a significant number of pixels are moving, there's a dynamic obstacle
    if cv2.countNonZero(fg_mask) > 5000: 
        return True
    return False

def detect_static_obstacles(frame):
    # Use Canny edge detection for large feature outlines (boxes, walls)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Look at the center-forward trajectory area
    h, w = edges.shape
    roi = edges[int(h * 0.3):int(h * 0.7), int(w * 0.2):int(w * 0.8)]
    if cv2.countNonZero(roi) > 3000:  # Substantial blocking edges
        return True
    return False

def calculate_depth(cx_left, cx_right):
    """Calculates distance in millimeters using stereo disparity."""
    disparity = cx_left - cx_right
    
    # Avoid division by zero if the object is infinitely far away or math fails
    if disparity <= 0:
        return float('inf') 
        
    distance_mm = (BASELINE_MM * FOCAL_LENGTH_PIXELS) / disparity
    return distance_mm

def get_stereo_target_distance(frame_left, frame_right, target_function):
    """Passes both frames to a detection function and calculates depth."""
    center_left, _ = target_function(frame_left)
    center_right, _ = target_function(frame_right)
    
    if center_left and center_right:
        # Calculate distance
        distance = calculate_depth(center_left[0], center_right[0])
        # Return the left center for steering, and the actual distance for stopping
        return center_left, distance
    return None, None