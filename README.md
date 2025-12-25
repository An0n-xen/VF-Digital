# VF-Digital: Video Fingerprinting & Recognition System

A powerful video recognition system built in Python, based on the algorithm from **"Robust Video Fingerprinting for Content-Based Video Identification"**. It uses gradient-based fingerprinting and sliding window search to create unique fingerprints for video content, allowing for fast and accurate identification of videos even from short, low-quality clips.

## 🌟 Key Features

- **Fast Video Identification**: Identify videos from short clips (as little as 5-10 seconds)
- **Robust Fingerprinting**: Uses gradient orientation analysis that is resilient to compression and quality changes
- **Real-time Stage Tracking**: Visual UI shows all 4 processing stages with live indicators
- **Modern Web Interface**: Sonic Identify-inspired Flask UI with cyan/purple gradients and drag-and-drop
- **Efficient Storage**: Automatic cleanup deletes uploaded videos every 15 minutes (fingerprints preserved)
- **Database Management**: NumPy-based fingerprint storage with JSON metadata

## 🚀 How It Works

The system follows a three-phase pipeline to fingerprint and identify videos:

### 1. Video Preprocessing

The raw video is converted into a standardized format for fingerprinting:

- **Frame Extraction**: Sample frames at **10 FPS** (1 frame every ~100ms)
- **Grayscale Conversion**: Convert to single-channel grayscale for faster processing
- **Standardized Resolution**: Resize all frames to **320×240** pixels
- **Optimization**: Skip frames intelligently using `cap.grab()` for speed

This creates a uniform representation regardless of source video format, frame rate, or resolution.

### 2. Fingerprint Extraction (Gradient Analysis)

We process each frame to extract robust features based on **gradient orientation**:

#### Grid Division
Each 320×240 frame is divided into an **8-block grid** (2 rows × 4 columns):

```
┌─────┬─────┬─────┬─────┐
│  1  │  2  │  3  │  4  │  (120px × 160px each)
├─────┼─────┼─────┼─────┤
│  5  │  6  │  7  │  8  │
└─────┴─────┴─────┴─────┘
```

#### Gradient Computation
For each block, we calculate:

1. **Horizontal Gradients (Gx)**: Using Sobel operator → detects vertical edges
2. **Vertical Gradients (Gy)**: Using Sobel operator → detects horizontal edges
3. **Magnitude**: `r = √(Gx² + Gy²)` → edge strength
4. **Orientation**: `θ = arctan2(Gy, Gx)` → edge direction

#### Centroid Calculation
The fingerprint for each block is the **weighted orientation centroid**:

```
Fingerprint = Σ(r × θ) / Σ(r)
```

This creates an **8-dimensional feature vector** per frame that captures the spatial structure of the image.

**Result**: A video becomes a sequence of 8-element fingerprints, one per frame.

### 3. Database Storage

Fingerprints are stored efficiently for fast retrieval:

- **Format**: Compressed NumPy arrays (`.npy` files)
- **Metadata**: JSON file with video names, frame counts, and durations
- **Memory Mapping**: Large fingerprint arrays are memory-mapped for efficient search
- **Structure**:
  ```
  video_db/
  ├── fingerprints/
  │   ├── uuid1.npy    # N×8 array
  │   ├── uuid2.npy
  │   └── ...
  └── metadata.json
  ```

### 4. Matching & Scoring (Sliding Window Search)

When identifying a video clip:

1. **Query Processing**: Extract fingerprints from the query video (K frames)
2. **Database Scan**: For each video in the database:
   - Load fingerprints using memory mapping
   - Slide a K-frame window across the entire video
   - Calculate Euclidean distance at each position:
     ```
     Score = mean((Query - Window)²)
     ```
3. **Best Match**: Track the lowest score across all videos and positions
4. **Threshold Check**: Match is valid if score < threshold (default: 0.4)
5. **Early Stopping**: Stop searching if a near-perfect match is found (score < 0.01)

**Output**: Video name, timestamp (in seconds), and confidence score


## 📊 Technical Specifications

### Performance
- **Frame Processing**: ~10-50 frames/second (depends on video resolution)
- **Search Speed**: Linear O(N×M) where N = database frames, M = query frames
- **Memory**: Memory-mapped arrays enable searching large databases without loading into RAM

### Algorithm Parameters
```python
TARGET_FPS = 10              # Sampling rate
TARGET_SIZE = (320, 240)     # Frame dimensions  
GRID_SIZE = (2, 4)           # 8 blocks per frame
SEARCH_THRESHOLD = 0.4       # Match sensitivity
EARLY_STOP_THRESHOLD = 0.01  # Perfect match threshold
```

