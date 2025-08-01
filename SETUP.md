# Silo-Sight Setup Guide

## Prerequisites

- Python 3.10 or higher
- FFmpeg (for video processing)

## Installation

### 1. Install System Dependencies

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install FFmpeg
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg python3-pip python3-venv
```

**Windows:**
```bash
# Install FFmpeg from https://ffmpeg.org/download.html
# Or use Chocolatey: choco install ffmpeg
```

### 2. Clone Repository

```bash
git clone <your-repo-url>
cd Silo
```

### 3. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when activated.

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- OpenCV (computer vision)
- MediaPipe (facial landmarks)
- NumPy, SciPy (numerical computing)
- Matplotlib (visualization)

### 5. Verify Installation

```bash
python3 -c "import cv2, mediapipe, numpy; print('All dependencies installed successfully!')"
```

## Quick Start

### Calibration

1. Record checkerboard video on Zoom with both cameras visible
2. Split video into two camera feeds:
   ```bash
   ffmpeg -i zoom_recording.mp4 -filter:v "crop=iw/2:ih:0:0" cam1_checkerboard.mp4
   ffmpeg -i zoom_recording.mp4 -filter:v "crop=iw/2:ih:iw/2:0" cam2_checkerboard.mp4
   ```
3. Run calibration:
   ```bash
   cd Calibration
   python3 stereo_calibrate.py --cam1 cam1_checkerboard.mp4 --cam2 cam2_checkerboard.mp4
   ```

See [Calibration/README.md](Calibration/README.md) for detailed instructions.

## Deactivating Virtual Environment

When you're done working:
```bash
deactivate
```

## Troubleshooting

### "python3: command not found"
- Install Python from https://python.org
- Or use `python` instead of `python3`

### "pip: command not found"
- Use `pip3` instead of `pip`
- Or reinstall Python with pip included

### Import errors after installation
- Ensure virtual environment is activated (see `(venv)` in prompt)
- Try reinstalling: `pip install --force-reinstall -r requirements.txt`

### FFmpeg not found
- Verify installation: `ffmpeg -version`
- Add to PATH if installed but not found
