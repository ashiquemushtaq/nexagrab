# NexaGrab

A universal web application designed to help users download videos from various social media platforms like YouTube, TikTok, Instagram, and more, by simply pasting a video link.

## 🌟 Features

* **Multi-Platform Support:** Download videos from a wide range of social media platforms (powered by `yt-dlp`).

* **Quality Selection:** Choose from available video qualities before downloading.

* **Direct Download:** Initiates a direct file download to your device.

* **Server-Side Processing:** Handles complex video stream merging (video + audio) on the backend using `ffmpeg`.

* **Temporary File Cleanup:** Automatically deletes temporary video files from the server after successful transfer to the client.

* **Responsive UI:** A clean and responsive user interface built with HTML and Tailwind CSS.

## 🛠️ Technologies Used

* **Frontend:**

    * HTML5

    * CSS (Tailwind CSS)

    * JavaScript (Vanilla JS)

* **Backend:**

    * Python 3.x

    * Flask (Web Framework)

    * Flask-CORS (for handling Cross-Origin requests)

    * `yt-dlp` (Python library for video downloading)

    * `ffmpeg` (External tool for video/audio merging - **Crucial!**)

## 🚀 Getting Started (Local Setup)

Follow these steps to get NexaGrab running on your local machine for development and testing.

### Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/).

* **`ffmpeg`**: `yt-dlp` relies on `ffmpeg` for merging video and audio streams.

    * **Windows:** Download a build from [ffmpeg.org/download.html](https://ffmpeg.ffmpeg.org/download.html) (e.g., a `Gyan` or `BtbN` build). Extract it and **add the path to its `bin` folder to your system's PATH environment variable**.

    * **macOS (using Homebrew):** `brew install ffmpeg`

    * **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install ffmpeg`

    * **Verify installation:** Open a new terminal and run `ffmpeg -version`.

### Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/yourusername/nexagrab.git](https://github.com/yourusername/nexagrab.git)
    cd nexagrab

    ```

    *(Remember to replace `yourusername` with your actual GitHub username if you cloned your own fork.)*

2.  **Create a Python Virtual Environment:**

    ```bash
    python -m venv venv

    ```

3.  **Activate the Virtual Environment:**

    * **macOS / Linux:**

        ```bash
        source venv/bin/activate

        ```

    * **Windows (Command Prompt)::**

        ```cmd
        venv\Scripts\activate.bat

        ```

    * **Windows (PowerShell):**

        ```powershell
        venv\Scripts\Activate.ps1

        ```

4.  **Install Python Dependencies:**

    ```bash
    pip install Flask yt-dlp Flask-CORS

    ```

5.  **Configure `ffmpeg` in `app.py`:**
    Open `app.py` in your text editor. Find the line `FFMPEG_LOCATION = r'C:\ffmpeg\ffmpeg-2025-06-08-git-5fea5e3e11-full_build\bin\ffmpeg.exe'` (or similar).
    **Replace the path with the absolute path to your `ffmpeg.exe`** (or `ffmpeg` binary on Linux/macOS). For example, on Linux it might be `/usr/bin/ffmpeg`.

    *Example for `app.py` on Linux/macOS:*

    ```python
    FFMPEG_LOCATION = '/usr/bin/ffmpeg' # Or '/usr/local/bin/ffmpeg'

    ```

### Running the Application

1.  **Start the Flask Backend Server:**
    Make sure your virtual environment is active (from step 3 above).

    ```bash
    python app.py

    ```

    You should see output indicating that the Flask server is running on `http://127.0.0.1:5000`. Keep this terminal window open.

2.  **Open the Frontend in Your Browser:**
    Navigate to the `nexagrab` directory in your file explorer. Double-click on `index.html` to open it in your web browser. Alternatively, you can open your browser and type `file:///path/to/your/nexagrab/index.html` (replace `path/to/your/nexagrab` with the actual path).

## 💡 Usage

1.  **Paste Video Link:** Enter the URL of the video you wish to download into the input field.

2.  **Get Video Info:** Click the "Get Video Info" button. The application will fetch available qualities from the backend.

3.  **Select Quality:** Once qualities are listed, choose your desired video resolution/format from the dropdown.

4.  **Download Selected:** Click the "Download Selected" button. The video will be downloaded directly to your browser's default download location.

## ⚠️ Important Notes

* **`ffmpeg`:** Ensure `ffmpeg` is correctly installed and its path is configured in `app.py`. Without it, video/audio merging will fail.

* **Temporary Files:** Videos are temporarily downloaded to the `temp_downloads` folder on your server before being streamed to the client. These files are automatically cleaned up after a short delay (with retries) to account for browser file locks.

* **Legal Disclaimer:** Be aware of the terms of service of the platforms you download from. Downloading copyrighted content without permission may have legal implications. This application is provided for educational and personal use in understanding web development and video extraction technologies.

* **Production Deployment:** This setup is for local development. For a public deployment, you would need:

    * A production-ready WSGI server (e.g., Gunicorn/uWSGI).

    * A web server (e.g., Nginx/Apache) for serving static files and acting as a reverse proxy.

    * HTTPS/SSL certificate (e.g., via Certbot).

    * Considerations for server security, scalability, and robust error logging.

## 🤝 Contributing

Feel free to fork this repository, submit pull requests, or open issues if you find bugs or have suggestions for improvements!
