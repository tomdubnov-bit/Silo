Silo-Sight Multi-View Deepfake Integrity Check


Motivation
In 2024, the multinational firm Arup suffered a staggering loss of approximately $25 million due to a sophisticated deepfake attack. An employee, initially suspicious of an email request, was convinced to authorize the transfers after attending a fake video conference. During the call, all participants, including the Chief Financial Officer and senior colleagues, were AI-generated deepfakes with convincingly cloned visuals. This is not an isolated case. As deepfake sophistication and access accelerates, businesses suffer financial, operational and reputation damage. Companies currently face a difficult trade-off:
1. Risk Fraud: Rely on current, lax digital protocols where web conferences are easily faked.
2. Slow Operations: Insist on in-person approvals for high stakes meetings, severely impeding operational speed.
Arup's loss proves that relying on visual recognition in 2D web conferencing environments is no longer safe.


Solution: Silo-Sight
Silo-Sight tackles this threat by leveraging a core weakness of deepfake technology: its struggle with geometric and 3D consistency across multiple simultaneous viewing angles. Silo-Sight acts as a zero-trust check for a person entering a virtual conference room. The system uses two webcams to verify the physical location of rigid facial features. The principle is simple: Facial extremities viewed from two fixed cameras must always triangulate to a single, consistent 3D point in space. A deepfake, generated in 2D, will show measurable geometric inconsistencies when attempting to reconcile the two views.


Implementation: Proof of Concept Pipeline
1. Orient: Mathematically establish the fixed relationship between the two cameras using stereo calibration (OpenCV stereo calibration functions).
2. 2D Detection: Use facial landmark detection (MediaPipe) to find the 2D pixel coordinates of rigid facial features in both camera views.
3. 3D Triangulation: Given the 2D coordinates from both views and the calibrated camera relationship, compute the 3D position of each landmark in real-world space.
4. 2D Reprojection: Project the computed 3D points back onto both camera image planes to get expected 2D coordinates.
5. Comparison: Calculate reprojection error - the difference between observed 2D landmarks and expected 2D positions.
6. Scoring: Aggregate error across all landmarks and output a confidence score from 0-100 representing how likely the user is a real human, not a deepfake.

Real humans produce low reprojection errors (below 5 pixels). Deepfakes displayed on screens produce high errors (above 15 pixels) because they lack true 3D geometry.


Getting Started

Requirements:
- Python 3.10 or higher
- Two webcams (ideally two separate computers joining the same Zoom call for proper stereo setup)
- Printed checkerboard pattern (8 rows x 11 columns, 5/8 inch squares)

Installation:
1. Clone repository
2. Create virtual environment: python3 -m venv venv
3. Activate: source venv/bin/activate (macOS/Linux) or venv\Scripts\activate (Windows)
4. Install dependencies: pip install -r requirements.txt

See SETUP.md for detailed installation instructions.


Usage

1. Calibration (One-Time Setup)

Record calibration video with both cameras visible (join Zoom from two separate devices for best results). Start recording. Hold checkerboard and move it around for 20-30 seconds at different distances, angles, and positions. Stop recording.

Split the video:
python3 Ingestion/split_zoom_video.py path/to/zoom_calibration.mp4 --output-prefix cam_calibration

Run calibration:
python3 Calibration/stereo_calibrate.py --cam1 cam_calibration1.mp4 --cam2 cam_calibration2.mp4 --frame_interval 30

This generates stereo_calibration.npz. Do NOT move the cameras after calibration.

2. Deepfake Detection

From Zoom screenshot:
python3 detect_deepfake.py --screenshot zoom_screenshot.png

From separate images:
python3 detect_deepfake.py --front front_view.png --side side_view.png

Save results:
python3 detect_deepfake.py --screenshot test.png --output-json result.json --output-csv results.csv

See USAGE.md for comprehensive usage guide.


Landmark Selection

