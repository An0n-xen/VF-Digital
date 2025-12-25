// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDatabaseStatus();
    initializeTabSwitching();
    initializeFileInputs();
    initializeThresholdSlider();
    initializeForms();
    initializeDragDrop();
});

// Tab Switching
function initializeTabSwitching() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            // Update active states
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(targetTab + 'Tab').classList.add('active');
            
            // Reset results and stages when switching tabs
            resetStages();
            hideResults();
        });
    });
}

// Load database status
function loadDatabaseStatus() {
    fetch('/api/database/status')
        .then(response => response.json())
        .then(data => {
            updateDatabaseStatus(data);
        })
        .catch(error => {
            document.getElementById('videoCount').textContent = 'Error loading';
        });
}

// Update database status display
function updateDatabaseStatus(data) {
    const count = data.total_videos;
    document.getElementById('videoCount').textContent = `${count} Video${count !== 1 ? 's' : ''} Indexed`;
    
    if (data.videos.length > 0) {
        displayVideoList(data.videos);
    }
}

// Display video list
function displayVideoList(videos) {
    const videoListSection = document.getElementById('videoListSection');
    const videoList = document.getElementById('videoList');
    
    let html = '';
    videos.forEach(video => {
        html += `
            <div class="video-item">
                <div class="video-item-name">${video.name}</div>
                <div class="video-item-details">
                    ${video.frames} frames • ${video.duration.toFixed(2)}s duration
                </div>
            </div>
        `;
    });
    
    videoList.innerHTML = html;
    videoListSection.style.display = 'block';
}

// Initialize file inputs
function initializeFileInputs() {
    const videoFileInput = document.getElementById('videoFile');
    const queryFileInput = document.getElementById('queryFile');
    const uploadDropZone = document.getElementById('uploadDropZone');
    const searchDropZone = document.getElementById('searchDropZone');
    
    uploadDropZone.addEventListener('click', () => videoFileInput.click());
    searchDropZone.addEventListener('click', () => queryFileInput.click());
    
    videoFileInput.addEventListener('change', function() {
        handleFileSelect(this, uploadDropZone);
    });
    
    queryFileInput.addEventListener('change', function() {
        handleFileSelect(this, searchDropZone);
    });
}

// Handle file selection
function handleFileSelect(input, dropZone) {
    if (input.files && input.files[0]) {
        const fileName = input.files[0].name;
        dropZone.classList.add('has-file');
        dropZone.querySelector('.upload-title').textContent = fileName;
        dropZone.querySelector('.upload-hint').textContent = 'File selected';
    }
}

// Initialize drag and drop
function initializeDragDrop() {
    const dropZones = document.querySelectorAll('.upload-area');
    
    dropZones.forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('drag-over');
        });
        
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                handleFileSelect(input, zone);
            }
        });
    });
}

// Initialize threshold slider
function initializeThresholdSlider() {
    const thresholdSlider = document.getElementById('threshold');
    const thresholdValue = document.getElementById('thresholdValue');
    
    thresholdSlider.addEventListener('input', function() {
        thresholdValue.textContent = this.value;
    });
}

// Initialize forms
function initializeForms() {
    const uploadForm = document.getElementById('uploadForm');
    const searchForm = document.getElementById('searchForm');
    
    uploadForm.addEventListener('submit', handleUpload);
    searchForm.addEventListener('submit', handleSearch);
}

// Stage management functions
function showStages() {
    const stageTracker = document.getElementById('stageTracker');
    stageTracker.style.display = 'block';
}

function resetStages() {
    const stageTracker = document.getElementById('stageTracker');
    stageTracker.style.display = 'none';
    
    const stages = document.querySelectorAll('.stage-item');
    stages.forEach(stage => {
        stage.classList.remove('active', 'completed', 'error');
        stage.querySelector('.stage-status').textContent = 'Waiting...';
    });
}

function updateStage(stageNumber, status, message) {
    const stage = document.querySelector(`.stage-item[data-stage="${stageNumber}"]`);
    if (!stage) return;
    
    // Remove all status classes
    stage.classList.remove('active', 'completed', 'error');
    
    // Add new status class
    stage.classList.add(status);
    
    // Update status text
    stage.querySelector('.stage-status').textContent = message;
}

function hideResults() {
    document.getElementById('uploadResult').style.display = 'none';
    document.getElementById('searchResult').style.display = 'none';
}

