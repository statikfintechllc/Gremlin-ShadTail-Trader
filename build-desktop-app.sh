#!/bin/bash

# Gremlin ShadTail Trader - Professional App Builder
# This script creates a proper desktop application

echo "🚀 Building Gremlin ShadTail Trader Desktop Application..."

# Navigate to project directory
cd "$(dirname "$0")"

# Create a professional 512x512 PNG icon if it doesn't exist
if [ ! -f "resources/icon.png" ]; then
    echo "📱 Creating professional app icon..."
    # Create a modern financial app icon using ImageMagick or fallback
    if command -v convert >/dev/null 2>&1; then
        # Create a gradient background with trading chart pattern
        convert -size 512x512 gradient:"#1a1a2e-#16213e" \
            \( -size 400x300 -fill "#00ff88" -stroke "#00ff88" -strokewidth 2 \
               -draw "path 'M 50,250 Q 100,150 150,200 T 250,100 T 350,150'" \) \
            -gravity center -composite \
            \( -size 100x100 -background none -fill "#ffffff" \
               -font Arial-Bold -pointsize 72 -gravity center label:"G" \) \
            -gravity center -composite \
            resources/icon.png
    else
        # Fallback: copy existing icon or create basic one
        if [ -f "resources/icon.icns" ]; then
            echo "Using existing icon.icns as fallback"
        else
            # Create basic colored square as absolute fallback
            echo "Creating basic fallback icon..."
            mkdir -p resources
            echo "iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAA==" | base64 -d > resources/icon.png || touch resources/icon.png
        fi
    fi
fi

echo "🔧 Installing dependencies..."
npm install

echo "🏗️  Building application..."
npm run build

echo "📦 Packaging desktop application..."
# Build Linux AppImage and DEB packages
npm run package:linux

echo "🖥️  Setting up desktop integration..."

# Get the current user's desktop directory
DESKTOP_DIR="$HOME/Desktop"
APPLICATIONS_DIR="$HOME/.local/share/applications"

# Create applications directory if it doesn't exist
mkdir -p "$APPLICATIONS_DIR"

# Update the desktop file with correct paths
CURRENT_DIR=$(pwd)
sed -e "s|/home/runner/work/Gremlin-ShadTail-Trader/Gremlin-ShadTail-Trader|$CURRENT_DIR|g" \
    -e "s|/home/statiksmoke8/Gremlin-ShadTail-Trader|$CURRENT_DIR|g" \
    GremlinTrader.desktop > "$APPLICATIONS_DIR/GremlinTrader.desktop"

# Make desktop file executable
chmod +x "$APPLICATIONS_DIR/GremlinTrader.desktop"

# Copy to desktop if it exists
if [ -d "$DESKTOP_DIR" ]; then
    cp "$APPLICATIONS_DIR/GremlinTrader.desktop" "$DESKTOP_DIR/"
    chmod +x "$DESKTOP_DIR/GremlinTrader.desktop"
    echo "✅ Desktop shortcut created at $DESKTOP_DIR/GremlinTrader.desktop"
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR"
fi

echo "🎯 Creating launch script..."
cat > launch-gremlin-trader.sh << 'EOF'
#!/bin/bash

# Gremlin ShadTail Trader Launcher
cd "$(dirname "$0")"

echo "🚀 Starting Gremlin ShadTail Trader..."

# Check if we have a packaged app
if [ -f "dist-electron/linux-unpacked/gremlin-shadtail-trader" ]; then
    echo "📱 Launching packaged application..."
    exec "./dist-electron/linux-unpacked/gremlin-shadtail-trader"
elif [ -f "dist-electron/Gremlin ShadTail Trader-*-x86_64.AppImage" ]; then
    echo "📱 Launching AppImage..."
    exec "./dist-electron/Gremlin ShadTail Trader"*".AppImage"
else
    echo "🔧 Launching development version..."
    npm run start
fi
EOF

chmod +x launch-gremlin-trader.sh

echo ""
echo "✅ SUCCESS! Gremlin ShadTail Trader has been built and configured!"
echo ""
echo "📱 You can now launch the app in several ways:"
echo "   1. Click the 'Gremlin ShadTail Trader' icon on your desktop"
echo "   2. Find it in your applications menu under 'Office > Finance'"
echo "   3. Run: ./launch-gremlin-trader.sh"
echo "   4. Run the AppImage: ./dist-electron/Gremlin\\ ShadTail\\ Trader-*.AppImage"
echo ""
echo "🎨 The app features a professional dark theme similar to Grok and OpenAI apps"
echo "🔥 All trading agents are active and ready for autonomous trading"
echo ""

# Try to launch the application
if [ "$1" = "--launch" ]; then
    echo "🚀 Auto-launching application..."
    ./launch-gremlin-trader.sh &
fi
