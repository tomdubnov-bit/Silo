# Footage Recording Improvements Guide

**Goal**: Achieve calibration RMS error < 1.0 pixels (currently 4.72 pixels)

This document outlines specific improvements needed when re-recording calibration footage and detection test screenshots to achieve optimal system performance.

---

## Calibration Video Improvements

### Critical Issues to Fix

#### 1. **Checkerboard Flatness** ⭐ HIGHEST PRIORITY
**Current Issue**: Checkerboard appears warped/curved, causing corner detection errors

**Solutions**:
- Mount checkerboard on rigid backing (cardboard, foam board, or acrylic sheet)
- Print on stiff paper or laminate the printout
- Alternative: Purchase a professional calibration board
- Ensure board doesn't bend when held
- Test flatness: lay on table and check for gaps/warping

#### 2. **Camera Angle** ⭐ HIGH PRIORITY
**Current Issue**: Side camera only ~15-20° from frontal (target: 30°+)

**Solutions**:
- Position side camera at **30-45° angle** from front camera
- Use protractor or angle measurement app to verify
- Sharper angle = better stereo triangulation accuracy
- Do NOT go beyond 60° (landmarks become hard to detect from extreme profiles)

**Setup suggestion**:
```
        Front Camera (0°)
              |
              |
              |
          [Subject]
            /
           /
          /
    Side Camera (30-45°)
```

#### 3. **Lighting Quality**
**Current Issue**: Shadows and uneven lighting affect corner detection

**Solutions**:
- Use **diffuse, even lighting** (avoid direct overhead lights)
- Minimize shadows on checkerboard
- Avoid reflections/glare (especially on glossy checkerboard surfaces)
- Natural daylight from window works well (avoid direct sunlight)
- If using lamps: position them to the sides, not directly above

**Ideal setup**: Soft, even illumination across entire checkerboard from multiple angles

#### 4. **Camera Stability**
**Current Issue**: Camera movement during recording affects calibration

**Solutions**:
- Use tripods or stable mounts for BOTH cameras
- If no tripods: prop cameras on stable surfaces (books, boxes)
- Ensure cameras don't shift during 60-second recording
- Lock laptop/phone position before starting
- Test stability: record 5 seconds, check if frame is steady

#### 5. **Recording Duration and Variety**
**Current**: 70 seconds, decent variety but could be better

**Improvements**:
- Record for **60-90 seconds** total
- Include these positions systematically:
  - **Close to cameras** (30-40cm away) - 10 seconds
  - **Far from cameras** (80-100cm away) - 10 seconds
  - **Center frame** - 10 seconds
  - **Left side of frame** - 10 seconds
  - **Right side of frame** - 10 seconds
  - **Top of frame** - 10 seconds
  - **Bottom of frame** - 10 seconds
  - **Tilted 30° left** - 5 seconds
  - **Tilted 30° right** - 5 seconds
  - **Rotated 45° clockwise** - 5 seconds
  - **Rotated 45° counter-clockwise** - 5 seconds

**Movement tips**:
- Move slowly and deliberately
- Pause 1-2 seconds in each position
- Keep board parallel to cameras (not angled away)
- Ensure board stays in BOTH camera views at all times

#### 6. **Board Size in Frame**
**Optimal**: Checkerboard should fill 40-60% of frame

- Too small: Poor corner detection accuracy
- Too large: Corners near edges may be missed
- Vary size during recording (as mentioned above)

---

## Detection Screenshot Improvements

### Head Position Variety

Based on test results, these positions are recommended:

#### Best Performing Positions
1. **Head tilted slightly up** (SS2 - lowest error: 39.5 pixels)
   - Look slightly above camera level
   - Natural, comfortable pose

#### Standard Test Positions (Take all 5)

1. **Neutral/Straight** (SS1)
   - Head level, looking directly at front camera
   - Neutral expression
   - This is your baseline

2. **Tilted Up** (SS2) ⭐ RECOMMENDED
   - Chin slightly raised
   - Look ~15° above front camera
   - Best geometric consistency in current tests

3. **Tilted Down**
   - Chin slightly lowered
   - Look ~15° below front camera
   - Tests lower face landmarks

4. **Turned Left**
   - Rotate head ~10-15° to your left
   - Keep facing generally forward
   - Tests landmark visibility at rotation

5. **Turned Right**
   - Rotate head ~10-15° to your right
   - Keep facing generally forward
   - Mirror of position 4

### Screenshot Quality Guidelines

#### Lighting
- Same lighting as calibration video (consistent conditions)
- Even illumination on face
- Avoid harsh shadows on nose/chin

#### Expression
- **Neutral expression** (no smiling, talking, or facial movements)
- Eyes open naturally
- Relaxed face muscles
- Remember: We're using expression-invariant landmarks, but extreme expressions could still affect detection

