"""
Frame and Video Ingestion Module
Handles loading images, extracting frames from videos, and preparing frame pairs.
"""

import cv2
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
import config


def load_image(image_path, color_mode='BGR'):
    """
    Load a single image from file.

    Args:
        image_path (str): Path to image file
        color_mode (str): 'BGR' (default), 'RGB', or 'GRAY'

    Returns:
        np.ndarray: Loaded image, or None if loading failed

    Raises:
        FileNotFoundError: If image file doesn't exist
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Convert color space if needed
    if color_mode == 'RGB':
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    elif color_mode == 'GRAY':
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return image


def load_frame_pair(front_view_path, side_view_path, color_mode='BGR'):
    """
    Load a synchronized pair of frames (front view and side view).

    Args:
        front_view_path (str): Path to front view image
        side_view_path (str): Path to side view image
        color_mode (str): 'BGR' (default), 'RGB', or 'GRAY'

    Returns:
        tuple: (frame_front, frame_side) as numpy arrays

    Raises:
        FileNotFoundError: If either image file doesn't exist
        ValueError: If images have different dimensions
    """
    frame_front = load_image(front_view_path, color_mode)
    frame_side = load_image(side_view_path, color_mode)

    # Verify frames have same dimensions (important for stereo processing)
    if frame_front.shape[:2] != frame_side.shape[:2]:
        raise ValueError(
            f"Frame dimensions mismatch: "
            f"front={frame_front.shape[:2]}, side={frame_side.shape[:2]}"
        )

    return frame_front, frame_side


def extract_frames_from_video(video_path, output_dir, camera_name="cam",
                              frame_interval=15, max_frames=None):
    """
    Extract frames from video at regular intervals.

    Args:
        video_path (str): Path to video file
        output_dir (str): Directory to save extracted frames
        camera_name (str): Camera identifier (used in output filenames)
        frame_interval (int): Extract every Nth frame (default: 15)
        max_frames (int): Maximum number of frames to extract (None = unlimited)

    Returns:
        list: Paths to extracted frame images

    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If video cannot be opened
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    frame_paths = []
    frame_count = 0
    saved_count = 0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0

    print(f"Extracting frames from {video_path}...")
    print(f"  Video info: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s duration")
    print(f"  Extracting every {frame_interval}th frame")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Save every Nth frame
        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_dir, f"{camera_name}_frame_{saved_count:04d}.png")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
            saved_count += 1

            # Check if we've reached max frames
            if max_frames and saved_count >= max_frames:
                break

        frame_count += 1

    cap.release()
    print(f"  Extracted {saved_count} frames from {frame_count} total frames")

    return frame_paths


def load_images_from_directory(directory_path, extensions=('.png', '.jpg', '.jpeg')):
    """
    Load all image paths from a directory.

    Args:
        directory_path (str): Path to directory containing images
        extensions (tuple): Valid image file extensions

    Returns:
        list: Sorted list of image file paths

    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If no valid images found
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    if not os.path.isdir(directory_path):
        raise ValueError(f"Path is not a directory: {directory_path}")

    # Get all files with valid extensions
    image_paths = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(extensions):
            image_paths.append(os.path.join(directory_path, filename))

    if not image_paths:
        raise ValueError(
            f"No images found in {directory_path} with extensions {extensions}"
        )

    # Sort to ensure consistent ordering
    image_paths.sort()

    print(f"Found {len(image_paths)} images in {directory_path}")

    return image_paths


def validate_frame_pair_directories(dir1, dir2):
    """
    Validate that two directories contain matching frame pairs.

    Args:
        dir1 (str): Path to first directory
        dir2 (str): Path to second directory

    Returns:
        tuple: (images_dir1, images_dir2) - sorted lists of matching image paths

    Raises:
        ValueError: If directories don't contain same number of images
    """
    images_dir1 = load_images_from_directory(dir1)
    images_dir2 = load_images_from_directory(dir2)

    if len(images_dir1) != len(images_dir2):
        raise ValueError(
            f"Mismatched image counts: "
            f"{dir1} has {len(images_dir1)}, {dir2} has {len(images_dir2)}"
        )

    print(f"✓ Validated {len(images_dir1)} frame pairs")

    return images_dir1, images_dir2


def save_frame(frame, output_path):
    """
    Save a frame to disk.

    Args:
        frame (np.ndarray): Frame to save
        output_path (str): Output file path

    Returns:
        bool: True if successful, False otherwise
    """
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    success = cv2.imwrite(output_path, frame)

    if success:
        print(f"✓ Saved frame to {output_path}")
    else:
        print(f"✗ Failed to save frame to {output_path}")

    return success


def get_frame_dimensions(image_path):
    """
    Get dimensions of an image without fully loading it.

    Args:
        image_path (str): Path to image file

    Returns:
        tuple: (width, height) of image
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot read image: {image_path}")

    height, width = image.shape[:2]
    return width, height


