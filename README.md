# Person Detection System

A clean, modular person detection system with rain filtering and web interface.

## Features

🎯 **Core Detection**
- YOLO-based person detection
- Background subtraction motion detection
- Advanced rain filtering to reduce false positives
- Multiple ROI (Region of Interest) support
- Real-time motion smoothing

🌐 **Web Interface**
- Live camera feed streaming
- Interactive ROI creation with mouse
- Real-time motion sensitivity controls
- Rain detection status indicators
- Bootstrap-based responsive UI

⚡ **Performance**
- Modular, clean architecture
- Configurable detection parameters
- Efficient OpenCV processing
- WebSocket real-time updates

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Web Interface

```bash
python start_web.py
```

Then open http://localhost:5001 in your browser.

### 3. Run Command Line Interface

```bash
# Basic usage
python main.py

# Custom options
python main.py --camera 1 --threshold 1000 --fullscreen
```

## Project Structure

```
detector-py/
├── main.py                 # Standalone CLI detector
├── start_web.py            # Web interface launcher
├── requirements.txt        # Dependencies
├── README.md              # This file
├── config/                # Configuration files
│   └── rois.json          # Auto-saved ROI configurations
├── src/                   # Core detection modules
│   ├── detector.py   # Clean detector implementation
└── web/                   # Web application
    ├── app.py             # Flask web server
    ├── static/
    │   └── app.js         # Clean frontend JavaScript
    └── templates/
        └── index.html     # Web interface HTML
```

## Configuration

### Motion Detection Settings

- **Motion Threshold**: Minimum pixel area to trigger detection (default: 800)
- **Rain Filter**: Maximum small contours before considering rain (default: 50)
- **Min Contour Area**: Minimum size for valid motion contours (default: 1500)
- **Motion Smoothing**: Frames required for motion confirmation (default: 3)

### Web Interface Controls

1. **Initialize System** - Load YOLO model and setup detector
2. **Start/Stop Camera** - Control camera feed
3. **ROI Management** - Create/delete detection zones
4. **Motion Sensitivity** - Adjust detection parameters in real-time
5. **Rain Detection** - Visual indicator when rain filtering is active

## Usage Tips

### Creating ROIs
- **Web Interface**: Click and drag on camera feed
- **CLI Interface**: Click and drag on OpenCV window

### Rain Filtering
The system automatically detects rain patterns and reduces false positives by:
- Analyzing contour sizes and quantities
- Requiring consistent motion over multiple frames
- Filtering out small, numerous motion areas

### Keyboard Controls (CLI)
- `q` - Quit
- `r` - Clear all ROIs
- `s` - Save ROIs to file
- `l` - Load ROIs from file

## Troubleshooting

### Camera Issues
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

### YOLO Model Download
Models are downloaded automatically on first run. For manual download:
```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### Web Interface Not Loading
1. Check if port 5001 is available
2. Ensure Flask-SocketIO is installed correctly
3. Try running with different port: modify `WEB_PORT` in `web/app.py`

## Development

### Adding New Features
1. Core detection logic: Modify `src/detector.py`
2. Web API endpoints: Add to `web/app.py`
3. Frontend functionality: Update `web/static/app.js`

### Code Structure
- `DetectorConfig`: Configuration management
- `PersonDetector`: Core detection logic with rain filtering
- `WebDetector`: Web interface wrapper
- `DetectorWebUI`: Frontend JavaScript class

## License

This project is open source. Feel free to modify and distribute.

## Credits

- **YOLO**: Ultralytics YOLO for person detection
- **OpenCV**: Computer vision processing
- **Flask**: Web framework
- **Bootstrap**: UI components