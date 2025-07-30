"""
Stereo Camera Calibration Script
Performs stereo calibration using checkerboard pattern to compute camera parameters.

Usage:
    python stereo_calibrate.py --cam1 <video_path> --cam2 <video_path>
    OR
    python stereo_calibrate.py --cam1_dir <images_dir> --cam2_dir <images_dir>
"""

import cv2
import numpy as np
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
import config

class StereoCalibrator:
    """
    Handles stereo camera calibration using checkerboard pattern.
    """

    def __init__(self, checkerboard_size=None, square_size=None):
        """
        Initialize the calibrator.

        Args:
            checkerboard_size (tuple): (width, height) in internal corners
            square_size (float): Size of each square in meters
        """
        self.checkerboard_size = checkerboard_size or config.CHECKERBOARD_SIZE
        self.square_size = square_size or config.SQUARE_SIZE
        self.criteria = config.CALIBRATION_CRITERIA

        # Prepare object points for checkerboard (3D points in real world space)
        self.objp = np.zeros((self.checkerboard_size[0] * self.checkerboard_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:self.checkerboard_size[0],
                                     0:self.checkerboard_size[1]].T.reshape(-1, 2)
        self.objp *= self.square_size

        # Storage for object points and image points from all images
        self.objpoints = []  # 3D points in real world space
        self.imgpoints_cam1 = []  # 2D points in camera 1 image plane
        self.imgpoints_cam2 = []  # 2D points in camera 2 image plane

        # Image size (will be set when first image is processed)
        self.image_size = None

    def find_checkerboard_corners(self, image, camera_name="Camera"):
        """
        Find checkerboard corners in an image.

        Args:
            image (np.ndarray): Input image (color or grayscale)
            camera_name (str): Name for logging purposes

        Returns:
            tuple: (success, corners) where success is bool and corners is np.ndarray
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Find the checkerboard corners
        ret, corners = cv2.findChessboardCorners(
            gray,
            self.checkerboard_size,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        # If found, refine corner positions to sub-pixel accuracy
        if ret:
            corners_refined = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), self.criteria
            )
            print(f"  ✓ {camera_name}: Checkerboard detected ({len(corners_refined)} corners)")
            return True, corners_refined
        else:
            print(f"  ✗ {camera_name}: Checkerboard not detected")
            return False, None

    def extract_frames_from_video(self, video_path, output_dir, camera_name="cam1", frame_interval=15):
        """
        Extract frames from calibration video at regular intervals.

        Args:
            video_path (str): Path to video file
            output_dir (str): Directory to save extracted frames
            camera_name (str): Camera identifier
            frame_interval (int): Extract every Nth frame

        Returns:
            list: Paths to extracted frame images
        """
        os.makedirs(output_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        frame_paths = []
        frame_count = 0
        saved_count = 0

        print(f"Extracting frames from {video_path}...")

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

            frame_count += 1

        cap.release()
        print(f"Extracted {saved_count} frames from {frame_count} total frames")

        return frame_paths

    def calibrate_single_camera(self, image_paths, camera_name="Camera"):
        """
        Calibrate a single camera using checkerboard images.

        Args:
            image_paths (list): List of paths to calibration images
            camera_name (str): Camera identifier for logging

        Returns:
            tuple: (ret, camera_matrix, dist_coeffs, rvecs, tvecs, valid_indices)
        """
        objpoints = []
        imgpoints = []
        valid_indices = []

        print(f"\n{'='*60}")
        print(f"Calibrating {camera_name}")
        print(f"{'='*60}")

        for idx, img_path in enumerate(image_paths):
            image = cv2.imread(img_path)
            if image is None:
                print(f"  ✗ Cannot read image: {img_path}")
                continue

            # Set image size from first valid image
            if self.image_size is None:
                self.image_size = (image.shape[1], image.shape[0])

            # Find checkerboard corners
            ret, corners = self.find_checkerboard_corners(image, camera_name)

            if ret:
                objpoints.append(self.objp)
                imgpoints.append(corners)
                valid_indices.append(idx)

        # Perform camera calibration
        if len(objpoints) < config.MIN_CALIBRATION_IMAGES:
            raise ValueError(
                f"Not enough valid calibration images for {camera_name}. "
                f"Found {len(objpoints)}, need at least {config.MIN_CALIBRATION_IMAGES}"
            )

        print(f"\nRunning calibration for {camera_name} with {len(objpoints)} images...")
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, self.image_size, None, None
        )

        # Calculate reprojection error
        mean_error = 0
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(
                objpoints[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs
            )
            error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            mean_error += error
        mean_error /= len(objpoints)

        print(f"\n{camera_name} Calibration Results:")
        print(f"  Mean reprojection error: {mean_error:.4f} pixels")
        print(f"  Camera matrix:\n{camera_matrix}")
        print(f"  Distortion coefficients: {dist_coeffs.ravel()}")

        if mean_error > config.MAX_CALIBRATION_ERROR:
            print(f"  ⚠ Warning: Reprojection error exceeds threshold ({config.MAX_CALIBRATION_ERROR}px)")

        return ret, camera_matrix, dist_coeffs, rvecs, tvecs, valid_indices

    def calibrate_stereo(self, images_cam1, images_cam2):
        """
        Perform stereo calibration on two camera image sets.

        Args:
            images_cam1 (list): List of image paths from camera 1
            images_cam2 (list): List of image paths from camera 2

        Returns:
            dict: Calibration results containing all parameters
        """
        if len(images_cam1) != len(images_cam2):
            raise ValueError("Camera 1 and Camera 2 must have same number of images")

        print(f"\n{'='*60}")
        print(f"STEREO CALIBRATION")
        print(f"{'='*60}")
        print(f"Checkerboard: {self.checkerboard_size[0]}x{self.checkerboard_size[1]} corners")
        print(f"Square size: {self.square_size*1000}mm")
        print(f"Total image pairs: {len(images_cam1)}")

        # First, calibrate each camera individually
        print("\nStep 1: Individual Camera Calibration")
        ret1, K1, dist1, rvecs1, tvecs1, valid_idx1 = self.calibrate_single_camera(
            images_cam1, "Camera 1 (Front)"
        )
        ret2, K2, dist2, rvecs2, tvecs2, valid_idx2 = self.calibrate_single_camera(
            images_cam2, "Camera 2 (Side)"
        )

        # Find common valid images (where checkerboard was detected in both views)
        print("\nStep 2: Finding synchronized frame pairs...")
        common_indices = sorted(set(valid_idx1) & set(valid_idx2))
        print(f"Found {len(common_indices)} synchronized pairs where checkerboard detected in both views")

        if len(common_indices) < config.MIN_CALIBRATION_IMAGES:
            raise ValueError(
                f"Not enough synchronized pairs for stereo calibration. "
                f"Found {len(common_indices)}, need at least {config.MIN_CALIBRATION_IMAGES}"
            )

        # Collect object points and image points for common images
        objpoints_stereo = []
        imgpoints_cam1_stereo = []
        imgpoints_cam2_stereo = []

        for idx in common_indices:
            img1 = cv2.imread(images_cam1[idx])
            img2 = cv2.imread(images_cam2[idx])

            ret1, corners1 = self.find_checkerboard_corners(img1, f"Pair {idx} - Cam1")
            ret2, corners2 = self.find_checkerboard_corners(img2, f"Pair {idx} - Cam2")

            if ret1 and ret2:
                objpoints_stereo.append(self.objp)
                imgpoints_cam1_stereo.append(corners1)
                imgpoints_cam2_stereo.append(corners2)

        # Perform stereo calibration
        print(f"\nStep 3: Stereo calibration with {len(objpoints_stereo)} pairs...")

        flags = cv2.CALIB_FIX_INTRINSIC

        ret, K1, dist1, K2, dist2, R, T, E, F = cv2.stereoCalibrate(
            objpoints_stereo,
            imgpoints_cam1_stereo,
            imgpoints_cam2_stereo,
            K1, dist1,
            K2, dist2,
            self.image_size,
            criteria=self.criteria,
            flags=flags
        )

        # Compute projection matrices
        # P1 = K1 [I|0]
        # P2 = K2 [R|T]
        P1 = K1 @ np.hstack([np.eye(3), np.zeros((3, 1))])
        P2 = K2 @ np.hstack([R, T])

        print(f"\n{'='*60}")
        print(f"STEREO CALIBRATION COMPLETE")
        print(f"{'='*60}")
        print(f"Stereo RMS error: {ret:.4f} pixels")
        print(f"\nRotation matrix R:\n{R}")
        print(f"\nTranslation vector T:\n{T.ravel()}")
        print(f"\nBaseline (camera separation): {np.linalg.norm(T):.4f} meters")

        # Package results
        calibration_results = {
            'K1': K1,
            'K2': K2,
            'dist1': dist1,
            'dist2': dist2,
            'R': R,
            'T': T,
            'E': E,
            'F': F,
            'P1': P1,
            'P2': P2,
            'image_size': self.image_size,
            'rms_error': ret,
            'checkerboard_size': self.checkerboard_size,
            'square_size': self.square_size
        }

        return calibration_results

    def save_calibration(self, calibration_results, output_path=None):
        """
        Save calibration results to file.

        Args:
            calibration_results (dict): Calibration parameters
            output_path (str): Path to save file (default: config.CALIBRATION_DATA_PATH)
        """
        output_path = output_path or config.CALIBRATION_DATA_PATH

        np.savez(
            output_path,
            K1=calibration_results['K1'],
            K2=calibration_results['K2'],
            dist1=calibration_results['dist1'],
            dist2=calibration_results['dist2'],
            R=calibration_results['R'],
            T=calibration_results['T'],
            E=calibration_results['E'],
            F=calibration_results['F'],
            P1=calibration_results['P1'],
            P2=calibration_results['P2'],
            image_size=calibration_results['image_size'],
            rms_error=calibration_results['rms_error']
        )

        print(f"\n✓ Calibration data saved to: {output_path}")

    @staticmethod
    def load_calibration(calibration_path=None):
        """
        Load calibration data from file.

        Args:
            calibration_path (str): Path to calibration file

        Returns:
            dict: Calibration parameters
        """
        calibration_path = calibration_path or config.CALIBRATION_DATA_PATH

        if not os.path.exists(calibration_path):
            raise FileNotFoundError(f"Calibration file not found: {calibration_path}")

        data = np.load(calibration_path)

        return {
            'K1': data['K1'],
            'K2': data['K2'],
            'dist1': data['dist1'],
            'dist2': data['dist2'],
            'R': data['R'],
            'T': data['T'],
            'E': data['E'],
            'F': data['F'],
            'P1': data['P1'],
            'P2': data['P2'],
            'image_size': tuple(data['image_size']),
            'rms_error': float(data['rms_error'])
        }


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Stereo Camera Calibration")
    parser.add_argument('--cam1', type=str, help='Path to Camera 1 video file')
    parser.add_argument('--cam2', type=str, help='Path to Camera 2 video file')
    parser.add_argument('--cam1_dir', type=str, help='Directory with Camera 1 images')
    parser.add_argument('--cam2_dir', type=str, help='Directory with Camera 2 images')
    parser.add_argument('--output', type=str, default=config.CALIBRATION_DATA_PATH,
                       help='Output path for calibration data')
    parser.add_argument('--frame_interval', type=int, default=15,
                       help='Extract every Nth frame from video (default: 15)')

    args = parser.parse_args()

    calibrator = StereoCalibrator()

    # Get image lists
    if args.cam1 and args.cam2:
        # Extract frames from videos
        print("Mode: Video input")
        temp_dir = "2. Calibration/temp_frames"
        images_cam1 = calibrator.extract_frames_from_video(
            args.cam1, os.path.join(temp_dir, "cam1"), "cam1", args.frame_interval
        )
        images_cam2 = calibrator.extract_frames_from_video(
            args.cam2, os.path.join(temp_dir, "cam2"), "cam2", args.frame_interval
        )
    elif args.cam1_dir and args.cam2_dir:
        # Use existing images
        print("Mode: Image directory input")
        images_cam1 = sorted([
            os.path.join(args.cam1_dir, f) for f in os.listdir(args.cam1_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        images_cam2 = sorted([
            os.path.join(args.cam2_dir, f) for f in os.listdir(args.cam2_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
    else:
        parser.print_help()
        sys.exit(1)

    # Perform calibration
    try:
        results = calibrator.calibrate_stereo(images_cam1, images_cam2)
        calibrator.save_calibration(results, args.output)

        print("\n" + "="*60)
        print("SUCCESS! Stereo calibration complete.")
        print("="*60)
        print(f"\nNext steps:")
        print(f"1. Verify calibration quality (RMS error < {config.MAX_CALIBRATION_ERROR}px)")
        print(f"2. Do NOT move the cameras after calibration")
        print(f"3. Proceed to frame capture and deepfake detection")

    except Exception as e:
        print(f"\n✗ Calibration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
