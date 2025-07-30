"""
Calibration Validation Utility
Verifies the quality of stereo calibration and visualizes results.

Usage:
    python validate_calibration.py --calibration stereo_calibration.npz
"""

import cv2
import numpy as np
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))
import config
from stereo_calibrate import StereoCalibrator


def validate_calibration(calibration_data):
    """
    Validate calibration quality and print diagnostics.

    Args:
        calibration_data (dict): Loaded calibration parameters

    Returns:
        bool: True if calibration passes validation checks
    """
    print("\n" + "="*60)
    print("CALIBRATION VALIDATION")
    print("="*60)

    validation_passed = True

    # Check 1: RMS Error
    print(f"\n1. RMS Reprojection Error:")
    print(f"   Value: {calibration_data['rms_error']:.4f} pixels")
    print(f"   Threshold: {config.MAX_CALIBRATION_ERROR} pixels")

    if calibration_data['rms_error'] < config.MAX_CALIBRATION_ERROR:
        print(f"   ✓ PASS")
    else:
        print(f"   ✗ FAIL - Error too high")
        validation_passed = False

    # Check 2: Camera matrices are valid
    print(f"\n2. Camera Intrinsics:")
    K1 = calibration_data['K1']
    K2 = calibration_data['K2']

    print(f"   Camera 1 focal lengths: fx={K1[0,0]:.2f}, fy={K1[1,1]:.2f}")
    print(f"   Camera 1 principal point: cx={K1[0,2]:.2f}, cy={K1[1,2]:.2f}")
    print(f"   Camera 2 focal lengths: fx={K2[0,0]:.2f}, fy={K2[1,1]:.2f}")
    print(f"   Camera 2 principal point: cx={K2[0,2]:.2f}, cy={K2[1,2]:.2f}")

    # Focal lengths should be reasonable (not zero or negative)
    if K1[0,0] > 0 and K1[1,1] > 0 and K2[0,0] > 0 and K2[1,1] > 0:
        print(f"   ✓ PASS")
    else:
        print(f"   ✗ FAIL - Invalid focal lengths")
        validation_passed = False

    # Check 3: Rotation matrix properties
    print(f"\n3. Rotation Matrix:")
    R = calibration_data['R']

    # R should be orthogonal (R^T * R = I)
    identity_check = R.T @ R
    orthogonality_error = np.linalg.norm(identity_check - np.eye(3))
    print(f"   Orthogonality error: {orthogonality_error:.6f}")

    # Determinant should be +1 (proper rotation)
    det = np.linalg.det(R)
    print(f"   Determinant: {det:.6f} (should be ~1.0)")

    if orthogonality_error < 0.01 and abs(det - 1.0) < 0.01:
        print(f"   ✓ PASS")
    else:
        print(f"   ✗ FAIL - Invalid rotation matrix")
        validation_passed = False

    # Check 4: Translation vector (baseline)
    print(f"\n4. Camera Baseline:")
    T = calibration_data['T']
    baseline = np.linalg.norm(T)
    print(f"   Translation: {T.ravel()}")
    print(f"   Baseline distance: {baseline:.4f} meters ({baseline*100:.2f} cm)")

    # Baseline should be reasonable (e.g., 10cm to 1m for desktop setup)
    if 0.05 < baseline < 2.0:
        print(f"   ✓ PASS")
    else:
        print(f"   ⚠ WARNING - Baseline seems unusual (expected 5cm - 2m)")
        # Don't fail, just warn

    # Check 5: Distortion coefficients
    print(f"\n5. Distortion Coefficients:")
    dist1 = calibration_data['dist1'].ravel()
    dist2 = calibration_data['dist2'].ravel()
    print(f"   Camera 1: {dist1}")
    print(f"   Camera 2: {dist2}")

    # High distortion coefficients might indicate poor calibration or fish-eye lens
    max_dist1 = np.max(np.abs(dist1))
    max_dist2 = np.max(np.abs(dist2))

    if max_dist1 < 2.0 and max_dist2 < 2.0:
        print(f"   ✓ PASS")
    else:
        print(f"   ⚠ WARNING - High distortion coefficients detected")

    # Check 6: Projection matrices
    print(f"\n6. Projection Matrices:")
    P1 = calibration_data['P1']
    P2 = calibration_data['P2']
    print(f"   P1 shape: {P1.shape}")
    print(f"   P2 shape: {P2.shape}")

    if P1.shape == (3, 4) and P2.shape == (3, 4):
        print(f"   ✓ PASS")
    else:
        print(f"   ✗ FAIL - Invalid projection matrix dimensions")
        validation_passed = False

    # Overall result
    print("\n" + "="*60)
    if validation_passed:
        print("✓ CALIBRATION VALIDATION PASSED")
        print("="*60)
        print("\nCalibration quality is good. You can proceed with detection.")
    else:
        print("✗ CALIBRATION VALIDATION FAILED")
        print("="*60)
        print("\nCalibration quality is poor. Consider recalibrating with:")
        print("  - More checkerboard images (20-30 recommended)")
        print("  - Better variety of angles and positions")
        print("  - Ensure checkerboard is flat and well-lit")
        print("  - Check that cameras are stable during capture")

    return validation_passed