def resize_frame(frame, target_size=None, scale_factor=None):
    """
    Resize a frame to target size or by scale factor.

    Args:
        frame (np.ndarray): Input frame
        target_size (tuple): Target (width, height), or None
        scale_factor (float): Scale factor (e.g., 0.5 for half size), or None

    Returns:
        np.ndarray: Resized frame

    Note:
        Either target_size or scale_factor must be provided, not both.
    """
    if target_size and scale_factor:
        raise ValueError("Provide either target_size or scale_factor, not both")

    if target_size:
        resized = cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)
    elif scale_factor:
        width = int(frame.shape[1] * scale_factor)
        height = int(frame.shape[0] * scale_factor)
        resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
    else:
        raise ValueError("Must provide either target_size or scale_factor")

    return resized


def detect_content_bounds(image):
    """
    Detect non-black content boundaries in an image.
    Useful for cropping Zoom recordings with black bars.

    Args:
        image (np.ndarray): Input image (BGR)

    Returns:
        tuple: (x, y, width, height) of content region, or None if detection fails
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold to find non-black pixels (anything above 10 is considered content)
    _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

    # Find contours of non-black regions
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Get bounding box of largest contour (should be the content area)
    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)

    return (x, y, w, h)


def crop_to_content(image, padding=0):
    """
    Automatically crop image to remove black bars.

    Args:
        image (np.ndarray): Input image (BGR)
        padding (int): Pixels of padding to leave around content

    Returns:
        np.ndarray: Cropped image, or original if detection fails
    """
    bounds = detect_content_bounds(image)

    if bounds is None:
        print("⚠ Warning: Could not detect content bounds, returning original image")
        return image

    x, y, w, h = bounds

    # Apply padding (but don't go outside image bounds)
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(image.shape[1] - x, w + 2 * padding)
    h = min(image.shape[0] - y, h + 2 * padding)

    cropped = image[y:y+h, x:x+w]

    print(f"✓ Cropped from {image.shape[1]}x{image.shape[0]} to {w}x{h}")
    print(f"  Removed: {y}px top, {image.shape[0]-y-h}px bottom, {x}px left, {image.shape[1]-x-w}px right")

    return cropped


def split_side_by_side_image(image_path, output_dir=None, names=('cam1', 'cam2'), auto_crop=True):
    """
    Split a side-by-side image (e.g., Zoom screenshot) into two separate images.

    Args:
        image_path (str): Path to side-by-side image
        output_dir (str): Directory to save split images (None = don't save)
        names (tuple): Names for left and right images
        auto_crop (bool): Automatically crop black bars before splitting (default: True)

    Returns:
        tuple: (left_image, right_image) as numpy arrays

    Raises:
        FileNotFoundError: If image doesn't exist
        ValueError: If image width is odd (can't split evenly)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Auto-crop black bars if requested
    if auto_crop:
        image = crop_to_content(image, padding=0)

    height, width = image.shape[:2]

    # Check if width is even
    if width % 2 != 0:
        raise ValueError(
            f"Image width ({width}) is odd - cannot split evenly. "
            f"Crop image to even width first."
        )

    # Split down the middle
    mid = width // 2
    left_image = image[:, :mid]      # Left half
    right_image = image[:, mid:]     # Right half

    # Save if output directory provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

        left_path = os.path.join(output_dir, f"{names[0]}.png")
        right_path = os.path.join(output_dir, f"{names[1]}.png")

        cv2.imwrite(left_path, left_image)
        cv2.imwrite(right_path, right_image)

        print(f"✓ Split image saved:")
        print(f"  Left ({names[0]}): {left_path}")
        print(f"  Right ({names[1]}): {right_path}")

    return left_image, right_image


def load_and_split_zoom_screenshot(screenshot_path, camera_layout='side_by_side',
                                   front_camera='left'):
    """
    Load a Zoom screenshot and extract front view and side view cameras.

    Args:
        screenshot_path (str): Path to Zoom screenshot
        camera_layout (str): 'side_by_side' (left/right) or 'stacked' (top/bottom)
        front_camera (str): 'left' or 'right' for side_by_side, 'top' or 'bottom' for stacked

    Returns:
        tuple: (frame_front, frame_side) as numpy arrays

    Raises:
        ValueError: If camera_layout or front_camera is invalid
    """
    if camera_layout == 'side_by_side':
        left, right = split_side_by_side_image(screenshot_path)

        if front_camera == 'left':
            frame_front, frame_side = left, right
        elif front_camera == 'right':
            frame_front, frame_side = right, left
        else:
            raise ValueError(f"front_camera must be 'left' or 'right', got '{front_camera}'")

    elif camera_layout == 'stacked':
        # Top/bottom split
        image = cv2.imread(screenshot_path)
        if image is None:
            raise ValueError(f"Failed to load image: {screenshot_path}")

        height = image.shape[0]
        if height % 2 != 0:
            raise ValueError(f"Image height ({height}) is odd - cannot split evenly")

        mid = height // 2
        top = image[:mid, :]
        bottom = image[mid:, :]

        if front_camera == 'top':
            frame_front, frame_side = top, bottom
        elif front_camera == 'bottom':
            frame_front, frame_side = bottom, top
        else:
            raise ValueError(f"front_camera must be 'top' or 'bottom' for stacked layout")

    else:
        raise ValueError(f"camera_layout must be 'side_by_side' or 'stacked', got '{camera_layout}'")

    print(f"✓ Loaded Zoom screenshot:")
    print(f"  Front view: {frame_front.shape}")
    print(f"  Side view: {frame_side.shape}")

    return frame_front, frame_side
