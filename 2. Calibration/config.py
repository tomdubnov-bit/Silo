"""
Configuration file for Silo-Sight Stereo Vision Deepfake Detection
All parameters and constants used across the system
"""

import numpy as np

# ============================================================================
# CALIBRATION PARAMETERS
# ============================================================================

# Checkerboard pattern dimensions (internal corners)
# 8 rows x 11 columns of squares = 7x10 internal corners
CHECKERBOARD_SIZE = (10, 7)  # (width, height) in internal corners
SQUARE_SIZE = 0.015  # Size of each square in meters (15mm)

# Physical board dimensions (for reference)
BOARD_WIDTH = 0.279  # 279mm in meters
BOARD_HEIGHT = 0.216  # 216mm in meters

# Calibration criteria for cv2.cornerSubPix and calibration termination
CALIBRATION_CRITERIA = (
    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
    30,  # max iterations
    0.001  # epsilon (convergence threshold)
)

# Stereo calibration flags
STEREO_CALIBRATION_FLAGS = (
    cv2.CALIB_FIX_INTRINSIC  # Use intrinsic parameters from individual calibrations
)

# Maximum acceptable reprojection error during calibration (pixels)
MAX_CALIBRATION_ERROR = 1.0

# Minimum number of checkerboard images needed for good calibration
MIN_CALIBRATION_IMAGES = 10

# ============================================================================
# CAMERA PARAMETERS
# ============================================================================

# Expected camera angle separation (degrees)
CAMERA_ANGLE_SEPARATION = 30

# Camera resolution (will be auto-detected but can override)
CAMERA_RESOLUTION = None  # Set to (width, height) to override, e.g., (1280, 720)

# ============================================================================
# LANDMARK DETECTION PARAMETERS
# ============================================================================

# MediaPipe Face Mesh configuration
MEDIAPIPE_CONFIG = {
    'max_num_faces': 1,
    'refine_landmarks': True,
    'min_detection_confidence': 0.5,
    'min_tracking_confidence': 0.5
}

# Key facial landmarks to use for triangulation (MediaPipe indices)
# These are stable landmarks visible from both front and side views
KEY_LANDMARKS = [
    1,    # Nose tip
    4,    # Nose bridge top
    152,  # Chin
    234,  # Left forehead
    454,  # Right forehead
    33,   # Left eye outer corner
    263,  # Right eye outer corner
    61,   # Left mouth corner
    291,  # Right mouth corner
    199,  # Nose bridge mid
]

# Alternative: Use all 468 landmarks (set to None to use KEY_LANDMARKS)
USE_ALL_LANDMARKS = False

# ============================================================================
# DETECTION THRESHOLDS
# ============================================================================

# Reprojection error thresholds (pixels)
REAL_HUMAN_THRESHOLD = 5.0  # Below this = likely real human
DEEPFAKE_THRESHOLD = 15.0   # Above this = likely deepfake

# Confidence score boundaries
MIN_CONFIDENCE = 0
MAX_CONFIDENCE = 100
HUMAN_CONFIDENCE_CUTOFF = 70  # Above this = classified as human

# ============================================================================
# FILE PATHS
# ============================================================================

# Calibration data storage
CALIBRATION_DATA_PATH = "stereo_calibration.npz"

# Output directories
CALIBRATION_OUTPUT_DIR = "2. Calibration/output"
DETECTION_OUTPUT_DIR = "6. Output"
VISUALIZATION_DIR = "6. Output/visualizations"

# ============================================================================
# VISUALIZATION PARAMETERS
# ============================================================================

# Colors (BGR format for OpenCV)
COLOR_OBSERVED = (0, 255, 0)      # Green for observed landmarks
COLOR_REPROJECTED = (0, 0, 255)   # Red for reprojected landmarks
COLOR_ERROR_LINE = (255, 0, 0)    # Blue for error lines
COLOR_TEXT = (255, 255, 255)      # White for text

# Marker sizes
LANDMARK_RADIUS = 3
LINE_THICKNESS = 1
TEXT_FONT = cv2.FONT_HERSHEY_SIMPLEX
TEXT_SCALE = 0.5
TEXT_THICKNESS = 1

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_landmark_indices():
    """
    Returns the list of landmark indices to use for detection.

    Returns:
        list: Landmark indices (0-467 for MediaPipe)
    """
    if USE_ALL_LANDMARKS:
        return list(range(468))  # All MediaPipe landmarks
    else:
        return KEY_LANDMARKS


def calculate_confidence_score(mean_error):
    """
    Convert mean reprojection error to confidence score (0-100).

    Args:
        mean_error (float): Mean reprojection error in pixels

    Returns:
        float: Confidence score (0-100)
    """
    if mean_error < REAL_HUMAN_THRESHOLD:
        confidence = MAX_CONFIDENCE
    elif mean_error > DEEPFAKE_THRESHOLD:
        confidence = MIN_CONFIDENCE
    else:
        # Linear interpolation between thresholds
        error_range = DEEPFAKE_THRESHOLD - REAL_HUMAN_THRESHOLD
        normalized_error = (mean_error - REAL_HUMAN_THRESHOLD) / error_range
        confidence = MAX_CONFIDENCE - (normalized_error * MAX_CONFIDENCE)

    return np.clip(confidence, MIN_CONFIDENCE, MAX_CONFIDENCE)


def is_deepfake(confidence_score):
    """
    Determine if subject is a deepfake based on confidence score.

    Args:
        confidence_score (float): Confidence score (0-100)

    Returns:
        bool: True if deepfake, False if real human
    """
    return confidence_score < HUMAN_CONFIDENCE_CUTOFF


# Import cv2 at the end to avoid circular dependencies in other modules
try:
    import cv2
except ImportError:
    print("Warning: OpenCV not installed. Some config parameters may not work.")
    cv2 = None
