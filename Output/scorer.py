"""
Scoring and Output Module
Converts reprojection errors to confidence scores and formats results.
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
import config


class DeepfakeScorer:
    """
    Converts error metrics to confidence scores and determines authenticity.
    """

    def __init__(self):
        """Initialize scorer with config thresholds."""
        self.real_threshold = config.REAL_HUMAN_THRESHOLD
        self.deepfake_threshold = config.DEEPFAKE_THRESHOLD
        self.confidence_cutoff = config.HUMAN_CONFIDENCE_CUTOFF

    def calculate_confidence_score(self, mean_error):
        """
        Convert mean reprojection error to confidence score (0-100).

        Args:
            mean_error (float): Mean reprojection error in pixels

        Returns:
            float: Confidence score (0-100), where higher = more likely real human
        """
        return config.calculate_confidence_score(mean_error)

    def determine_authenticity(self, confidence_score):
        """
        Determine if subject is deepfake based on confidence score.

        Args:
            confidence_score (float): Confidence score (0-100)

        Returns:
            bool: True if deepfake, False if real human
        """
        return config.is_deepfake(confidence_score)

    def generate_detection_result(self, error_stats, frame_info=None):
        """
        Generate complete detection result.

        Args:
            error_stats (dict): Error statistics from error_calculator
            frame_info (dict): Optional metadata about the frames

        Returns:
            dict: Complete detection result
        """
        mean_error = error_stats['mean_error']
        confidence_score = self.calculate_confidence_score(mean_error)
        is_deepfake = self.determine_authenticity(confidence_score)

        result = {
            'timestamp': datetime.now().isoformat(),
            'detection': {
                'is_deepfake': bool(is_deepfake),
                'confidence_score': float(confidence_score),
                'classification': 'deepfake' if is_deepfake else 'real_human'
            },
            'metrics': {
                'mean_reprojection_error': float(mean_error),
                'std_reprojection_error': float(error_stats['std_error']),
                'min_error': float(error_stats['min_error']),
                'max_error': float(error_stats['max_error']),
                'cam1_mean_error': float(error_stats['cam1_mean']),
                'cam2_mean_error': float(error_stats['cam2_mean']),
                'landmarks_analyzed': int(error_stats['n_landmarks'])
            },
            'thresholds': {
                'real_human': float(self.real_threshold),
                'deepfake': float(self.deepfake_threshold),
                'confidence_cutoff': float(self.confidence_cutoff)
            }
        }

        if frame_info:
            result['frame_info'] = frame_info

        return result

    def format_console_output(self, result):
        """
        Format detection result for console display.

        Args:
            result (dict): Detection result from generate_detection_result()

        Returns:
            str: Formatted console output
        """
        lines = []
        lines.append("")
        lines.append("="*70)
        lines.append("SILO-SIGHT DEEPFAKE DETECTION RESULT")
        lines.append("="*70)

        # Detection result
        detection = result['detection']
        is_deepfake = detection['is_deepfake']
        confidence = detection['confidence_score']

        lines.append("")
        if is_deepfake:
            lines.append("⚠️  DEEPFAKE DETECTED")
            lines.append(f"   Confidence Score: {confidence:.1f}/100 (Low authenticity)")
        else:
            lines.append("✓  REAL HUMAN DETECTED")
            lines.append(f"   Confidence Score: {confidence:.1f}/100 (High authenticity)")

        # Metrics
        metrics = result['metrics']
        lines.append("")
        lines.append("Geometric Consistency Metrics:")
        lines.append(f"  Mean Reprojection Error: {metrics['mean_reprojection_error']:.3f} pixels")
        lines.append(f"  Error Range: {metrics['min_error']:.3f} - {metrics['max_error']:.3f} pixels")
        lines.append(f"  Standard Deviation: {metrics['std_reprojection_error']:.3f} pixels")
        lines.append(f"  Camera 1 Error: {metrics['cam1_mean_error']:.3f} pixels")
        lines.append(f"  Camera 2 Error: {metrics['cam2_mean_error']:.3f} pixels")
        lines.append(f"  Landmarks Analyzed: {metrics['landmarks_analyzed']}")

        # Thresholds
        thresholds = result['thresholds']
        lines.append("")
        lines.append("Detection Thresholds:")
        lines.append(f"  Real Human: < {thresholds['real_human']:.1f} pixels")
        lines.append(f"  Deepfake: > {thresholds['deepfake']:.1f} pixels")
        lines.append(f"  Confidence Cutoff: {thresholds['confidence_cutoff']:.0f}/100")

        # Interpretation
        lines.append("")
        lines.append("Interpretation:")
        if is_deepfake:
            lines.append("  High reprojection error indicates geometric inconsistency between")
            lines.append("  the two camera views. This suggests the subject is a 2D deepfake")
            lines.append("  that cannot maintain 3D geometric consistency.")
        else:
            lines.append("  Low reprojection error indicates geometric consistency between")
            lines.append("  the two camera views. The subject appears to be a real 3D human")
            lines.append("  face with consistent spatial properties.")

        lines.append("")
        lines.append("="*70)
        lines.append(f"Analysis completed at: {result['timestamp']}")
        lines.append("="*70)
        lines.append("")

        return "\n".join(lines)

    def save_result_json(self, result, output_path):
        """
        Save detection result to JSON file.

        Args:
            result (dict): Detection result
            output_path (str): Path to save JSON file

        Returns:
            bool: True if successful
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✓ Results saved to {output_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to save results: {e}")
            return False

    def save_result_csv(self, result, output_path, append=True):
        """
        Save detection result to CSV file (for batch processing).

        Args:
            result (dict): Detection result
            output_path (str): Path to CSV file
            append (bool): Append to existing file or create new

        Returns:
            bool: True if successful
        """
        import csv
        import os

        try:
            # Check if file exists for header
            file_exists = os.path.exists(output_path)
            mode = 'a' if (append and file_exists) else 'w'

            with open(output_path, mode, newline='') as f:
                fieldnames = [
                    'timestamp',
                    'is_deepfake',
                    'confidence_score',
                    'mean_error',
                    'std_error',
                    'cam1_error',
                    'cam2_error',
                    'landmarks_count'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # Write header if new file
                if not file_exists or not append:
                    writer.writeheader()

                # Write data
                row = {
                    'timestamp': result['timestamp'],
                    'is_deepfake': result['detection']['is_deepfake'],
                    'confidence_score': result['detection']['confidence_score'],
                    'mean_error': result['metrics']['mean_reprojection_error'],
                    'std_error': result['metrics']['std_reprojection_error'],
                    'cam1_error': result['metrics']['cam1_mean_error'],
                    'cam2_error': result['metrics']['cam2_mean_error'],
                    'landmarks_count': result['metrics']['landmarks_analyzed']
                }
                writer.writerow(row)

            print(f"✓ Results appended to {output_path}")
            return True

        except Exception as e:
            print(f"✗ Failed to save CSV: {e}")
            return False


def test_scorer():
    """
    Test scorer with sample error data.
    """
    print("Testing Deepfake Scorer")
    print("="*60)

    scorer = DeepfakeScorer()

    # Test 1: Real human (low error)
    print("\nTest 1: Real Human")
    error_stats = {
        'mean_error': 3.2,
        'std_error': 1.1,
        'min_error': 1.5,
        'max_error': 5.8,
        'cam1_mean': 3.0,
        'cam2_mean': 3.4,
        'n_landmarks': 10
    }

    result = scorer.generate_detection_result(error_stats)
    print(scorer.format_console_output(result))

    # Test 2: Deepfake (high error)
    print("\n\nTest 2: Deepfake")
    error_stats = {
        'mean_error': 18.5,
        'std_error': 4.2,
        'min_error': 12.1,
        'max_error': 27.3,
        'cam1_mean': 17.9,
        'cam2_mean': 19.1,
        'n_landmarks': 10
    }

    result = scorer.generate_detection_result(error_stats)
    print(scorer.format_console_output(result))

    # Test saving
    print("\nTesting file outputs...")
    scorer.save_result_json(result, "test_result.json")
    scorer.save_result_csv(result, "test_results.csv", append=False)


if __name__ == "__main__":
    test_scorer()
