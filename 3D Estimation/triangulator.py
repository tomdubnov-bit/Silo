"""
3D Triangulation Module
Converts 2D landmark pairs from stereo views into 3D coordinates.
"""

import cv2
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
import config


class StereoTriangulator:
    """
    Performs 3D triangulation of 2D landmark pairs using stereo calibration.
    """

    def __init__(self, calibration_path=None):
        """
        Initialize triangulator with calibration data.

        Args:
            calibration_path (str): Path to calibration file (None = use config default)

        Raises:
            FileNotFoundError: If calibration file doesn't exist
        """
        calibration_path = calibration_path or config.CALIBRATION_DATA_PATH

        # Load calibration data
        self.calibration = self._load_calibration(calibration_path)

        # Extract calibration parameters
        self.K1 = self.calibration['K1']
        self.K2 = self.calibration['K2']
        self.dist1 = self.calibration['dist1']
        self.dist2 = self.calibration['dist2']
        self.R = self.calibration['R']
        self.T = self.calibration['T']
        self.P1 = self.calibration['P1']
        self.P2 = self.calibration['P2']

        print(f"✓ Loaded calibration from {calibration_path}")
        print(f"  Camera baseline: {np.linalg.norm(self.T)*100:.2f} cm")

    def _load_calibration(self, calibration_path):
        """
        Load calibration data from file.

        Args:
            calibration_path (str): Path to .npz calibration file

        Returns:
            dict: Calibration parameters

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        import os
        if not os.path.exists(calibration_path):
            raise FileNotFoundError(
                f"Calibration file not found: {calibration_path}\n"
                f"Run stereo_calibrate.py first to generate calibration data."
            )

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

    def undistort_points(self, points_cam1, points_cam2):
        """
        Undistort 2D points using camera distortion coefficients.

        Args:
            points_cam1 (np.ndarray): Nx2 array of points from camera 1
            points_cam2 (np.ndarray): Nx2 array of points from camera 2

        Returns:
            tuple: (undistorted_cam1, undistorted_cam2) as Nx2 arrays
        """
        # Reshape for cv2.undistortPoints (needs Nx1x2 format)
        points_cam1_reshaped = points_cam1.reshape(-1, 1, 2)
        points_cam2_reshaped = points_cam2.reshape(-1, 1, 2)

        # Undistort points
        undistorted_cam1 = cv2.undistortPoints(
            points_cam1_reshaped, self.K1, self.dist1, None, self.K1
        )
        undistorted_cam2 = cv2.undistortPoints(
            points_cam2_reshaped, self.K2, self.dist2, None, self.K2
        )

        # Reshape back to Nx2
        undistorted_cam1 = undistorted_cam1.reshape(-1, 2)
        undistorted_cam2 = undistorted_cam2.reshape(-1, 2)

        return undistorted_cam1, undistorted_cam2

    def triangulate(self, landmarks_cam1, landmarks_cam2, undistort=True):
        """
        Triangulate 3D points from 2D landmark pairs.

        Args:
            landmarks_cam1 (np.ndarray): Nx2 array of landmarks from camera 1 (front)
            landmarks_cam2 (np.ndarray): Nx2 array of landmarks from camera 2 (side)
            undistort (bool): Whether to undistort points first (recommended)

        Returns:
            np.ndarray: Nx3 array of 3D coordinates (X, Y, Z) in meters

        Raises:
            ValueError: If landmark arrays have different lengths
        """
        if len(landmarks_cam1) != len(landmarks_cam2):
            raise ValueError(
                f"Landmark count mismatch: cam1={len(landmarks_cam1)}, cam2={len(landmarks_cam2)}"
            )

        n_points = len(landmarks_cam1)

        # Undistort points if requested
        if undistort:
            points_cam1, points_cam2 = self.undistort_points(landmarks_cam1, landmarks_cam2)
        else:
            points_cam1, points_cam2 = landmarks_cam1, landmarks_cam2

        # Prepare points for triangulation (needs 2xN format)
        points_cam1_T = points_cam1.T.astype(np.float64)  # 2xN
        points_cam2_T = points_cam2.T.astype(np.float64)  # 2xN

        # Triangulate using cv2.triangulatePoints
        # Returns 4xN homogeneous coordinates
        points_4d_homogeneous = cv2.triangulatePoints(
            self.P1, self.P2, points_cam1_T, points_cam2_T
        )

        # Convert from homogeneous (4D) to 3D coordinates
        # Divide [X, Y, Z, W] by W to get [X/W, Y/W, Z/W]
        points_3d = points_4d_homogeneous[:3, :] / points_4d_homogeneous[3, :]

        # Transpose to Nx3 format
        points_3d = points_3d.T

        print(f"✓ Triangulated {n_points} 3D points")

        return points_3d.astype(np.float32)

    def project_3d_to_2d(self, points_3d, camera='cam1'):
        """
        Project 3D points back to 2D image coordinates (reprojection).

        Args:
            points_3d (np.ndarray): Nx3 array of 3D points
            camera (str): 'cam1' or 'cam2' to select projection matrix

        Returns:
            np.ndarray: Nx2 array of reprojected 2D points

        Raises:
            ValueError: If camera not recognized
        """
        if camera == 'cam1':
            P = self.P1
        elif camera == 'cam2':
            P = self.P2
        else:
            raise ValueError(f"camera must be 'cam1' or 'cam2', got '{camera}'")

        # Convert to homogeneous coordinates (Nx4: [X, Y, Z, 1])
        n_points = len(points_3d)
        points_3d_homogeneous = np.hstack([points_3d, np.ones((n_points, 1))])

        # Project: P @ [X, Y, Z, 1]^T
        # P is 3x4, points is Nx4, so we transpose points for matrix multiplication
        projected_homogeneous = (P @ points_3d_homogeneous.T).T  # Nx3

        # Convert from homogeneous to 2D: [x/w, y/w]
        points_2d = projected_homogeneous[:, :2] / projected_homogeneous[:, 2:3]

        return points_2d.astype(np.float32)

    def reproject_landmarks(self, points_3d):
        """
        Reproject 3D points to both camera views.

        Args:
            points_3d (np.ndarray): Nx3 array of 3D points

        Returns:
            tuple: (reprojected_cam1, reprojected_cam2) as Nx2 arrays
        """
        reprojected_cam1 = self.project_3d_to_2d(points_3d, camera='cam1')
        reprojected_cam2 = self.project_3d_to_2d(points_3d, camera='cam2')

        return reprojected_cam1, reprojected_cam2

    def get_calibration_quality(self):
        """
        Get calibration quality metrics.

        Returns:
            dict: Quality metrics including RMS error and baseline
        """
        return {
            'rms_error': self.calibration['rms_error'],
            'baseline_m': np.linalg.norm(self.T),
            'baseline_cm': np.linalg.norm(self.T) * 100,
            'image_size': self.calibration['image_size']
        }


def test_triangulation(calibration_path):
    """
    Test triangulation with synthetic data.

    Args:
        calibration_path (str): Path to calibration file
    """
    print("="*60)
    print("Testing 3D Triangulation")
    print("="*60)

    # Initialize triangulator
    triangulator = StereoTriangulator(calibration_path)

    # Print calibration quality
    quality = triangulator.get_calibration_quality()
    print(f"\nCalibration Quality:")
    print(f"  RMS error: {quality['rms_error']:.4f} pixels")
    print(f"  Baseline: {quality['baseline_cm']:.2f} cm")
    print(f"  Image size: {quality['image_size']}")

    # Create synthetic 2D points for testing
    print("\nTesting with synthetic points...")

    # Simulate nose tip detected at different locations in each camera
    landmarks_cam1 = np.array([[960, 540]], dtype=np.float32)  # Image center
    landmarks_cam2 = np.array([[1100, 550]], dtype=np.float32)  # Slightly offset

    print(f"  Camera 1 point: {landmarks_cam1[0]}")
    print(f"  Camera 2 point: {landmarks_cam2[0]}")

    # Triangulate
    points_3d = triangulator.triangulate(landmarks_cam1, landmarks_cam2)

    print(f"\n✓ 3D point: ({points_3d[0][0]:.4f}, {points_3d[0][1]:.4f}, {points_3d[0][2]:.4f}) meters")
    print(f"  Distance from cameras: {points_3d[0][2]:.2f} m")

    # Reproject back
    repr_cam1, repr_cam2 = triangulator.reproject_landmarks(points_3d)

    print(f"\nReprojected points:")
    print(f"  Camera 1: {repr_cam1[0]} (original: {landmarks_cam1[0]})")
    print(f"  Camera 2: {repr_cam2[0]} (original: {landmarks_cam2[0]})")

    # Calculate reprojection error
    error_cam1 = np.linalg.norm(repr_cam1[0] - landmarks_cam1[0])
    error_cam2 = np.linalg.norm(repr_cam2[0] - landmarks_cam2[0])
    mean_error = (error_cam1 + error_cam2) / 2

    print(f"\nReprojection errors:")
    print(f"  Camera 1: {error_cam1:.3f} pixels")
    print(f"  Camera 2: {error_cam2:.3f} pixels")
    print(f"  Mean: {mean_error:.3f} pixels")

    if mean_error < 5:
        print(f"\n✓ Test PASSED - Low reprojection error (< 5px)")
    else:
        print(f"\n⚠ Test WARNING - High reprojection error (> 5px)")

    print("="*60)


if __name__ == "__main__":
    """
    Test triangulation module.
    Usage: python triangulator.py [calibration_path]
    """
    import sys

    calibration_path = sys.argv[1] if len(sys.argv) > 1 else config.CALIBRATION_DATA_PATH

    try:
        test_triangulation(calibration_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nRun stereo calibration first:")
        print("  cd Calibration")
        print("  python stereo_calibrate.py --cam1 video1.mp4 --cam2 video2.mp4")
        sys.exit(1)
