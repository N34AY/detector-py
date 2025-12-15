# Environment Configuration

This project uses environment variables for configuration management. All configuration is stored in a `.env` file to avoid hardcoding values in the source code.

## Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your specific configuration:
   ```bash
   nano .env  # or use your preferred editor
   ```

## Environment Variables

### Server Configuration
- `WEB_HOST` - Flask server host (default: `0.0.0.0`)
- `WEB_PORT` - Flask server port (default: `5001`)
- `VITE_DEV_PORT` - Vue.js development server port (default: `5173`)

### Application Configuration
- `ENV_MODE` - Application environment (`development` or `production`)
- `DEBUG_MODE` - Enable Flask debug mode (`true` or `false`)
- `FLASK_SECRET_KEY` - Flask session secret key (change in production!)

### Camera & Detection
- `DEFAULT_CAMERA_SOURCE` - Default camera index (default: `0`)
- `DEFAULT_SENSITIVITY` - Motion detection sensitivity (default: `50`)
- `DEFAULT_MIN_AREA` - Minimum detection area (default: `1000`)

### Logging & CORS
- `LOG_LEVEL` - Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `CORS_ORIGINS` - CORS allowed origins (default: `*`)

### Production Configuration
- `STATIC_FOLDER` - Static files directory for production (default: `frontend/dist`)
- `STATIC_URL_PATH` - URL path for static files (default: empty)

## Usage Examples

### Development Mode
```bash
# Start with default settings
./start.sh

# Start with custom port
WEB_PORT=8080 ./start.sh
```

### Production Mode
```bash
# Build and start production server
./build.sh
./start-prod.sh

# Start production with custom configuration
ENV_MODE=production WEB_PORT=8080 ./start-prod.sh
```

### Environment Override
You can override any environment variable on the command line:
```bash
# Temporary override
WEB_HOST=127.0.0.1 WEB_PORT=3000 ./start.sh

# Multiple overrides
ENV_MODE=production LOG_LEVEL=DEBUG ./start-prod.sh
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit the `.env` file** to version control (it's in `.gitignore`)
2. **Change `FLASK_SECRET_KEY`** to a secure random value in production
3. **Set specific `CORS_ORIGINS`** instead of `*` for production environments
4. **Use HTTPS** in production by configuring a reverse proxy (nginx, Apache)
5. **Restrict `WEB_HOST`** to specific interfaces if needed for security

## File Structure

```
detector-py/
├── .env                 # Your configuration (not committed)
├── .env.example         # Template with default values
├── start.sh             # Development server (loads .env)
├── start-prod.sh        # Production server (loads .env)
├── build.sh             # Frontend build script
└── web/
    ├── app.py           # Flask app (uses environment variables)
    └── frontend/
        ├── vite.config.ts    # Vite config (uses environment variables)
        └── src/
            └── stores/detector.ts    # Socket connection (environment-aware)
```

## Troubleshooting

### Environment Variables Not Loading
- Ensure `.env` file exists and is readable
- Check for syntax errors in `.env` (no spaces around `=`)
- Verify the script is run from the project root directory

### Port Already in Use
- Change `WEB_PORT` or `VITE_DEV_PORT` in `.env`
- Or override on command line: `WEB_PORT=8080 ./start.sh`
- Find and stop the conflicting process: `lsof -i :$WEB_PORT`

### Production vs Development
- Development: Uses separate Flask and Vue.js dev servers
- Production: Flask serves built Vue.js static files
- Set `ENV_MODE=production` for production mode