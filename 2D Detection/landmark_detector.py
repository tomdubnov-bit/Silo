"""
2D Facial Landmark Detection Module
Uses MediaPipe Face Mesh to detect facial landmarks in frame pairs.
"""

import cv2
import numpy as np
import mediapipe as mp
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
import config


class FaceLandmarkDetector:
    """
    Detects facial landmarks using MediaPipe Face Mesh.
    """

    def __init__(self, landmark_indices=None):
        """
        Initialize the landmark detector.

        Args:
            landmark_indices (list): List of landmark indices to extract (None = use config)
        """
        self.landmark_indices = landmark_indices or config.get_landmark_indices()

        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,  # Treat each frame independently (critical for stereo views)
            max_num_faces=config.MEDIAPIPE_CONFIG['max_num_faces'],
            refine_landmarks=config.MEDIAPIPE_CONFIG['refine_landmarks'],
            min_detection_confidence=config.MEDIAPIPE_CONFIG['min_detection_confidence'],
            min_tracking_confidence=config.MEDIAPIPE_CONFIG['min_tracking_confidence']
        )

        # For visualization
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def detect_landmarks(self, frame):
        """
        Detect facial landmarks in a single frame.

        Args:
            frame (np.ndarray): Input image in BGR format

        Returns:
            np.ndarray: Nx2 array of (x, y) pixel coordinates for selected landmarks,
                       or None if no face detected

        Raises:
            ValueError: If frame is invalid
        """
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame provided")

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process frame
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return None  # No face detected

        # Get first face (max_num_faces=1 in config)
        face_landmarks = results.multi_face_landmarks[0]

        # Extract selected landmarks
        height, width = frame.shape[:2]
        landmarks_2d = []

        for idx in self.landmark_indices:
            if idx >= len(face_landmarks.landmark):
                raise ValueError(f"Landmark index {idx} out of range (max: {len(face_landmarks.landmark)-1})")

            landmark = face_landmarks.landmark[idx]

            # Convert normalized coordinates to pixel coordinates
            x_px = landmark.x * width
            y_px = landmark.y * height

            landmarks_2d.append([x_px, y_px])

        return np.array(landmarks_2d, dtype=np.float32)

    def detect_landmarks_pair(self, frame_front, frame_side):
        """
        Detect landmarks in both front and side view frames.

        Args:
            frame_front (np.ndarray): Front view frame (BGR)
            frame_side (np.ndarray): Side view frame (BGR)

        Returns:
            tuple: (landmarks_front, landmarks_side) as Nx2 arrays,
                   or (None, None) if face not detected in either view

        Note:
            If face is detected in only one view, both will be None.
            For stereo processing, need landmarks in BOTH views.
        """
        landmarks_front = self.detect_landmarks(frame_front)
        landmarks_side = self.detect_landmarks(frame_side)

        # Check if face detected in both views
        if landmarks_front is None:
            print("⚠ Warning: No face detected in front view")
            return None, None

        if landmarks_side is None:
            print("⚠ Warning: No face detected in side view")
            return None, None

        # Verify same number of landmarks
        if len(landmarks_front) != len(landmarks_side):
            raise ValueError(
                f"Landmark count mismatch: front={len(landmarks_front)}, side={len(landmarks_side)}"
            )

        print(f"✓ Detected {len(landmarks_front)} landmarks in both views")

        return landmarks_front, landmarks_side

    def visualize_landmarks(self, frame, landmarks, color=(0, 255, 0), radius=3):
        """
        Draw landmarks on frame for visualization.

        Args:
            frame (np.ndarray): Input frame (BGR)
            landmarks (np.ndarray): Nx2 array of (x, y) coordinates
            color (tuple): BGR color for markers
            radius (int): Marker radius in pixels

        Returns:
            np.ndarray: Frame with landmarks drawn
        """
        if landmarks is None:
            return frame.copy()

        vis_frame = frame.copy()

        for x, y in landmarks:
            cv2.circle(vis_frame, (int(x), int(y)), radius, color, -1)

        return vis_frame

    def visualize_landmarks_with_labels(self, frame, landmarks, landmark_indices=None):
        """
        Draw landmarks with index labels for debugging.

        Args:
            frame (np.ndarray): Input frame (BGR)
            landmarks (np.ndarray): Nx2 array of (x, y) coordinates
            landmark_indices (list): Corresponding landmark indices (None = use self.landmark_indices)

        Returns:
            np.ndarray: Frame with labeled landmarks
        """
        if landmarks is None:
            return frame.copy()

        vis_frame = frame.copy()
        indices = landmark_indices or self.landmark_indices

        for i, (x, y) in enumerate(landmarks):
            # Draw circle
            cv2.circle(vis_frame, (int(x), int(y)), 3, (0, 255, 0), -1)

            # Draw label
            label = str(indices[i])
            cv2.putText(
                vis_frame, label,
                (int(x) + 5, int(y) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3, (255, 255, 255), 1
            )

        return vis_frame

    def get_landmark_names(self):
        """
        Get descriptive names for key landmarks.

        Returns:
            dict: Mapping of landmark index to descriptive name
        """
        # MediaPipe Face Mesh landmark names (current set: 6 rigid landmarks)
        landmark_names = {
            1: "Nose tip",
            4: "Nose bridge top",
            199: "Nose bridge mid",
            152: "Chin",
            234: "Left forehead",
            454: "Right forehead",
        }

        return {idx: landmark_names.get(idx, f"Landmark {idx}")
                for idx in self.landmark_indices}

    def close(self):
        """
        Release MediaPipe resources.
        """
        self.face_mesh.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def detect_and_visualize(frame_path, output_path=None, show_labels=False):
    """
    Utility function to detect and visualize landmarks on a single image.

    Args:
        frame_path (str): Path to input image
        output_path (str): Path to save visualization (None = display only)
        show_labels (bool): Show landmark indices

    Returns:
        np.ndarray: Detected landmarks
    """
    frame = cv2.imread(frame_path)
    if frame is None:
        raise FileNotFoundError(f"Could not load image: {frame_path}")

    with FaceLandmarkDetector() as detector:
        landmarks = detector.detect_landmarks(frame)

        if landmarks is None:
            print("No face detected in image")
            return None

        # Visualize
        if show_labels:
            vis_frame = detector.visualize_landmarks_with_labels(frame, landmarks)
        else:
            vis_frame = detector.visualize_landmarks(frame, landmarks)

        # Save or display
        if output_path:
            cv2.imwrite(output_path, vis_frame)
            print(f"✓ Visualization saved to {output_path}")
        else:
            cv2.imshow("Landmarks", vis_frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        # Print landmark info
        print(f"\nDetected {len(landmarks)} landmarks:")
        names = detector.get_landmark_names()
        for idx, (x, y) in zip(detector.landmark_indices, landmarks):
            print(f"  {names[idx]}: ({x:.1f}, {y:.1f})")

        return landmarks


if __name__ == "__main__":
    """
    Test landmark detection on a single image.
    Usage: python landmark_detector.py <image_path> [output_path]
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python landmark_detector.py <image_path> [output_path]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    detect_and_visualize(image_path, output_path, show_labels=True)
