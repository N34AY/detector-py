# Motion Detection System 🎯

A modern, full-stack motion detection system with Vue 3 frontend, Flask backend, and advanced computer vision capabilities.

## ✨ Features

🎯 **Smart Motion Detection**
- OpenCV-based background subtraction with MOG2
- Advanced rain filtering to reduce false positives  
- Multiple ROI (Region of Interest) support
- Configurable motion sensitivity and thresholds
- Real-time motion status tracking

🌐 **Modern Web Interface**
- Vue 3 + TypeScript + Vite frontend
- Real-time camera feed streaming via WebSocket
- Interactive ROI creation with click-and-drag
- Live motion detection visualization
- Responsive glassmorphism design

🔊 **Smart Notifications**
- Real-time sound alerts for motion detection
- Configurable volume controls
- Motion event tracking and statistics

💤 **System Integration**
- Cross-platform sleep prevention (macOS/Windows/Linux)
- Auto-start sleep prevention with web interface
- Background monitoring capabilities

⚡ **Performance & Architecture**
- Clean, modular Python backend with Flask-SocketIO
- Modern TypeScript frontend with Pinia state management
- Real-time WebSocket communication
- Efficient OpenCV processing pipeline

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd web/frontend

# Install Node.js dependencies
npm install
```

### 3. Development Mode

**Option A: Full Stack Script (Recommended)**
```bash
# From project root, run both frontend and backend
./start.sh
```
- Flask Backend: http://localhost:${WEB_PORT} (default: 5001)
- Vue Frontend: http://localhost:${VITE_DEV_PORT} (default: 5173)

**Option B: Separate Servers**
```bash
# Terminal 1: Start Flask backend
cd web && python3 app.py

# Terminal 2: Start Vue frontend  
cd web/frontend && npm run dev
```

### 4. Production Build

```bash
# Build and start production server
./build.sh
./start-prod.sh
```🔧 Environment Configuration

This project uses environment variables for configuration. See [ENVIRONMENT.md](ENVIRONMENT.md) for detailed setup.

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration as needed
nano .env
```

## 📁 Project Structure

```
detector-py/
├── .env                   # Environment configuration
├── .env.example           # Environment template
├── build.sh               # Production build script
├── start.sh               # Development server script
├── start-prod.sh          # Production server script
├── requirements.txt       # Python dependencies
├── ENVIRONMENT.md         # Environment configuration docs
├── README.md              # This file
├── config/                # Configuration files
│   └── rois.json          # Auto-saved ROI configurations
├── src/                   # Core detection modules
│   └── detector.py        # Clean detector implementation
└── web/                   # Web application
    ├── app.py             # Flask backend with WebSocket
    └── frontend/          # Vue 3 + TypeScript frontend
        ├── src/
        │   ├── components/ # Vue components
        │   ├── stores/     # Pinia state management
        │   └── views/      # Vue pages
        ├── package.json    # Node.js dependencies
        └── vite.config.ts  # Vite configuration
```

## ⚙️ Configuration

### Environment Variables

The system uses environment variables for configuration. Key settings:

- `ENV_MODE` - Application environment (development/production)
- `WEB_HOST` - Flask server host (default: 0.0.0.0)
- `WEB_PORT` - Flask server port (default: 5001)
- `VITE_DEV_PORT` - Vue dev server port (default: 5173)
- `DEFAULT_CAMERA_SOURCE` - Camera index (default: 0)
- `LOG_LEVEL` - Logging level (default: INFO)

See [ENVIRONMENT.md](ENVIRONMENT.md) for complete configuration options.

### Motion Detection Settings

- **Motion Threshold**: Minimum pixel area to trigger detection (default: 800)
- **Rain Filter**: Maximum small contours before considering rain (default: 50)
- **Min Contour Area**: Minimum size for valid motion contours (default: 1500)
- **Motion Smoothing**: Frames required for motion confirmation (default: 3)

### Web Interface Features

1. **Auto-initialization** - System starts automatically when web app loads
2. **Real-time Camera Feed** - Live video stream with WebSocket
3. **Interactive ROI Management** - Create/edit detection zones with mouse
4. **Motion Detection Visualization** - Live motion indicators on ROIs
5. **System Statistics** - FPS, detection counts, and camera status
6. **Modern UI** - Responsive glassmorphism design with Tailwind CSS

## 💡 Usage Tips

### Creating ROIs
- **Web Interface**: Click and drag on the camera feed to create detection zones
- **Auto-loading**: ROIs are automatically saved and restored between sessions

### Motion Detection
- **Real-time Feedback**: Motion detected ROIs are highlighted in real-time
- **Smart Filtering**: Advanced algorithms reduce false positives from rain/shadows
- **Configurable Sensitivity**: Adjust detection parameters via environment variables

## Troubleshooting

### Camera Issues
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

### Dependencies
```bash
# Reinstall Python dependencies
pip install -r requirements.txt

# Reinstall Node.js dependencies
cd web/frontend && npm install
```

### Web Interface Not Loading
1. Check if the configured port is available
   ```bash
   lsof -i :${WEB_PORT:-5001}
   ```
2. Ensure Flask-SocketIO is installed correctly
3. Try running with different port: modify `WEB_PORT` in `.env`

## 🛠️ Development

### Adding New Features
1. **Core detection logic**: Modify `src/detector.py`
2. **Backend API endpoints**: Add to `web/app.py`
3. **Frontend components**: Create/modify Vue components in `web/frontend/src/components/`
4. **State management**: Update Pinia stores in `web/frontend/src/stores/`
5. **Styling**: Use Tailwind CSS classes or modify `web/frontend/src/style.css`

### Architecture
- **Backend**: Flask + Flask-SocketIO for WebSocket communication
- **Frontend**: Vue 3 + TypeScript + Vite + Pinia + Tailwind CSS
- **Detection**: OpenCV MOG2 background subtraction with smart filtering
- **Configuration**: Environment variables with .env file support
- **Real-time**: WebSocket for live camera feed and motion detection updates

## License

This project is open source. Feel free to modify and distribute.

## 🙏 Credits

- **OpenCV**: Computer vision processing and motion detection
- **Flask**: Lightweight web framework with WebSocket support
- **Vue 3**: Modern reactive frontend framework
- **TypeScript**: Type-safe JavaScript development
- **Vite**: Fast frontend build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Socket.IO**: Real-time WebSocket communication