def visualize_epipolar_geometry(calibration_data, img1_path, img2_path, output_dir="2. Calibration/output"):
    """
    Visualize epipolar geometry to verify stereo calibration.
    Draws epipolar lines for clicked points.

    Args:
        calibration_data (dict): Calibration parameters
        img1_path (str): Path to test image from camera 1
        img2_path (str): Path to test image from camera 2
        output_dir (str): Directory to save visualization
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        print("Error: Could not load test images")
        return

    F = calibration_data['F']

    # Function to draw epilines
    def draw_epilines(img1, img2, lines, pts1, pts2):
        """Draw epipolar lines on images."""
        r, c = img1.shape[:2]
        img1_color = img1.copy()
        img2_color = img2.copy()

        for r_line, pt1, pt2 in zip(lines, pts1, pts2):
            color = tuple(np.random.randint(0, 255, 3).tolist())

            # Draw epipolar line on img2
            x0, y0 = map(int, [0, -r_line[2]/r_line[1]])
            x1, y1 = map(int, [c, -(r_line[2]+r_line[0]*c)/r_line[1]])
            img2_color = cv2.line(img2_color, (x0,y0), (x1,y1), color, 1)

            # Draw point on img1
            img1_color = cv2.circle(img1_color, tuple(pt1.astype(int)), 5, color, -1)

            # Draw point on img2
            img2_color = cv2.circle(img2_color, tuple(pt2.astype(int)), 5, color, -1)

        return img1_color, img2_color

    # Use corners detection as sample points
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Detect some corner points
    pts1 = cv2.goodFeaturesToTrack(gray1, maxCorners=20, qualityLevel=0.01, minDistance=30)
    pts2 = cv2.goodFeaturesToTrack(gray2, maxCorners=20, qualityLevel=0.01, minDistance=30)

    if pts1 is not None and len(pts1) >= 5:
        pts1 = pts1[:5].reshape(-1, 2)
        pts2 = pts2[:5].reshape(-1, 2) if pts2 is not None and len(pts2) >= 5 else pts1

        # Compute epilines for points in img1
        lines2 = cv2.computeCorrespondEpilines(pts1.reshape(-1, 1, 2), 1, F)
        lines2 = lines2.reshape(-1, 3)

        # Compute epilines for points in img2
        lines1 = cv2.computeCorrespondEpilines(pts2.reshape(-1, 1, 2), 2, F)
        lines1 = lines1.reshape(-1, 3)

        # Draw epilines
        img1_epilines, img2_epilines = draw_epilines(img1, img2, lines2, pts1, pts2)

        # Save visualization
        combined = np.hstack([img1_epilines, img2_epilines])
        output_path = os.path.join(output_dir, "epipolar_lines.png")
        cv2.imwrite(output_path, combined)
        print(f"\n✓ Epipolar geometry visualization saved to: {output_path}")
        print("  Points in left image should lie on corresponding epipolar lines in right image")
    else:
        print("\n⚠ Could not detect enough feature points for epipolar visualization")


def print_calibration_summary(calibration_data):
    """
    Print a human-readable summary of calibration data.

    Args:
        calibration_data (dict): Calibration parameters
    """
    print("\n" + "="*60)
    print("CALIBRATION SUMMARY")
    print("="*60)

    T = calibration_data['T']
    R = calibration_data['R']

    # Calculate rotation angle
    angle = np.arccos((np.trace(R) - 1) / 2) * 180 / np.pi

    # Calculate rotation axis (Rodrigues)
    rvec, _ = cv2.Rodrigues(R)
    axis = rvec.ravel() / np.linalg.norm(rvec)

    print(f"\nCamera Separation:")
    print(f"  Baseline: {np.linalg.norm(T)*100:.2f} cm")
    print(f"  Translation: X={T[0,0]*100:.2f}cm, Y={T[1,0]*100:.2f}cm, Z={T[2,0]*100:.2f}cm")

    print(f"\nRelative Rotation:")
    print(f"  Angle: {angle:.2f} degrees")
    print(f"  Axis: [{axis[0]:.3f}, {axis[1]:.3f}, {axis[2]:.3f}]")

    print(f"\nImage Size: {calibration_data['image_size']}")
    print(f"Calibration Quality: {calibration_data['rms_error']:.4f} pixels RMS error")

    print("="*60)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Validate Stereo Calibration")
    parser.add_argument('--calibration', type=str, default=config.CALIBRATION_DATA_PATH,
                       help='Path to calibration file')
    parser.add_argument('--img1', type=str, help='Test image from camera 1 (for epipolar visualization)')
    parser.add_argument('--img2', type=str, help='Test image from camera 2 (for epipolar visualization)')
    parser.add_argument('--output', type=str, default='2. Calibration/output',
                       help='Output directory for visualizations')

    args = parser.parse_args()

    try:
        # Load calibration
        print(f"Loading calibration from: {args.calibration}")
        calibration_data = StereoCalibrator.load_calibration(args.calibration)

        # Print summary
        print_calibration_summary(calibration_data)

        # Validate
        passed = validate_calibration(calibration_data)

        # Visualize epipolar geometry if test images provided
        if args.img1 and args.img2:
            visualize_epipolar_geometry(calibration_data, args.img1, args.img2, args.output)

        sys.exit(0 if passed else 1)

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nRun stereo_calibrate.py first to generate calibration data.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