#### Camera Position
- **DO NOT MOVE CAMERAS** after calibration
- Use exact same setup as calibration video
- Even 1cm of camera movement invalidates calibration

#### Focus and Clarity
- Ensure face is in focus in BOTH views
- No motion blur
- High resolution (current 3420x2214 is good)

#### Zoom Controls
- Disable any auto-focus or auto-zoom
- Lock camera settings if possible
- Consistent framing with calibration video

---

## Recording Checklist

### Pre-Recording Setup
- [ ] Print/mount checkerboard on rigid backing
- [ ] Verify board is flat (no warping)
- [ ] Set up both cameras on stable mounts
- [ ] Measure camera angle: 30-45° separation
- [ ] Verify both cameras have same height
- [ ] Set up even, diffuse lighting
- [ ] Test frame in Zoom - board should be ~40-60% of frame
- [ ] Lock camera positions (mark with tape if needed)

### During Calibration Recording
- [ ] Start recording in Zoom
- [ ] Move slowly through all positions (close, far, left, right, top, bottom, tilted, rotated)
- [ ] Pause 1-2 seconds in each position
- [ ] Keep board in BOTH camera views at all times
- [ ] Verify board stays flat (don't let it bend)
- [ ] Record for 60-90 seconds total

### After Calibration Recording
- [ ] Stop recording
- [ ] Download video from Zoom
- [ ] Run split_zoom_video.py to split into cam1/cam2
- [ ] Run stereo_calibrate.py on split videos
- [ ] Check RMS error: **MUST be < 1.0 pixels**
- [ ] If RMS > 1.0: re-record with better technique

### Detection Screenshots
- [ ] **Verify cameras haven't moved since calibration**
- [ ] Join new Zoom meeting with same camera setup
- [ ] Take screenshot in neutral position (SS1)
- [ ] Take screenshot tilted up (SS2)
- [ ] Take screenshot tilted down
- [ ] Take screenshot turned left
- [ ] Take screenshot turned right
- [ ] Download all screenshots
- [ ] Test with detect_deepfake.py

---

## Expected Results After Improvements

### Calibration Quality Targets
- **RMS error**: < 1.0 pixels (currently 4.72)
- **Checkerboard detection rate**: > 80% of frames in both cameras
- **Synchronized pairs**: > 50 frame pairs with successful detection in both views

### Detection Error Targets
Once calibration is good, you should see:
- **Real human error**: 2-5 pixels (currently 40-60 pixels)
- **Deepfake error**: > 15-20 pixels (with good calibration, geometric inconsistency will be clear)

### Consistency Checks
- Camera 1 and Camera 2 errors should be similar (within 2-3 pixels of each other)
- Error should be consistent across different head positions (±2-3 pixels variance)
- Standard deviation should be low (< 5 pixels)

---

## Common Mistakes to Avoid

1. ❌ **Moving cameras between calibration and detection**
   - Invalidates entire calibration
   - Even small movements matter

2. ❌ **Using different Zoom settings/layouts**
   - Keep same side-by-side layout
   - Same camera positions in Zoom grid

3. ❌ **Rushing through calibration positions**
   - Move slowly, pause in each position
   - Fast movement = motion blur = bad corner detection

4. ❌ **Checkerboard too close to edge of frame**
   - Keep board centered with margins on all sides
   - Corners near frame edges are often distorted

5. ❌ **Recording in low light**
   - Checkerboard corners need clear contrast
   - Dim lighting = poor detection accuracy

6. ❌ **Ignoring RMS error**
   - If RMS > 1.0, don't proceed to detection
   - Re-record calibration until RMS is acceptable

---

## Troubleshooting Guide

### If RMS error is still high after improvements:

1. **Check for board warping**
   - Lay board flat on table
   - Look for gaps/curves
   - Re-mount on stiffer backing

2. **Verify camera angle**
   - Measure actual angle with protractor
   - Should be 30-45°, not less

3. **Check lighting consistency**
   - Look for shadows moving during recording
   - Ensure even illumination throughout

4. **Review corner detection logs**
   - Look for patterns in missed frames
   - Certain positions might consistently fail

5. **Try professional calibration board**
   - Printed boards can warp
   - Commercial boards are laser-cut and rigid

---

## Success Criteria Summary

✅ **Ready to proceed when**:
- Calibration RMS error < 1.0 pixels
- Detection errors for real person: 2-5 pixels
- Consistent errors across different head positions
- Camera 1 and Camera 2 errors are similar

🔴 **Re-record if**:
- Calibration RMS error > 1.0 pixels
- Detection errors > 10 pixels for real person
- Large variance between different head positions
- Asymmetric errors between cameras (one camera much worse)

---

**Last Updated**: 2025-11-10
**Current Calibration RMS**: 4.72 pixels (TARGET: < 1.0 pixels)
**Current Detection Error Range**: 39-62 pixels (TARGET: 2-5 pixels)
