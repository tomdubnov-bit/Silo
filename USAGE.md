# Silo-Sight Usage Guide

Complete guide for using the Silo-Sight deepfake detection system.

## Quick Start

### 1. Calibration (One-Time Setup)

```bash
# Record checkerboard video on Zoom with both cameras
# Split the video
ffmpeg -i zoom_recording.mp4 -filter:v "crop=iw/2:ih:0:0" cam1_checkerboard.mp4
ffmpeg -i zoom_recording.mp4 -filter:v "crop=iw/2:ih:iw/2:0" cam2_checkerboard.mp4

# Run calibration
cd Calibration
python3 stereo_calibrate.py --cam1 cam1_checkerboard.mp4 --cam2 cam2_checkerboard.mp4

# Validate calibration
python3 validate_calibration.py --calibration ../stereo_calibration.npz
```

### 2. Deepfake Detection

```bash
# From Zoom screenshot
python3 detect_deepfake.py --screenshot zoom_screenshot.png

# From separate front/side images
python3 detect_deepfake.py --front front_view.png --side side_view.png

# Save results
python3 detect_deepfake.py --screenshot test.png --output-json result.json --output-csv results.csv
```

## Detailed Workflows

### Calibration Workflow

**What you need:**
- Two cameras (one front-facing, one at 30° angle)
- Printed checkerboard pattern (8x11 squares, 15mm each)
- Zoom or screen recording software

**Steps:**

1. **Setup cameras:**
   - Position Camera 1 facing you directly
   - Position Camera 2 at 30° angle to the right
   - **Do NOT move cameras after calibration!**

2. **Record calibration video:**
   - Start Zoom meeting with both cameras
   - Ensure Gallery View shows cameras side-by-side
   - Start recording
   - Hold checkerboard and move it around for 20 seconds:
     - Close and far
     - Different angles
     - Different positions (left, right, up, down)
   - Stop recording

3. **Process and calibrate:**
   ```bash
   # Split video
   ffmpeg -i zoom_recording.mp4 -filter:v "crop=iw/2:ih:0:0" cam1.mp4
   ffmpeg -i zoom_recording.mp4 -filter:v "crop=iw/2:ih:iw/2:0" cam2.mp4

   # Calibrate
   cd Calibration
   python3 stereo_calibrate.py --cam1 cam1.mp4 --cam2 cam2.mp4
   ```

4. **Validate:**
   ```bash
   python3 validate_calibration.py --calibration ../stereo_calibration.npz
   ```

**Expected output:**
```
✓ CALIBRATION VALIDATION PASSED
RMS error: 0.45 pixels (< 1.0)
Baseline: 28.3 cm
```

---

### Detection Workflow

**What you need:**
- Completed calibration (stereo_calibration.npz)
- Screenshot from Zoom with both cameras visible

**Option 1: Zoom Screenshot (Recommended)**

```bash
# Take screenshot during Zoom call (Cmd+Shift+4 on Mac)
# Ensure both camera views are visible in gallery view

# Run detection
python3 detect_deepfake.py \
  --screenshot zoom_screenshot.png \
  --front-camera left \
  --layout side_by_side
```

**Option 2: Separate Images**

```bash
# If you have pre-split images
python3 detect_deepfake.py \
  --front front_view.png \
  --side side_view.png
```

**Expected output:**

```
======================================================================
SILO-SIGHT DEEPFAKE DETECTION RESULT
======================================================================

✓  REAL HUMAN DETECTED
   Confidence Score: 94.2/100 (High authenticity)

Geometric Consistency Metrics:
  Mean Reprojection Error: 3.127 pixels
  Error Range: 1.234 - 5.891 pixels
  Camera 1 Error: 3.045 pixels
  Camera 2 Error: 3.209 pixels
  Landmarks Analyzed: 10

Detection Thresholds:
  Real Human: < 5.0 pixels
  Deepfake: > 15.0 pixels

Interpretation:
  Low reprojection error indicates geometric consistency between
  the two camera views. The subject appears to be a real 3D human
  face with consistent spatial properties.
======================================================================
```

