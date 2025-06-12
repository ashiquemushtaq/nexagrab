// script.js

// Get references to HTML elements by their IDs
const videoLinkInput = document.getElementById('videoLinkInput');
const getVideoInfoButton = document.getElementById('getVideoInfoButton');
const statusMessage = document.getElementById('statusMessage');
const qualitySelectionArea = document.getElementById('qualitySelectionArea');
const qualitySelect = document.getElementById('qualitySelect');
const downloadSelectedButton = document.getElementById('downloadSelectedButton');
const finalDownloadLinkArea = document.getElementById('finalDownloadLinkArea'); // This area will remain hidden
const finalDownloadLink = document.getElementById('finalDownloadLink'); // This link won't be used at all

let currentVideoQualities = []; // Store qualities received from the backend

/**
 * Clears any existing status messages and hides all dynamic areas.
 * This function is called when the user starts typing in the input field
 * or when a new request begins.
 */
function clearStatus() {
    statusMessage.textContent = ''; // Clear the text content of the status message
    qualitySelectionArea.classList.add('hidden'); // Hide the quality selection area
    finalDownloadLinkArea.classList.add('hidden'); // Ensure final download link area is hidden
    // Reset quality select options
    qualitySelect.innerHTML = '<option value="" disabled selected>Loading qualities...</option>';
}

// Event listener for the "Get Video Info" button
getVideoInfoButton.addEventListener('click', async () => {
    const videoUrl = videoLinkInput.value.trim();

    if (!videoUrl) {
        statusMessage.className = 'mt-6 text-lg text-red-600 font-medium';
        statusMessage.textContent = 'Please enter a video link.';
        return;
    }

    clearStatus(); // Clear previous states
    statusMessage.className = 'mt-6 text-lg text-blue-600 font-medium animate-pulse';
    statusMessage.textContent = 'Fetching video information and available qualities...';
    getVideoInfoButton.disabled = true; // Disable button to prevent multiple clicks

    try {
        // Request available qualities from the backend
        const response = await fetch('http://127.0.0.1:5000/api/get-video-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: videoUrl })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }

        if (data.qualities && data.qualities.length > 0) {
            currentVideoQualities = data.qualities; // Store the fetched qualities
            populateQualitySelect(currentVideoQualities); // Populate the dropdown
            qualitySelectionArea.classList.remove('hidden'); // Show the quality selection area
            statusMessage.className = 'mt-6 text-lg text-green-600 font-medium';
            statusMessage.textContent = 'Video information fetched. Select a quality and click Download.';
            // Update button text to reflect direct download
            downloadSelectedButton.textContent = 'Download Selected';
        } else {
            statusMessage.className = 'mt-6 text-lg text-red-600 font-medium';
            statusMessage.textContent = 'No downloadable qualities found for this video.';
        }
    } catch (error) {
        console.error('Error fetching video info:', error);
        statusMessage.className = 'mt-6 text-lg text-red-600 font-medium';
        statusMessage.textContent = `Error: ${error.message}. Please check the link or try again.`;
    } finally {
        getVideoInfoButton.disabled = false; // Re-enable the button
    }
});

/**
 * Populates the quality dropdown with options.
 * @param {Array} qualities - An array of quality objects from the backend.
 */
function populateQualitySelect(qualities) {
    qualitySelect.innerHTML = ''; // Clear existing options
    qualities.forEach(q => {
        const option = document.createElement('option');
        option.value = q.format_id; // Value will be yt-dlp's format ID
        option.textContent = q.label; // Display text (e.g., "720p MP4 (Video + Audio)")
        if (q.is_default) { // Optionally pre-select a 'best' quality if backend indicates it
            option.selected = true;
        }
        qualitySelect.appendChild(option);
    });
}

// Event listener for the "Download Selected Quality" button
downloadSelectedButton.addEventListener('click', () => { // Removed async
    const videoUrl = videoLinkInput.value.trim();
    const selectedFormatId = qualitySelect.value;

    if (!videoUrl || !selectedFormatId) {
        statusMessage.className = 'mt-6 text-lg text-red-600 font-medium';
        statusMessage.textContent = 'Please get video info first and select a quality.';
        return;
    }

    statusMessage.className = 'mt-6 text-lg text-blue-600 font-medium animate-pulse';
    statusMessage.textContent = 'Initiating download...'; // Simplified message
    downloadSelectedButton.disabled = true; // Disable button immediately

    // Get a filename hint for the backend (though backend determines final name)
    const selectedQuality = currentVideoQualities.find(q => q.format_id === selectedFormatId);
    let filenameHint = selectedQuality ? selectedQuality.title : 'video_download';
    if (selectedQuality && selectedQuality.ext) {
        filenameHint += `.${selectedQuality.ext}`;
    } else {
        filenameHint += '.mp4'; // Default to mp4 if extension is unknown
    }

    // --- MODIFIED: Redirect to the backend endpoint to trigger download ---
    // Create a URLSearchParams object to safely encode URL parameters
    const params = new URLSearchParams();
    params.append('url', videoUrl);
    params.append('format_id', selectedFormatId);
    params.append('filename_hint', filenameHint);

    // Construct the full URL to the backend endpoint
    const downloadEndpoint = `http://127.0.0.1:5000/api/get-download-link?${params.toString()}`;
    
    // Redirect the browser to this URL. The backend will respond with the file
    // and the Content-Disposition: attachment header will trigger the download.
    window.location.href = downloadEndpoint;

    // Reset button state after a short delay, as the page might not reload
    // immediately or if the download is very fast.
    setTimeout(() => {
        downloadSelectedButton.disabled = false;
        statusMessage.textContent = ''; // Clear message after download attempt
    }, 3000); // Give the browser 3 seconds to initiate the download
    // --- END MODIFIED ---
});