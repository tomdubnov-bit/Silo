Validation Plan - Silo-Sight POC Testing Strategy

OVERVIEW
This validation plan tests whether Silo-Sight can distinguish between real humans and deepfakes by comparing geometric consistency across two camera angles (30° separation).

VALIDATION HYPOTHESIS
- Real humans: Will show low reprojection error (<5px) due to true 3D geometric consistency
- Deepfakes: Will show high reprojection error (>15px) due to 2D generation lacking multi-view geometric consistency

VALIDATION APPROACH
Use the "Screen Replay Method" to simulate the real-world threat scenario (Arup-style video conference attack):
1. Record yourself on webcam (real baseline)
2. Create deepfake version of same recording (face-swapped to Barack Obama)
3. Play deepfake video on screen during dual-camera capture
4. Compare geometric consistency between real human and deepfake scenarios


VALIDATION PHASES

Phase 1: Principle Validation (2D vs 3D Test)
Goal: Verify the system can detect flat 2D objects vs real 3D faces
Method:
    a. Display a photo of a face on tablet/phone screen
    b. Capture with both cameras (front + 30° side view)
    c. Run through Silo-Sight pipeline
Expected Result: High reprojection error (>20px) - fails 3D consistency check
Why: A flat 2D image cannot maintain geometric consistency across viewing angles
Status: Pre-deepfake sanity check

Phase 2: Real Human Baseline
Goal: Establish expected error range for authentic humans
Method:
    a. Sit in front of both cameras in fixed position
    b. Capture 10-15 synchronized frame pairs with slight head position variations
    c. Run through full pipeline for each pair
    d. Record mean reprojection errors
Expected Result: Low reprojection error (2-5px), confidence >90
Data to Collect:
    - Mean error per frame pair
    - Standard deviation across frames
    - Per-landmark error distribution
    - Calibration quality metrics
Purpose: Establishes the "real human" threshold and accounts for system noise

Phase 3: Deepfake Generation & Testing
Goal: Test if deepfakes fail geometric consistency check
Method: See detailed steps below

Phase 4: Comparative Analysis
Goal: Confirm statistical separation between real and fake
Method:
    a. Compare error distributions (real human vs deepfake)
    b. Validate threshold values (5px for real, 15px for fake)
    c. Calculate detection accuracy
Expected Outcome: Clear separation in reprojection error between real and fake


DEEPFAKE GENERATION METHOD

Tool: Roop (GitHub: s0md3v/roop)
Why Roop:
    - Free and open source
    - One-click face swap (minimal setup)
    - Works on single videos (perfect for screen replay)
    - Fast processing on CPU (no GPU required)
    - Active community, well-documented

