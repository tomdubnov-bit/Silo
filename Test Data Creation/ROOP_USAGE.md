# Roop Setup and Usage Guide

**Purpose**: Create deepfake test images to validate Silo-Sight detection system

**Note**: This project has been discontinued but still works for our testing purposes.

---

## Installation

### 1. Install Dependencies

You're on macOS M4, so you'll need the Silicon-optimized version:

```bash
cd "Test Data Creation/roop"

# Install in your existing venv
source ../../venv/bin/activate

# Install Roop dependencies
pip install -r requirements.txt
```

**Note**: Installation may take 5-10 minutes due to TensorFlow and other large packages.

### 2. Verify Installation

```bash
python run.py --help
```

If this shows the help menu, installation succeeded.

---

## Creating Test Deepfakes

### Method 1: Simple Face Swap (Quick Test)

**Use case**: Swap a celebrity face onto one camera view in SS2

```bash
# Basic command structure
python run.py \
  --source /path/to/celebrity_face.jpg \
  --target /path/to/SiloSight_SS2.png \
  --output /path/to/SS2_deepfake.png
```

**Problem with this approach**:
- Only swaps ONE face in the image
- SS2 has TWO faces (left and right camera views)
- Would need to manually swap both faces

### Method 2: Screen Replay (Recommended for POC)

This is the better approach for your stereo vision test:

#### Step-by-Step Process

1. **Optional: Create a face-swapped version of SS2**
   ```bash
   python run.py \
     --source celebrity_face.jpg \
     --target ../../SiloSight_SS2.png \
     --output SS2_with_deepfake.png
   ```

2. **Display the image on your laptop/tablet screen**
   - Open `SS2_with_deepfake.png` (or just use original SS2)
   - Make it fullscreen or as large as possible

3. **Set up cameras to record the screen**
   - Position both cameras at the same angles as your calibration
   - Point them at the screen displaying the image
   - Join Zoom meeting

4. **Capture screenshot**
   - The cameras are now viewing a 2D representation
   - Take Zoom screenshot of this setup

5. **Run detection**
   ```bash
   cd ../..  # Back to Silo root
   python detect_deepfake.py --screenshot /path/to/screen_replay_screenshot.png --front-camera right
   ```

**Expected result**: Higher geometric error than real person, because:
- Screen is flat (2D surface)
- No actual 3D depth
- Violates stereo geometry assumptions

---

## Finding Source Faces for Testing

### Free Celebrity Face Sources

1. **Unsplash** (royalty-free): https://unsplash.com/s/photos/portrait
2. **Pexels** (royalty-free): https://www.pexels.com/search/portrait/
3. **This Person Does Not Exist** (AI-generated, no copyright): https://thispersondoesnotexist.com/
   - Refresh page to get new AI-generated face
   - Right-click and save image

### Requirements for Source Face

- ✓ Clear frontal view
- ✓ Good lighting
- ✓ High resolution (at least 512x512)
- ✓ Single face in image
- ✓ Neutral or slight expression
- ✗ Avoid: sunglasses, heavy makeup, extreme angles

---

## Roop Command Examples

### Basic Face Swap
```bash
python run.py \
  --source celebrity_face.jpg \
  --target ../../SiloSight_SS2.png \
  --output deepfake_output.png
```

### Face Swap with Quality Settings
```bash
python run.py \
  --source celebrity_face.jpg \
  --target ../../SiloSight_SS2.png \
  --output deepfake_output.png \
  --temp-frame-quality 100 \
  --execution-threads 4
```

### Swap All Faces (if multiple faces in image)
```bash
python run.py \
  --source celebrity_face.jpg \
  --target ../../SiloSight_SS2.png \
  --output deepfake_output.png \
  --many-faces
```

---

## Troubleshooting

### "No face detected in source image"
- Use a clearer frontal face photo
- Ensure face is well-lit
- Try a different source image

### "No face detected in target image"
- Your SS2 should have faces detected
- Check that image path is correct
- Try with `--many-faces` flag

### Installation errors
- Make sure you're in the venv: `source venv/bin/activate`
- For M1/M2/M3/M4 Mac: You need `onnxruntime-silicon` (should install automatically)
- If TensorFlow fails: Try `pip install tensorflow-macos`

### Slow processing
- Expected on first run (downloads model ~300MB)
- M4 Mac should process an image in 5-30 seconds
- Use `--execution-threads 4` to speed up

---

## Expected Workflow for Tomorrow

### Test 1: Real Person (Baseline)
1. Good calibration with flat checkerboard
2. Take 5 screenshots (neutral, up, down, left, right)
3. Run detection on all 5
4. **Expected**: 2-5 pixel errors (with good calibration)

### Test 2: Screen Replay (2D Test)
1. Display SS2 on screen
2. Point cameras at screen
3. Take Zoom screenshot
4. Run detection
5. **Expected**: Higher errors (>10-15 pixels) due to lack of 3D depth

### Test 3: Face-Swapped Deepfake (Optional)
1. Use Roop to swap celebrity face onto SS2
2. Display on screen
3. Point cameras at screen
4. Take Zoom screenshot
5. Run detection
6. **Expected**: Similar to Test 2 (2D geometry violation)

---

## Alternative: Skip Roop and Use Screen Replay Only

**Simplest approach for POC validation**:

You don't actually need to create a face-swapped deepfake. The screen replay method alone demonstrates the core concept:

1. **Real 3D person** → Low geometric error (2-5 pixels)
2. **2D screen representation** → High geometric error (>10-15 pixels)

This proves your system can distinguish 3D geometry from 2D, which is the fundamental principle behind detecting deepfakes.

**When to use actual face swap**:
- Demonstrating to investors/stakeholders
- Publishing results
- More realistic validation
- Testing specific deepfake artifacts

**For POC tomorrow**: Screen replay is sufficient and faster.

---

## Notes

- Roop is discontinued but stable
- Works well for single-image face swaps
- Processing time: 5-30 seconds per image on M4
- First run downloads ~300MB model file
- Output quality is good enough for testing

---

**Created**: 2025-11-10
**Roop Version**: Final release (discontinued project)
**Testing Purpose**: Validate Silo-Sight can detect geometric inconsistency in deepfakes