---

## Command-Line Reference

### detect_deepfake.py

```bash
# Basic usage
python3 detect_deepfake.py --screenshot <path>
python3 detect_deepfake.py --front <path> --side <path>

# Options
--screenshot PATH          Path to Zoom screenshot
--front PATH              Path to front view image
--side PATH               Path to side view image
--layout {side_by_side,stacked}  Camera layout in screenshot
--front-camera {left,right,top,bottom}  Which camera is front-facing
--calibration PATH        Path to calibration file
--output-json PATH        Save result to JSON file
--output-csv PATH         Append result to CSV file
--quiet                   Suppress progress messages

# Examples
python3 detect_deepfake.py --screenshot test.png --output-json result.json
python3 detect_deepfake.py --front f.png --side s.png --quiet
python3 detect_deepfake.py --screenshot test.png --layout stacked --front-camera top
```

### Exit Codes

- `0`: Real human detected
- `1`: Deepfake detected or error occurred

---

## Module Testing

### Test Landmark Detection

```bash
cd "2D Detection"
python3 landmark_detector.py ../test_image.png output_with_landmarks.png
```

### Test 3D Triangulation

```bash
cd "3D Estimation"
python3 triangulator.py ../stereo_calibration.npz
```

### Test Error Calculator

```bash
cd Comparison
python3 error_calculator.py
```

### Test Scorer

```bash
cd Output
python3 scorer.py
```

---

## Troubleshooting

### "Calibration file not found"
- Run `stereo_calibrate.py` first
- Check that `stereo_calibration.npz` exists in project root

### "No face detected"
- Ensure face is clearly visible in both camera views
- Check lighting (face should be well-lit)
- Try different head position

### "High reprojection error for real human"
- Cameras may have moved since calibration → recalibrate
- Calibration quality may be poor → check validation
- Screenshot timing mismatch → ensure synchronized capture

### "Low reprojection error for deepfake"
- Deepfake may use 3D modeling (advanced)
- Try different deepfake source
- Check that you're testing actual deepfake, not screen replay

---

## File Structure

```
Silo/
├── detect_deepfake.py          ← Main detection script
├── config.py                   ← Configuration
├── stereo_calibration.npz      ← Calibration data (generated)
│
├── Calibration/
│   ├── stereo_calibrate.py    ← Calibration script
│   └── validate_calibration.py
│
├── Ingestion/
│   └── frame_loader.py         ← Frame/screenshot loading
│
├── 2D Detection/
│   └── landmark_detector.py    ← MediaPipe facial landmarks
│
├── 3D Estimation/
│   └── triangulator.py         ← 3D triangulation
│
├── Comparison/
│   └── error_calculator.py     ← Reprojection error
│
└── Output/
    └── scorer.py               ← Scoring and results
```

---

## Validation Testing

### Phase 1: 2D vs 3D Test
Test with printed photo:
```bash
# Display photo on screen, capture with both cameras
python3 detect_deepfake.py --screenshot photo_on_screen.png
# Should detect as deepfake (high error)
```

### Phase 2: Real Human Baseline
```bash
# Capture yourself with both cameras
python3 detect_deepfake.py --screenshot real_human.png
# Should detect as real (low error ~2-5px)
```

### Phase 3: Deepfake Test
```bash
# Create deepfake, play on screen, capture
python3 detect_deepfake.py --screenshot deepfake_on_screen.png
# Should detect as deepfake (high error >15px)
```

---

## Tips for Best Results

1. **Good lighting** - Face should be evenly lit from both angles
2. **Clear view** - Face fully visible in both cameras
3. **Still pose** - Don't move during screenshot
4. **Fixed cameras** - Never move cameras after calibration
5. **Synchronized screenshots** - Both views captured at same instant

---

## Next Steps After POC

1. Test with multiple subjects
2. Test with different deepfake methods
3. Tune thresholds based on results
4. Add visualization outputs
5. Batch processing for multiple tests
