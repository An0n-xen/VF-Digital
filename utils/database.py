import os
import json
import uuid
import time
import logging
import numpy as np
from utils.video_utils import preprocess_video, extract_fingerprint
from utils.logger_config import setup_logger

logger = setup_logger(__name__, level=logging.INFO)


class VideoDatabase:
    def __init__(self, db_folder="./data/video_db"):
        self.db_folder = db_folder
        self.fp_folder = os.path.join(db_folder, "fingerprints")
        self.meta_path = os.path.join(db_folder, "metadata.json")

        # Create folders if they don't exist
        os.makedirs(self.fp_folder, exist_ok=True)

        # Load or Init Metadata
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def add_video(self, video_path, video_name=None):
        """Processes a video and saves its fingerprint to disk."""
        if video_name is None:
            video_name = os.path.basename(video_path)

        logger.info(f"Processing: {video_name}...")

        # 1. Process

        logger.info(f"[+] {"---" * 10} PROCESSING VIDEO {"---" * 10} [+]")
        frames = preprocess_video(video_path)
        if frames is None or len(frames) == 0:
            logger.error("Failed to process video.")
            return

        # 2. Extract
        logger.info(f"[+] {"---" * 10} EXTRACTING FINGERPRINTS {"---" * 10} [+]")
        fps = extract_fingerprint(frames)

        # 3. Save to Disk (Using Compressed Numpy Format)
        # Generate a unique ID for the file
        logger.info(f"[+] {"---" * 10} SAVING FINGERPRINTS {"---" * 10} [+]")
        file_id = str(uuid.uuid4())
        save_path = os.path.join(self.fp_folder, f"{file_id}.npy")

        np.save(save_path, fps)

        # 4. Update Metadata
        self.metadata[file_id] = {
            "name": video_name,
            "original_path": video_path,
            "frames": len(fps),
            "duration_sec": len(fps) / 10.0,  # Assuming 10fps
        }

        self._save_metadata()
        logger.info(f"Success! Saved {len(fps)} fingerprints to {save_path}")

    def search(self, query_fingerprints, threshold=0.4):
        """Scans ALL videos in the DB for a match."""
        logger.info(f"Searching {len(self.metadata)} videos...")
        start_time = time.time()

        best_match = None
        lowest_score = float("inf")

        K = len(query_fingerprints)

        # Iterate over every video in the database
        for file_id, info in self.metadata.items():
            file_path = os.path.join(self.fp_folder, f"{file_id}.npy")

            # MEMORY MAPPING:
            db_fps = np.load(file_path, mmap_mode="r")

            if len(db_fps) < K:
                continue

            # Sliding window search on this specific video
            # (Simplified Linear Scan)
            for i in range(len(db_fps) - K + 1):
                window = db_fps[i : i + K]

                # Fast Euclidean Distance
                diff = window - query_fingerprints
                score = np.mean(diff**2)

                if score < lowest_score:
                    lowest_score = score
                    best_match = {
                        "video": info["name"],
                        "start_time": i / 10.0,  # convert frame index to seconds
                        "score": score,
                    }

                    # Optimization: If we find a "perfect" match, stop early
                    if score < 0.01:
                        break

            # If we found a perfect match in this video, stop searching other videos
            if lowest_score < 0.01:
                break

        elapsed = time.time() - start_time
        logger.info(f"Search finished in {elapsed:.2f}s")

        if best_match and best_match["score"] < threshold:
            return best_match
        else:
            return None

    def _save_metadata(self):
        with open(self.meta_path, "w") as f:
            json.dump(self.metadata, f, indent=4)


if __name__ == "__main__":
    db = VideoDatabase()

    # 1. Add Videos (Do this once)
    logger.info("Adding videos to database")
    db.add_video("movies/matrix.mp4", "The Matrix")
    db.add_video("movies/shrek.mp4", "Shrek")

    # 2. Search (Simulated)
    logger.info("Searching for videos")
    if len(db.metadata) > 0:
        # Pick the first file in DB to test
        test_id = list(db.metadata.keys())[0]
        test_path = os.path.join(db.fp_folder, f"{test_id}.npy")

        # Load it and cut a 10s clip (Frames 50-150)
        full_fps = np.load(test_path)
        query_clip = full_fps[50:150]

        logger.info("Running test search")
        result = db.search(query_clip)

        if result:
            logger.info(f">> MATCH FOUND: {result['video']}")
            logger.info(f">> Timestamp: {result['start_time']} seconds")
            logger.info(f">> Confidence Score: {result['score']:.5f}")
        else:
            logger.info("No match found.")
