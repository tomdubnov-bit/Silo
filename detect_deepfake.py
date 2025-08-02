"""
Silo-Sight Deepfake Detection Pipeline
Main script for detecting deepfakes using stereo vision geometric consistency.

Usage:
    python detect_deepfake.py --screenshot <path> [options]
    python detect_deepfake.py --front <path> --side <path> [options]
"""

import argparse
import sys
import os
from pathlib import Path

# Add module paths
sys.path.append(str(Path(__file__).parent))

# Import modules
import config
from Ingestion import frame_loader
from importlib import import_module

# Import detection modules
landmark_detector_module = import_module('2D Detection.landmark_detector')
triangulator_module = import_module('3D Estimation.triangulator')
error_calculator_module = import_module('Comparison.error_calculator')
scorer_module = import_module('Output.scorer')

FaceLandmarkDetector = landmark_detector_module.FaceLandmarkDetector
StereoTriangulator = triangulator_module.StereoTriangulator
ReprojectionErrorCalculator = error_calculator_module.ReprojectionErrorCalculator
DeepfakeScorer = scorer_module.DeepfakeScorer


class DeepfakeDetectionPipeline:
    """
    Complete deepfake detection pipeline.
    """

    def __init__(self, calibration_path=None, verbose=True):
        """
        Initialize detection pipeline.

        Args:
            calibration_path (str): Path to calibration file (None = use default)
            verbose (bool): Print progress messages
        """
        self.verbose = verbose
        self.calibration_path = calibration_path or config.CALIBRATION_DATA_PATH

        # Initialize modules
        if self.verbose:
            print("\nInitializing Silo-Sight Detection Pipeline...")

        self.detector = FaceLandmarkDetector()
        self.triangulator = StereoTriangulator(self.calibration_path)
        self.error_calculator = ReprojectionErrorCalculator()
        self.scorer = DeepfakeScorer()

        if self.verbose:
            print("✓ All modules initialized")

    def detect_from_screenshot(self, screenshot_path, camera_layout='side_by_side',
                               front_camera='left'):
        """
        Detect deepfake from Zoom screenshot.

        Args:
            screenshot_path (str): Path to screenshot
            camera_layout (str): 'side_by_side' or 'stacked'
            front_camera (str): Which camera is front-facing

        Returns:
            dict: Detection result
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print("Loading and splitting screenshot...")

        # Load and split screenshot
        frame_front, frame_side = frame_loader.load_and_split_zoom_screenshot(
            screenshot_path, camera_layout, front_camera
        )

        return self.detect_from_frames(frame_front, frame_side)

    def detect_from_frame_pair(self, front_path, side_path):
        """
        Detect deepfake from separate front and side view images.

        Args:
            front_path (str): Path to front view image
            side_path (str): Path to side view image

        Returns:
            dict: Detection result
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print("Loading frame pair...")

        frame_front, frame_side = frame_loader.load_frame_pair(front_path, side_path)

        return self.detect_from_frames(frame_front, frame_side)

    def detect_from_frames(self, frame_front, frame_side):
        """
        Core detection logic from loaded frames.

        Args:
            frame_front (np.ndarray): Front view frame (BGR)
            frame_side (np.ndarray): Side view frame (BGR)

        Returns:
            dict: Detection result, or None if detection failed
        """
        # Step 1: Detect landmarks
        if self.verbose:
            print(f"\n{'='*70}")
            print("Step 1: Detecting facial landmarks...")

        landmarks_front, landmarks_side = self.detector.detect_landmarks_pair(
            frame_front, frame_side
        )

        if landmarks_front is None or landmarks_side is None:
            print("✗ Face detection failed - cannot proceed")
            return None

        # Step 2: Triangulate 3D points
        if self.verbose:
            print(f"\n{'='*70}")
            print("Step 2: Triangulating 3D coordinates...")

        points_3d = self.triangulator.triangulate(landmarks_front, landmarks_side)

        # Step 3: Reproject to 2D
        if self.verbose:
            print(f"\n{'='*70}")
            print("Step 3: Reprojecting to 2D...")

        reprojected_front, reprojected_side = self.triangulator.reproject_landmarks(points_3d)

        # Step 4: Calculate errors
        if self.verbose:
            print(f"\n{'='*70}")
            print("Step 4: Calculating reprojection errors...")

        error_stats = self.error_calculator.calculate_mean_error(
            landmarks_front, reprojected_front,
            landmarks_side, reprojected_side
        )

        if self.verbose:
            print(f"  Mean error: {error_stats['mean_error']:.3f} pixels")

        # Step 5: Generate result
        if self.verbose:
            print(f"\n{'='*70}")
            print("Step 5: Generating detection result...")

        result = self.scorer.generate_detection_result(error_stats)

        # Store intermediate data for visualization
        result['intermediate_data'] = {
            'landmarks_front': landmarks_front,
            'landmarks_side': landmarks_side,
            'reprojected_front': reprojected_front,
            'reprojected_side': reprojected_side,
            'points_3d': points_3d
        }

        return result

    def close(self):
        """Release resources."""
        self.detector.close()


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Silo-Sight Deepfake Detection using Stereo Vision Geometry"
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--screenshot', type=str,
                            help='Path to Zoom screenshot with both cameras')
    input_group.add_argument('--front', type=str,
                            help='Path to front view image (use with --side)')

    parser.add_argument('--side', type=str,
                       help='Path to side view image (use with --front)')

    # Screenshot options
    parser.add_argument('--layout', type=str, default='side_by_side',
                       choices=['side_by_side', 'stacked'],
                       help='Camera layout in screenshot (default: side_by_side)')
    parser.add_argument('--front-camera', type=str, default='left',
                       choices=['left', 'right', 'top', 'bottom'],
                       help='Which camera is front-facing (default: left)')

    # Calibration
    parser.add_argument('--calibration', type=str, default=config.CALIBRATION_DATA_PATH,
                       help='Path to calibration file')

    # Output options
    parser.add_argument('--output-json', type=str,
                       help='Save result to JSON file')
    parser.add_argument('--output-csv', type=str,
                       help='Append result to CSV file')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress messages')

    args = parser.parse_args()

    # Validate inputs
    if args.front and not args.side:
        parser.error("--front requires --side")
    if args.side and not args.front:
        parser.error("--side requires --front")

    # Initialize pipeline
    try:
        pipeline = DeepfakeDetectionPipeline(
            calibration_path=args.calibration,
            verbose=not args.quiet
        )
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease run stereo calibration first:")
        print("  cd Calibration")
        print("  python stereo_calibrate.py --cam1 video1.mp4 --cam2 video2.mp4")
        sys.exit(1)

    # Run detection
    try:
        if args.screenshot:
            result = pipeline.detect_from_screenshot(
                args.screenshot,
                camera_layout=args.layout,
                front_camera=args.front_camera
            )
        else:
            result = pipeline.detect_from_frame_pair(args.front, args.side)

        if result is None:
            print("\n✗ Detection failed")
            sys.exit(1)

        # Display result
        print(pipeline.scorer.format_console_output(result))

        # Save outputs
        if args.output_json:
            pipeline.scorer.save_result_json(result, args.output_json)

        if args.output_csv:
            pipeline.scorer.save_result_csv(result, args.output_csv)

        # Exit code based on detection
        exit_code = 1 if result['detection']['is_deepfake'] else 0
        sys.exit(exit_code)

    except Exception as e:
        print(f"\n✗ Error during detection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