The system uses 6 rigid, expression-invariant facial landmarks:
- Nose tip (index 1): Central, prominent, bone structure
- Nose bridge top (index 4): Rigid, expression-invariant
- Nose bridge mid (index 199): Additional nose stability point
- Chin (index 152): Prominent, rigid when mouth closed
- Left forehead (index 234): Pure bone structure
- Right forehead (index 454): Bilateral coverage, rigid

These points are bone structure that don't move during smiling, talking, or other expressions. This prevents false positives when real humans show facial expressions. Eye corners, mouth corners, and ears are excluded because they shift with expressions or have occlusion issues at the 30 degree camera angle.


Why Multi-View Deepfakes Are Difficult

While an attacker could theoretically create two separate deepfakes (one for each camera), this faces severe technical barriers:

Single Deepfake (Current Threat - Detected)
One 2D deepfake video displayed on screen. Both cameras capture the same flat screen from different angles. Result: Geometric inconsistency - 2D surface cannot triangulate to consistent 3D coordinates. High reprojection error flags as deepfake.

Two Independent Deepfakes (Still Detected)
Attacker creates separate deepfakes for each camera without 3D coordination. Facial features appear at inconsistent spatial positions. Even worse geometric inconsistency than single deepfake. Very high reprojection error flags as deepfake.

Two Coordinated 3D-Consistent Deepfakes (Theoretical Bypass - Extremely Complex)
For this to succeed, attacker must: create accurate 3D model of target's face, perform real-time 3D head pose tracking, render target face from two viewing angles simultaneously, maintain perfect geometric correspondence, inject both streams into video conference in real-time, and ensure rendering quality matches real video.

Comparison:
2D Deepfake (Current Threat): Free consumer apps, minimal expertise, under $100, 5-30 minutes, consumer hardware, widely available
3D-Consistent Multi-View (Theoretical): Custom 3D pipeline, computer graphics expertise, thousands in development cost, weeks to months, high-end GPU cluster, not in attacker toolkits

Silo-Sight raises the attack cost from "free consumer app" to "sophisticated 3D graphics engineering project." Even if 3D-consistent deepfakes become feasible, additional detection layers remain: rendering artifacts, temporal coherence issues, micro-expression failures, audio-visual synchronization, depth sensing, behavioral biometrics.


Technical Stack
1. Language: Python
    Access to robust computer vision libraries
2. Video Processing: OpenCV
    Camera stream acquisition, synchronization, and the full suite of Stereo Calibration functions (cv.calibrateCamera, cv.stereoCalibrate, cv.triangulatePoints, cv.projectPoints).
3. Feature Tracking: MediaPipe
    Fast and accurate facial extremity detection (468 landmark points)
4. Data/Math: NumPy, scipy
    High-performance numerical operations for matrix manipulation and error calculation.


Project Structure

Silo-Sight/
- detect_deepfake.py: Main detection pipeline
- config.py: System configuration
- stereo_calibration.npz: Calibration data (generated)
- Calibration/: Stereo camera calibration scripts
- Ingestion/: Image/video loading and preprocessing
- 2D Detection/: MediaPipe facial landmark detection
- 3D Triangulation/: Stereo triangulation to 3D points
- 2D Reprojection/: Project 3D points back to 2D
- Comparison/: Calculate reprojection error
- Output/: Generate confidence scores


Long-Term Vision
This POC is the foundation for a more powerful, general-purpose integrity engine. The long term vision includes the following features:
1. Live video ingestion and analysis
2. 3D Modeling
    Progress from a simple geometric consistency check to full 3D head model reconstruction in real-time. By accurately triangulating several facial landmarks (nose tip, chin, ear tips, forehead), Silo Safe creates a truth anchor. The system could then generate a low-fidelity 3D model of the user's head in real-time and continuously project that 3D model back onto the two camera feeds. Assert truth by checking if the live video and audio align perfectly with the derived 3D geometry: a task exponentially harder for deepfake generative models.
3. Real-time confidence score adjustment
4. Comprehensive integrity infrastructure for high stakes workflows, including:
    a. Pre-meeting vetting and facial mapping
    b. In-Meeting Deepfake Defense (Secure Room)
    c. Escalation and Alert Protocol
    d. Post-Event Accountability and Audit
