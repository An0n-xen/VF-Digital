from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import logging
import time
import threading
from datetime import datetime
from werkzeug.utils import secure_filename
import numpy as np
from utils.database import VideoDatabase
from utils.video_utils import preprocess_video, extract_fingerprint
from utils.logger_config import setup_logger

# Setup comprehensive logging
logger = setup_logger(__name__, level=logging.INFO)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 150 * 1024 * 1024  # 500MB max file size
app.config["UPLOAD_FOLDER"] = "./data/uploads"
app.config["ALLOWED_EXTENSIONS"] = {"mp4", "avi", "mov", "mkv", "webm"}

# Create upload folder if it doesn't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize video database
logger.info("=" * 80)
logger.info("INITIALIZING FLASK APPLICATION")
logger.info("=" * 80)
db = VideoDatabase()
logger.info(f"Video database initialized with {len(db.metadata)} videos")


def cleanup_old_videos():
    """
    Background task that deletes uploaded videos every 15 minutes to save disk space.
    Fingerprints are preserved in the database.
    """
    while True:
        try:
            time.sleep(15 * 60)  # Wait 15 minutes

            upload_folder = app.config["UPLOAD_FOLDER"]
            if not os.path.exists(upload_folder):
                continue

            logger.info("=" * 80)
            logger.info("CLEANUP: Starting automatic video cleanup")
            logger.info("=" * 80)

            deleted_count = 0
            total_size = 0

            # Get all files in upload folder
            for filename in os.listdir(upload_folder):
                filepath = os.path.join(upload_folder, filename)

                # Skip directories and query files
                if os.path.isdir(filepath) or filename.startswith("query_"):
                    continue

                try:
                    # Get file size before deletion
                    file_size = os.path.getsize(filepath)
                    total_size += file_size

                    # Delete the file
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(
                        f"CLEANUP: Deleted {filename} ({file_size / (1024*1024):.2f} MB)"
                    )

                except Exception as e:
                    logger.error(f"CLEANUP: Error deleting {filename}: {str(e)}")

            if deleted_count > 0:
                logger.info(
                    f"CLEANUP: Deleted {deleted_count} video(s), freed {total_size / (1024*1024):.2f} MB"
                )
            else:
                logger.info("CLEANUP: No videos to delete")

            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"CLEANUP: Error in cleanup thread: {str(e)}")


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_videos, daemon=True)
cleanup_thread.start()
logger.info("CLEANUP: Background cleanup thread started (runs every 15 minutes)")


def allowed_file(filename):
    """Check if file extension is allowed"""
    logger.debug(f"Checking if file '{filename}' is allowed")
    result = (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )
    logger.debug(f"File '{filename}' allowed: {result}")
    return result


@app.route("/")
def index():
    """Render the main page"""
    logger.info("=" * 80)
    logger.info("ROUTE: / (Index page requested)")
    logger.info("=" * 80)
    return render_template("index.html")


@app.route("/api/database/status")
def database_status():
    """Get current database status"""
    logger.info("=" * 80)
    logger.info("ROUTE: /api/database/status")
    logger.info("=" * 80)

    logger.info("Fetching database status...")
    status = {"total_videos": len(db.metadata), "videos": []}

    for file_id, info in db.metadata.items():
        logger.debug(f"Processing video metadata: {info['name']}")
        status["videos"].append(
            {
                "id": file_id,
                "name": info["name"],
                "frames": info["frames"],
                "duration": info["duration_sec"],
            }
        )

    logger.info(f"Database status retrieved: {status['total_videos']} videos found")
    return jsonify(status)


@app.route("/api/upload", methods=["POST"])
def upload_video():
    """Handle video upload and fingerprinting"""
    logger.info("=" * 80)
    logger.info("ROUTE: /api/upload (POST)")
    logger.info("=" * 80)

    # Stage 1: Check if file is in request
    logger.info("[STAGE 1] Checking if file exists in request...")
    if "video" not in request.files:
        logger.error("[STAGE 1 FAILED] No video file in request")
        return jsonify({"success": False, "error": "No video file provided"}), 400

    file = request.files["video"]
    video_name = request.form.get("name", "")

    logger.info(f"[STAGE 1 COMPLETE] File received: {file.filename}")

    # Stage 2: Validate file
    logger.info("[STAGE 2] Validating file...")
    if file.filename == "":
        logger.error("[STAGE 2 FAILED] Empty filename")
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        logger.error(f"[STAGE 2 FAILED] Invalid file type: {file.filename}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Invalid file type. Allowed: mp4, avi, mov, mkv, webm",
                }
            ),
            400,
        )

    logger.info(f"[STAGE 2 COMPLETE] File validation passed")

    # Stage 3: Save uploaded file
    logger.info("[STAGE 3] Saving uploaded file...")
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    try:
        file.save(filepath)
        logger.info(f"[STAGE 3 COMPLETE] File saved to: {filepath}")
    except Exception as e:
        logger.error(f"[STAGE 3 FAILED] Error saving file: {str(e)}")
        return (
            jsonify({"success": False, "error": f"Failed to save file: {str(e)}"}),
            500,
        )

    # Stage 4: Add to database
    logger.info("[STAGE 4] Adding video to database...")
    try:
        display_name = video_name if video_name else filename
        logger.info(f"[STAGE 4] Processing video with name: '{display_name}'")

        db.add_video(filepath, display_name)

        logger.info(
            f"[STAGE 4 COMPLETE] Video '{display_name}' successfully added to database"
        )
        logger.info("=" * 80)
        logger.info(f"UPLOAD SUCCESS: {display_name}")
        logger.info("=" * 80)

        return jsonify(
            {
                "success": True,
                "message": f'Video "{display_name}" added successfully!',
                "video_name": display_name,
            }
        )

    except Exception as e:
        logger.error(f"[STAGE 4 FAILED] Error processing video: {str(e)}")
        logger.error("=" * 80)
        logger.error(f"UPLOAD FAILED: {str(e)}")
        logger.error("=" * 80)

        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up failed upload: {filepath}")

        return (
            jsonify({"success": False, "error": f"Failed to process video: {str(e)}"}),
            500,
        )