### Storage Efficiency
- **Fingerprint Size**: 8 floats × 4 bytes = 32 bytes per frame
- **Example**: 10-minute video at 10fps = 6000 frames = 192 KB
- **Compression**: NumPy's compressed format reduces size further
- **Cleanup**: Uploaded videos auto-deleted every 15 minutes (saves gigabytes)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/an0n-xen/VF-Digital.git
cd VF-Digital

# Install dependencies
pip install -r requirements.txt
# or if using uv/poetry
uv sync
```

### Run the Application

```bash
python app.py
```

Open your browser to: **http://127.0.0.1:5000**

### Usage

1. **Add Videos to Database**:
   - Click "ADD VIDEO" tab
   - Drag & drop a video or click to browse
   - (Optional) Enter a custom name
   - Click "ADD TO DATABASE"
   - Watch the 4 processing stages complete

2. **Search for Videos**:
   - Click "FIND VIDEO" tab
   - Upload a short clip (even a few seconds works!)
   - Adjust threshold if needed (lower = stricter)
   - Click "SEARCH DATABASE"
   - View match results with exact timestamp

## 📁 Project Structure

```
VF-Digital/
├── app.py                      # Flask web application + cleanup thread
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # Sonic Identify UI
├── static/
│   ├── style.css              # Cyan/purple styling
│   └── script.js              # Stage tracker logic
├── utils/
│   ├── database.py            # VideoDatabase class
│   ├── video_utils.py         # Preprocessing & fingerprinting
│   ├── visualize.py           # Visualization tools
│   └── logger_config.py       # Logging configuration
└── data/
    ├── uploads/               # Temporary (auto-deleted every 15min)
    └── video_db/              # Permanent fingerprint storage
        ├── fingerprints/      # .npy arrays
        └── metadata.json      # Video metadata
```

## 🔧 Configuration

### App Settings (`app.py`)
```python
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max upload
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
CLEANUP_INTERVAL = 15 * 60  # 15 minutes
```

### Fingerprinting Parameters (`video_utils.py`)
```python
TARGET_FPS = 10              # Frame sampling rate
TARGET_SIZE = (320, 240)     # Standardized resolution
N_ROWS, M_COLS = 2, 4        # Grid dimensions (8 blocks)
```

### Automatic Cleanup

The system runs a background thread that:
- ✅ Deletes uploaded videos every **15 minutes**
- ✅ Preserves all fingerprints in the database
- ✅ Logs cleanup operations with file sizes
- ✅ Runs automatically on server start

**Note**: Videos in `./data/uploads/` are temporary. Fingerprints in `./data/video_db/` are permanent.


## 🎯 Use Cases

- **Content Protection**: Detect unauthorized uploads of copyrighted videos
- **Video Deduplication**: Find duplicate videos in large archives
- **Content Moderation**: Identify known prohibited content
- **Video Analytics**: Track video distribution across platforms
- **Clip Matching**: Find where a short clip appears in full-length videos
- **Quality-Independent Search**: Match videos despite compression or format changes

## 🛡️ Technical Advantages

### Why Gradient Orientation?
- **Robust to Compression**: Gradients capture structural information that survives compression
- **Illumination Invariant**: Orientation is less affected by brightness changes
- **Scale Invariant**: Resizing to 320×240 normalizes all videos
- **Fast Computation**: Sobel operators are highly optimized

### Why Grid Division?
- **Spatial Localization**: Captures "where" features are in the frame
- **Dimension Reduction**: 320×240 = 76,800 pixels → 8 features
- **Discriminative Power**: 8D vectors per frame provide good uniqueness

### Why 10 FPS?
- **Efficiency**: Most motion is captured at 10fps
- **Storage**: Reduces fingerprint size by 3-6× vs full frame rate
- **Speed**: Faster processing and searching


## 🙏 Acknowledgments

This implementation is based on the algorithm described in:

**"Robust Video Fingerprinting for Content-Based Video Identification"**

The fingerprinting technique uses gradient-based analysis and combinatorial hashing to create robust, compression-resistant video fingerprints. This approach enables efficient content identification even with degraded or low-quality video samples.

### Technologies Used
- **Framework**: Flask
- **Video Processing**: OpenCV
- **Numerical Computing**: NumPy
- **UI Design**: Inspired by Sonic Identify

---

*Identifying videos through gradient fingerprinting*
