"""
Split Zoom Video Helper
Splits a side-by-side Zoom recording into two separate videos, auto-cropping black bars.
"""

import cv2
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
import frame_loader


def split_zoom_video(input_path, output_prefix, auto_crop=True):
    """
    Split a side-by-side Zoom video into left and right camera videos.

    Args:
        input_path (str): Path to input video
        output_prefix (str): Prefix for output files (e.g., 'cam' → 'cam1.mp4', 'cam2.mp4')
        auto_crop (bool): Automatically detect and crop black bars

    Returns:
        tuple: (left_output_path, right_output_path)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Video not found: {input_path}")

    # Open input video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {input_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Input video: {input_path}")
    print(f"  Resolution: {original_width}x{original_height}")
    print(f"  FPS: {fps}")
    print(f"  Total frames: {total_frames}")
    print()

    # Read first frame to detect crop bounds
    ret, first_frame = cap.read()
    if not ret:
        raise ValueError("Cannot read first frame")

    # Detect content bounds
    if auto_crop:
        print("Detecting content bounds...")
        cropped_frame = frame_loader.crop_to_content(first_frame, padding=0)
        crop_height, crop_width = cropped_frame.shape[:2]
    else:
        crop_width = original_width
        crop_height = original_height
        cropped_frame = first_frame

    # Calculate split dimensions
    split_width = crop_width // 2
    split_height = crop_height

    print(f"Output resolution per camera: {split_width}x{split_height}")
    print()

    # Prepare output paths
    output_dir = os.path.dirname(input_path) or '.'
    left_output = os.path.join(output_dir, f"{output_prefix}1.mp4")
    right_output = os.path.join(output_dir, f"{output_prefix}2.mp4")

    # Create video writers
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_left = cv2.VideoWriter(left_output, fourcc, fps, (split_width, split_height))
    out_right = cv2.VideoWriter(right_output, fourcc, fps, (split_width, split_height))

    if not out_left.isOpened() or not out_right.isOpened():
        raise ValueError("Cannot create output video writers")

    # Reset video to beginning
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # Process frames
    frame_count = 0
    print("Processing frames...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Crop black bars if requested
        if auto_crop:
            frame = frame_loader.crop_to_content(frame, padding=0)

        # Split left and right
        mid = frame.shape[1] // 2
        left_frame = frame[:, :mid]
        right_frame = frame[:, mid:]

        # Write frames
        out_left.write(left_frame)
        out_right.write(right_frame)

        frame_count += 1

        # Progress indicator
        if frame_count % 100 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"  Progress: {frame_count}/{total_frames} ({progress:.1f}%)")

    # Cleanup
    cap.release()
    out_left.release()
    out_right.release()

    print()
    print(f"✓ Split complete!")
    print(f"  Left camera: {left_output}")
    print(f"  Right camera: {right_output}")
    print()

    return left_output, right_output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Split side-by-side Zoom video into two camera views"
    )
    parser.add_argument('input', type=str, help='Input video path')
    parser.add_argument('--output-prefix', type=str, default='cam',
                       help='Output file prefix (default: cam → cam1.mp4, cam2.mp4)')
    parser.add_argument('--no-auto-crop', action='store_true',
                       help='Disable automatic black bar cropping')

    args = parser.parse_args()

    try:
        split_zoom_video(
            args.input,
            args.output_prefix,
            auto_crop=not args.no_auto_crop
        )
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