@app.route("/api/search", methods=["POST"])
def search_video():
    """Handle video search"""
    logger.info("=" * 80)
    logger.info("ROUTE: /api/search (POST)")
    logger.info("=" * 80)

    # Stage 1: Check if file is in request
    logger.info("[STAGE 1] Checking if query video exists in request...")
    if "query_video" not in request.files:
        logger.error("[STAGE 1 FAILED] No query video file in request")
        return jsonify({"success": False, "error": "No query video provided"}), 400

    file = request.files["query_video"]
    logger.info(f"[STAGE 1 COMPLETE] Query file received: {file.filename}")

    # Stage 2: Validate file
    logger.info("[STAGE 2] Validating query file...")
    if file.filename == "":
        logger.error("[STAGE 2 FAILED] Empty filename")
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        logger.error(f"[STAGE 2 FAILED] Invalid file type: {file.filename}")
        return jsonify({"success": False, "error": "Invalid file type"}), 400

    logger.info(f"[STAGE 2 COMPLETE] Query file validation passed")

    # Stage 3: Save query file temporarily
    logger.info("[STAGE 3] Saving query file temporarily...")
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"query_{filename}")

    try:
        file.save(filepath)
        logger.info(f"[STAGE 3 COMPLETE] Query file saved to: {filepath}")
    except Exception as e:
        logger.error(f"[STAGE 3 FAILED] Error saving query file: {str(e)}")
        return (
            jsonify({"success": False, "error": f"Failed to save file: {str(e)}"}),
            500,
        )

    try:
        # Stage 4: Preprocess query video
        logger.info("[STAGE 4] Preprocessing query video...")
        frames = preprocess_video(filepath)

        if frames is None or len(frames) == 0:
            logger.error("[STAGE 4 FAILED] Failed to preprocess query video")
            return (
                jsonify({"success": False, "error": "Failed to process query video"}),
                500,
            )

        logger.info(
            f"[STAGE 4 COMPLETE] Query video preprocessed: {len(frames)} frames"
        )

        # Stage 5: Extract fingerprints
        logger.info("[STAGE 5] Extracting fingerprints from query video...")
        query_fps = extract_fingerprint(frames)
        logger.info(f"[STAGE 5 COMPLETE] Extracted {len(query_fps)} fingerprints")

        # Stage 6: Search database
        logger.info("[STAGE 6] Searching database for matches...")
        threshold = float(request.form.get("threshold", 0.4))
        logger.info(f"[STAGE 6] Using threshold: {threshold}")

        result = db.search(query_fps, threshold=threshold)

        if result:
            logger.info(f"[STAGE 6 COMPLETE] MATCH FOUND!")
            logger.info(f"  - Video: {result['video']}")
            logger.info(f"  - Timestamp: {result['start_time']}s")
            logger.info(f"  - Confidence Score: {result['score']:.5f}")
            logger.info("=" * 80)
            logger.info(f"SEARCH SUCCESS: Match found - {result['video']}")
            logger.info("=" * 80)

            return jsonify(
                {
                    "success": True,
                    "match_found": True,
                    "result": {
                        "video_name": result["video"],
                        "timestamp": round(result["start_time"], 2),
                        "confidence_score": round(result["score"], 5),
                    },
                }
            )
        else:
            logger.info("[STAGE 6 COMPLETE] No match found in database")
            logger.info("=" * 80)
            logger.info("SEARCH COMPLETE: No match found")
            logger.info("=" * 80)

            return jsonify(
                {
                    "success": True,
                    "match_found": False,
                    "message": "No matching video found in database",
                }
            )

    except Exception as e:
        logger.error(f"[SEARCH FAILED] Error during search: {str(e)}")
        logger.error("=" * 80)
        logger.error(f"SEARCH ERROR: {str(e)}")
        logger.error("=" * 80)
        return jsonify({"success": False, "error": f"Search failed: {str(e)}"}), 500

    finally:
        # Clean up query file
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up query file: {filepath}")


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("STARTING FLASK SERVER")
    logger.info("Server will run on http://127.0.0.1:5000")
    logger.info("=" * 80)
    app.run(debug=True, host="0.0.0.0", port=5000)
