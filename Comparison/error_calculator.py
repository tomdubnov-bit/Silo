"""
Reprojection Error Calculation Module
Compares observed vs reprojected landmarks to detect geometric inconsistencies.
"""

import numpy as np
import cv2
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
import config


class ReprojectionErrorCalculator:
    """
    Calculates reprojection errors between observed and reprojected landmarks.
    """

    def __init__(self):
        """Initialize error calculator."""
        self.real_threshold = config.REAL_HUMAN_THRESHOLD
        self.deepfake_threshold = config.DEEPFAKE_THRESHOLD

    def calculate_per_landmark_error(self, observed, reprojected):
        """
        Calculate Euclidean distance error for each landmark.

        Args:
            observed (np.ndarray): Nx2 array of observed 2D points
            reprojected (np.ndarray): Nx2 array of reprojected 2D points

        Returns:
            np.ndarray: N-length array of per-landmark errors (in pixels)

        Raises:
            ValueError: If arrays have different shapes
        """
        if observed.shape != reprojected.shape:
            raise ValueError(
                f"Shape mismatch: observed={observed.shape}, reprojected={reprojected.shape}"
            )

        # Calculate Euclidean distance for each point
        errors = np.linalg.norm(observed - reprojected, axis=1)

        return errors

    def calculate_mean_error(self, observed_cam1, reprojected_cam1,
                            observed_cam2, reprojected_cam2):
        """
        Calculate mean reprojection error across both camera views.

        Args:
            observed_cam1 (np.ndarray): Nx2 observed points from camera 1
            reprojected_cam1 (np.ndarray): Nx2 reprojected points for camera 1
            observed_cam2 (np.ndarray): Nx2 observed points from camera 2
            reprojected_cam2 (np.ndarray): Nx2 reprojected points for camera 2

        Returns:
            dict: Error statistics including mean, std, min, max per camera and overall
        """
        # Calculate per-landmark errors for each camera
        errors_cam1 = self.calculate_per_landmark_error(observed_cam1, reprojected_cam1)
        errors_cam2 = self.calculate_per_landmark_error(observed_cam2, reprojected_cam2)

        # Combine all errors
        all_errors = np.concatenate([errors_cam1, errors_cam2])

        # Calculate statistics
        stats = {
            'mean_error': float(np.mean(all_errors)),
            'std_error': float(np.std(all_errors)),
            'min_error': float(np.min(all_errors)),
            'max_error': float(np.max(all_errors)),
            'cam1_mean': float(np.mean(errors_cam1)),
            'cam2_mean': float(np.mean(errors_cam2)),
            'errors_cam1': errors_cam1,
            'errors_cam2': errors_cam2,
            'n_landmarks': len(errors_cam1)
        }

        return stats

    def classify_authenticity(self, mean_error):
        """
        Classify subject as real human or deepfake based on error.

        Args:
            mean_error (float): Mean reprojection error in pixels

        Returns:
            dict: Classification result with is_deepfake flag and reasoning
        """
        if mean_error < self.real_threshold:
            classification = {
                'is_deepfake': False,
                'confidence': 'high',
                'reasoning': f'Low error ({mean_error:.2f}px < {self.real_threshold}px threshold)'
            }
        elif mean_error > self.deepfake_threshold:
            classification = {
                'is_deepfake': True,
                'confidence': 'high',
                'reasoning': f'High error ({mean_error:.2f}px > {self.deepfake_threshold}px threshold)'
            }
        else:
            # In between thresholds - uncertain
            classification = {
                'is_deepfake': mean_error > (self.real_threshold + self.deepfake_threshold) / 2,
                'confidence': 'low',
                'reasoning': f'Moderate error ({mean_error:.2f}px between thresholds)'
            }

        return classification

    def generate_report(self, error_stats, include_per_landmark=False):
        """
        Generate human-readable error report.

        Args:
            error_stats (dict): Error statistics from calculate_mean_error()
            include_per_landmark (bool): Include detailed per-landmark errors

        Returns:
            str: Formatted report
        """
        mean_error = error_stats['mean_error']
        classification = self.classify_authenticity(mean_error)

        report = []
        report.append("="*60)
        report.append("REPROJECTION ERROR ANALYSIS")
        report.append("="*60)

        report.append(f"\nOverall Statistics:")
        report.append(f"  Mean error: {error_stats['mean_error']:.3f} pixels")
        report.append(f"  Std deviation: {error_stats['std_error']:.3f} pixels")
        report.append(f"  Min error: {error_stats['min_error']:.3f} pixels")
        report.append(f"  Max error: {error_stats['max_error']:.3f} pixels")
        report.append(f"  Landmarks analyzed: {error_stats['n_landmarks']}")

        report.append(f"\nPer-Camera Statistics:")
        report.append(f"  Camera 1 mean: {error_stats['cam1_mean']:.3f} pixels")
        report.append(f"  Camera 2 mean: {error_stats['cam2_mean']:.3f} pixels")

        report.append(f"\nClassification:")
        report.append(f"  Is deepfake: {classification['is_deepfake']}")
        report.append(f"  Confidence: {classification['confidence']}")
        report.append(f"  Reasoning: {classification['reasoning']}")

        report.append(f"\nThresholds:")
        report.append(f"  Real human: < {self.real_threshold} pixels")
        report.append(f"  Deepfake: > {self.deepfake_threshold} pixels")

        if include_per_landmark:
            report.append(f"\nPer-Landmark Errors (Camera 1):")
            for i, err in enumerate(error_stats['errors_cam1']):
                report.append(f"  Landmark {i}: {err:.3f} px")

            report.append(f"\nPer-Landmark Errors (Camera 2):")
            for i, err in enumerate(error_stats['errors_cam2']):
                report.append(f"  Landmark {i}: {err:.3f} px")

        report.append("="*60)

        return "\n".join(report)

    def visualize_errors(self, frame, observed, reprojected, errors, max_error_display=20):
        """
        Visualize reprojection errors on frame.

        Args:
            frame (np.ndarray): Input frame (BGR)
            observed (np.ndarray): Nx2 observed landmarks
            reprojected (np.ndarray): Nx2 reprojected landmarks
            errors (np.ndarray): N-length error values
            max_error_display (float): Maximum error for color scaling

        Returns:
            np.ndarray: Frame with error visualization
        """
        vis_frame = frame.copy()

        for i, (obs, rep, err) in enumerate(zip(observed, reprojected, errors)):
            # Color code by error (green = low, red = high)
            error_ratio = min(err / max_error_display, 1.0)
            color = (
                0,
                int(255 * (1 - error_ratio)),  # Green decreases with error
                int(255 * error_ratio)          # Red increases with error
            )

            # Draw observed point
            cv2.circle(vis_frame, (int(obs[0]), int(obs[1])), 5, (0, 255, 0), -1)

            # Draw reprojected point
            cv2.circle(vis_frame, (int(rep[0]), int(rep[1])), 5, (0, 0, 255), -1)

            # Draw line connecting them
            cv2.line(vis_frame,
                    (int(obs[0]), int(obs[1])),
                    (int(rep[0]), int(rep[1])),
                    color, 2)

            # Draw error value
            mid_x = int((obs[0] + rep[0]) / 2)
            mid_y = int((obs[1] + rep[1]) / 2)
            cv2.putText(vis_frame, f"{err:.1f}px",
                       (mid_x + 5, mid_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.4, color, 1)

        # Add legend
        cv2.putText(vis_frame, "Green = Observed", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(vis_frame, "Red = Reprojected", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return vis_frame

    def identify_outlier_landmarks(self, errors, threshold_std=2.0):
        """
        Identify landmarks with unusually high errors (potential outliers).

        Args:
            errors (np.ndarray): Array of per-landmark errors
            threshold_std (float): Number of standard deviations for outlier detection

        Returns:
            np.ndarray: Indices of outlier landmarks
        """
        mean = np.mean(errors)
        std = np.std(errors)
        threshold = mean + (threshold_std * std)

        outlier_indices = np.where(errors > threshold)[0]

        return outlier_indices


def test_error_calculator():
    """
    Test error calculator with synthetic data.
    """
    print("Testing Reprojection Error Calculator")
    print("="*60)

    calculator = ReprojectionErrorCalculator()

    # Create synthetic data
    # Case 1: Real human (low error)
    print("\nTest 1: Real Human (Low Error)")
    observed_cam1 = np.array([[100, 100], [200, 200], [300, 300]], dtype=np.float32)
    reprojected_cam1 = observed_cam1 + np.random.normal(0, 2, observed_cam1.shape)  # ~2px noise

    observed_cam2 = np.array([[150, 100], [250, 200], [350, 300]], dtype=np.float32)
    reprojected_cam2 = observed_cam2 + np.random.normal(0, 2, observed_cam2.shape)

    stats = calculator.calculate_mean_error(observed_cam1, reprojected_cam1,
                                            observed_cam2, reprojected_cam2)

    print(calculator.generate_report(stats))

    # Case 2: Deepfake (high error)
    print("\n\nTest 2: Deepfake (High Error)")
    reprojected_cam1 = observed_cam1 + np.random.normal(0, 20, observed_cam1.shape)  # ~20px noise
    reprojected_cam2 = observed_cam2 + np.random.normal(0, 20, observed_cam2.shape)

    stats = calculator.calculate_mean_error(observed_cam1, reprojected_cam1,
                                            observed_cam2, reprojected_cam2)

    print(calculator.generate_report(stats))


if __name__ == "__main__":
    test_error_calculator()