// Handle video upload
async function handleUpload(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadResult = document.getElementById('uploadResult');
    
    // Reset and show stages
    resetStages();
    hideResults();
    showStages();
    uploadBtn.disabled = true;
    
    const fileName = formData.get('video').name;
    const videoName = formData.get('name') || fileName;
    
    try {
        // Stage 1: File Validation
        updateStage(1, 'active', 'Validating file...');
        await sleep(300);
        
        if (!fileName) {
            updateStage(1, 'error', 'No file selected');
            throw new Error('No file selected');
        }
        
        updateStage(1, 'completed', 'File validated ✓');
        
        // Stage 2: Upload & Preprocessing
        updateStage(2, 'active', 'Uploading and preprocessing video...');
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!data.success) {
            updateStage(2, 'error', 'Upload failed');
            throw new Error(data.error);
        }
        
        updateStage(2, 'completed', 'Video preprocessed ✓');
        
        // Stage 3: Fingerprint Extraction
        updateStage(3, 'active', 'Extracting fingerprints...');
        await sleep(500);
        updateStage(3, 'completed', 'Fingerprints extracted ✓');
        
        // Stage 4: Database Storage
        updateStage(4, 'active', 'Saving to database...');
        await sleep(300);
        updateStage(4, 'completed', 'Saved to database ✓');
        
        // Show success result
        uploadResult.className = 'result-card success';
        uploadResult.innerHTML = `
            <div class="result-title">✓ SUCCESS</div>
            <p style="margin-top: 0.5rem;">${data.message}</p>
        `;
        uploadResult.style.display = 'block';
        
        // Reset form
        e.target.reset();
        resetFileInput('uploadDropZone', 'Upload Video File');
        
        // Reload database status
        setTimeout(() => {
            loadDatabaseStatus();
            resetStages();
        }, 2000);
        
    } catch (error) {
        uploadResult.className = 'result-card error';
        uploadResult.innerHTML = `
            <div class="result-title">✗ ERROR</div>
            <p style="margin-top: 0.5rem;">${error.message}</p>
        `;
        uploadResult.style.display = 'block';
    } finally {
        uploadBtn.disabled = false;
    }
}

// Handle video search
async function handleSearch(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const searchBtn = document.getElementById('searchBtn');
    const searchResult = document.getElementById('searchResult');
    
    // Reset and show stages
    resetStages();
    hideResults();
    showStages();
    searchBtn.disabled = true;
    
    const fileName = formData.get('query_video').name;
    const threshold = formData.get('threshold');
    
    try {
        // Stage 1: File Validation
        updateStage(1, 'active', 'Validating query video...');
        await sleep(300);
        
        if (!fileName) {
            updateStage(1, 'error', 'No file selected');
            throw new Error('No file selected');
        }
        
        updateStage(1, 'completed', 'Query validated ✓');
        
        // Stage 2: Preprocessing
        updateStage(2, 'active', 'Preprocessing query video...');
        
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!data.success) {
            updateStage(2, 'error', 'Processing failed');
            throw new Error(data.error);
        }
        
        updateStage(2, 'completed', 'Video preprocessed ✓');
        
        // Stage 3: Fingerprint Extraction
        updateStage(3, 'active', 'Extracting fingerprints...');
        await sleep(500);
        updateStage(3, 'completed', 'Fingerprints extracted ✓');
        
        // Stage 4: Database Search
        updateStage(4, 'active', 'Searching database...');
        await sleep(800);
        
        if (data.match_found) {
            updateStage(4, 'completed', `Match found: ${data.result.video_name} ✓`);
            
            searchResult.className = 'result-card success';
            searchResult.innerHTML = `
                <div class="result-title">✓ MATCH FOUND</div>
                <div class="result-details">
                    <div class="result-item">
                        <span class="result-label">Video Name</span>
                        <span class="result-value">${data.result.video_name}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Timestamp</span>
                        <span class="result-value">${data.result.timestamp}s</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Confidence</span>
                        <span class="result-value">${data.result.confidence_score}</span>
                    </div>
                </div>
            `;
        } else {
            updateStage(4, 'completed', 'No match found');
            
            searchResult.className = 'result-card info';
            searchResult.innerHTML = `
                <div class="result-title">NO MATCH FOUND</div>
                <p style="margin-top: 0.5rem;">The query video did not match any videos in the database.</p>
                <p style="margin-top: 0.5rem; font-size: 0.875rem; opacity: 0.8;">Try adjusting the threshold or uploading a different clip.</p>
            `;
        }
        
        searchResult.style.display = 'block';
        
        // Reset form
        e.target.reset();
        resetFileInput('searchDropZone', 'Upload Query Video');
        
        setTimeout(() => {
            resetStages();
        }, 3000);
        
    } catch (error) {
        searchResult.className = 'result-card error';
        searchResult.innerHTML = `
            <div class="result-title">✗ ERROR</div>
            <p style="margin-top: 0.5rem;">${error.message}</p>
        `;
        searchResult.style.display = 'block';
    } finally {
        searchBtn.disabled = false;
    }
}

// Helper functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function resetFileInput(zoneId, originalTitle) {
    const zone = document.getElementById(zoneId);
    zone.classList.remove('has-file');
    zone.querySelector('.upload-title').textContent = originalTitle;
    zone.querySelector('.upload-hint').textContent = 'Drop & Drop or Click to Browse';
}
