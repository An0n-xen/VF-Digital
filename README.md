# VF-Digital - Video Fingerprinting System

A powerful video fingerprinting and recognition system with a modern web interface built using Flask.

## 🌟 Features

- **Video Fingerprinting**: Upload videos to create unique fingerprints stored in a searchable database
- **Content Matching**: Search for video clips and find matches with timestamp accuracy
- **Modern Web UI**: Beautiful dark-mode interface with real-time feedback
- **Comprehensive Logging**: Stage-by-stage logging for every operation
- **Real-time Progress**: Live updates during video processing and searching

## 🚀 Quick Start

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## 📖 How It Works

### Video Fingerprinting Process

1. **Preprocessing**: Videos are converted to grayscale and resized to 320x240
2. **Frame Sampling**: Frames are extracted at 10 FPS for efficiency
3. **Fingerprint Extraction**: Each frame is divided into an 8-block grid (2x4)
4. **Gradient Analysis**: Sobel operators calculate gradients for each block
5. **Centroid Calculation**: The orientation centroid becomes the fingerprint
6. **Storage**: Fingerprints are saved as compressed numpy arrays

### Search Algorithm

1. Query video is processed using the same pipeline
2. Sliding window search across all videos in database
3. Euclidean distance calculates similarity scores
4. Best match below threshold is returned with timestamp

## 🎨 User Interface

The web interface includes:

- **Database Status Dashboard**: View all videos in your database
- **Upload Section**: Add new videos with drag-and-drop
- **Search Section**: Upload query clips to find matches
- **Activity Logs**: Real-time logging of all operations
- **Results Display**: Beautiful cards showing match results

## 📊 API Endpoints

### `GET /api/database/status`
Returns database statistics and video list

### `POST /api/upload`
Upload a video to the database
- **Form Data**: 
  - `video`: Video file
  - `name`: Optional custom name

### `POST /api/search`
Search for a video clip
- **Form Data**:
  - `query_video`: Query video file
  - `threshold`: Matching threshold (default: 0.4)

## 🔧 Configuration

Edit `app.py` to customize:
- `MAX_CONTENT_LENGTH`: Maximum upload file size (default: 500MB)
- `ALLOWED_EXTENSIONS`: Supported video formats
- `UPLOAD_FOLDER`: Directory for uploaded files

## 📁 Project Structure

```
VF-Digital/
├── app.py                    # Flask web application
├── main.py                   # CLI entry point
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html           # Web UI template
├── static/
│   ├── style.css            # UI styling
│   └── script.js            # Client-side logic
├── utils/
│   ├── database.py          # Database operations
│   ├── video_utils.py       # Video processing
│   ├── visualize.py         # Visualization tools
│   └── logger_config.py     # Logging configuration
├── uploads/                 # Uploaded video files
└── video_db/                # Fingerprint database
    ├── fingerprints/        # Fingerprint .npy files
    └── metadata.json        # Video metadata
```

## 🎯 Use Cases

- **Content Protection**: Detect unauthorized use of copyrighted videos
- **Video Deduplication**: Find duplicate or similar videos in large collections
- **Content Moderation**: Identify known inappropriate content
- **Video Analytics**: Track video distribution and usage
- **Research**: Study video similarity and matching algorithms

## 🛡️ Technical Details

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Video Processing**: OpenCV
- **Storage**: NumPy compressed arrays
- **Logging**: Colorlog with custom configuration

## 📝 Logging

The system logs every stage of operation:

**Upload Process:**
- Stage 1: File validation
- Stage 2: File type verification
- Stage 3: File storage
- Stage 4: Database processing

**Search Process:**
- Stage 1: Query validation
- Stage 2: File type verification
- Stage 3: Temporary storage
- Stage 4: Video preprocessing
- Stage 5: Fingerprint extraction
- Stage 6: Database search

Logs appear in both the console and the web UI's activity log section.

## 🎨 UI Features

- **Dark Mode Theme**: Easy on the eyes with purple-blue gradients
- **Responsive Design**: Works on desktop and mobile
- **Smooth Animations**: Micro-interactions enhance user experience
- **Progress Indicators**: Visual feedback during processing
- **Color-Coded Results**: Green for success, red for errors, blue for info
- **Auto-Scroll Logs**: Latest activities always visible

## 🔍 Example Usage

1. **Add a video to database:**
   - Click "Browse" in the upload section
   - Select `movie.mp4`
   - Enter name "My Movie"
   - Click "Add to Database"
   - Wait for success message

2. **Search for a clip:**
   - Click "Browse" in the search section
   - Select a short clip from the same movie
   - Adjust threshold if needed (lower = stricter)
   - Click "Search Database"
   - View match results with timestamp

## 🤝 Contributing

This is a personal project for video fingerprinting research and development.

## 📄 License

MIT License - Feel free to use and modify

## 🙏 Acknowledgments

Built with modern web technologies and computer vision algorithms for efficient video content matching.

---

**Made with ❤️ for VF-Digital**