Alternative Tools (if Roop doesn't work):
    1. FaceSwap (more control, steeper learning curve)
    2. DeepFaceLab (professional quality, complex setup)
    3. Reface mobile app (easiest but lower quality, watermarked)


DETAILED STEP-BY-STEP: DEEPFAKE CREATION WITH ROOP

Prerequisites:
1. Install Python 3.10
2. Install ffmpeg: brew install ffmpeg (macOS)
3. Download Roop from GitHub

Installation:
    git clone https://github.com/s0md3v/roop.git
    cd roop
    pip install -r requirements.txt

Source Material Preparation:
1. Record baseline video (for real human testing):
    a. Position yourself in front of webcam (front camera)
    b. Side camera at 30° angle
    c. Record 10-15 seconds with 5 distinct head positions:
        - Center, facing forward
        - Slight turn left
        - Slight turn right
        - Slight tilt up
        - Slight tilt down
    d. Save as: baseline_real.mp4 (front camera only for now)
    e. Ensure good lighting, clear face visibility

2. Obtain target face (Barack Obama):
    a. Download high-quality photo of Barack Obama (front-facing, clear)
    b. Save as: obama_face.jpg
    c. Requirements: clear facial features, good resolution, neutral expression

Deepfake Generation:
    python run.py --source obama_face.jpg --target baseline_real.mp4 --output deepfake_obama.mp4

    Parameters explained:
    - source: The face to swap IN (Obama)
    - target: Your original video
    - output: The deepfaked result

    Optional quality settings:
    --execution-provider cpu (or cuda if GPU available)
    --frame-processor face_swapper face_enhancer (adds enhancement)

Expected Processing Time: 2-5 minutes for 15-second video (CPU)


DUAL-CAMERA CAPTURE PROTOCOL

Real Human Capture:
1. Setup:
    - Front camera (MacBook webcam): Positioned directly in front
    - Side camera (phone/external webcam): Positioned 30° to the right
    - Ensure both cameras are fixed and won't move
    - Good, consistent lighting
2. Recording:
    - Use QuickTime or OBS to record both camera feeds simultaneously
    - OR take synchronized screenshots (manually trigger at same moment)
3. Capture 10-15 frame pairs with varied head positions
4. Save as: real_frame_pair_1.png, real_frame_pair_2.png, etc.
    - Each pair: real_front_1.png, real_side_1.png

Deepfake Capture:
1. Setup:
    - Play deepfake_obama.mp4 on your MacBook screen (fullscreen)
    - Front camera: Captures the screen showing deepfake
    - Side camera (30°): Captures the screen from side angle
2. Recording:
    - Play deepfake video
    - Capture synchronized screenshots at same 5 moments that match real human positions
3. Save as: fake_frame_pair_1.png, fake_frame_pair_2.png, etc.
    - Each pair: fake_front_1.png, fake_side_1.png

Critical Synchronization:
    - For screenshots: Use keyboard shortcut, manual trigger on both devices simultaneously
    - For video: Record both feeds, then extract frames at same timestamps post-capture
    - Timestamp metadata validation recommended


TESTING PROCEDURE

For Each Frame Pair:
1. Load frame pair (front view + side view)
2. Run through Silo-Sight pipeline:
    a. Frame ingestion & BGR conversion
    b. Landmark detection (MediaPipe)
    c. 3D triangulation
    d. Reprojection to both views
    e. Error calculation
3. Record:
    - Mean reprojection error (pixels)
    - Confidence score (0-100)
    - Per-landmark errors
    - Detection result (isDeepfake: True/False)

Data Collection:
Create results table:
    Frame Set | Type | Mean Error (px) | Confidence | Detection | Notes
    -----------------------------------------------------------------------
    Pair 1    | Real | 3.2            | 95         | Human     | Center position
    Pair 2    | Real | 4.1            | 92         | Human     | Left turn
    ...
    Pair 1    | Fake | 18.7           | 12         | Deepfake  | Screen at angle
    Pair 2    | Fake | 22.3           | 5          | Deepfake  | Side view


SUCCESS CRITERIA

1. Real Human Performance:
    - Mean reprojection error: 2-5 pixels
    - Confidence score: >85
    - Detection accuracy: >90% correctly identified as human

2. Deepfake Detection:
    - Mean reprojection error: >15 pixels
    - Confidence score: <30
    - Detection accuracy: >90% correctly identified as deepfake

3. Statistical Separation:
    - No overlap between real and fake error distributions
    - Clear threshold between categories

4. System Validation:
    - Calibration reprojection error: <1 pixel
    - Landmark detection success rate: >95%
    - Consistent results across different head positions


POTENTIAL ISSUES & MITIGATIONS

Issue: Deepfake on screen might not be detected because screen is too small
Mitigation: Fullscreen playback, zoom in on face

Issue: Side camera can't see screen properly at 30°
Mitigation: Adjust screen angle, or adjust camera to 45° if needed

Issue: MediaPipe fails on side-view landmarks
Mitigation: Use subset of landmarks visible from both angles (nose, chin, cheeks)

Issue: Real human baseline shows higher error than expected
Mitigation: Recalibrate cameras, check for camera movement, increase threshold

Issue: Roop fails to install or run
Mitigation: Use alternative tool (FaceSwap or Reface app), or use pre-made deepfake videos


DELIVERABLES

1. Dataset:
    - 10-15 real human frame pairs
    - 10-15 deepfake frame pairs
    - Calibration data (stereo_calibration.npz)

2. Results:
    - Error metrics table
    - Detection accuracy statistics
    - Visualization of error distributions

3. Validation Report:
    - Confirmation that geometric inconsistency exists in deepfakes
    - Validated threshold values
    - Proof of concept success/failure analysis
