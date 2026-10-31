# Lucid - Universal Media Workspace

A professional, Miter-styled media downloader and workspace web application inspired by Lucidchart's clean interface design. Built with Flask, `yt-dlp`, `spotipy`, and FFmpeg, it supports multi-platform media downloads, YouTube 8K exploring, and real-time batch music/playlist downloading with automated album art extraction and live progress tracking.

🌐 **Live Application:** [https://flask-youtube-downloader-o005.onrender.com](https://flask-youtube-downloader-o005.onrender.com)

---

## Features

* **Lucidchart-Inspired Workspace:** Sharp-edged (mitered) aesthetic with zero curved borders, custom Dark/Light mode switching, inline SVGs, and an Ultramarine / Off-Cream design system.
* **Music & Playlist Workspace:** Extract tracklists from Spotify or YouTube playlists, preview album art, select individual tracks, and batch download with automated real-time progress bars per track.
* **Universal Media Downloader:** Paste links from TikTok, Instagram, X/Twitter, YouTube, and over 1,000+ supported sites with custom start/end clipping and subtitle (CC) embedding.
* **YouTube 8K Explorer:** Search videos, filter by resolution (up to 8K Ultra HD) and view count, and download directly.

---

## Tech Stack

* **Backend:** Python, Flask, `yt-dlp`, `spotipy`, Gunicorn
* **Media Processing:** FFmpeg / FFprobe (Dynamic automated system path finder)
* **Frontend:** HTML5, CSS3 (Custom Grid Workspace Layout), Vanilla JavaScript, SVG Icons

---

## Complete Local Installation & Setup

Follow these steps to set up, configure, and run the project locally on your machine:

### 1. Prerequisites
Ensure you have the following installed on your system:
* **Python** (v3.10 or higher recommended)
* **Git**
* **FFmpeg** (Required for media merging and audio conversion. On Windows, you can install it via PowerShell using: `winget install Gyan.FFmpeg`)

### 2. Clone the Repository
Open your terminal and clone your repository to your local directory:
```bash
git clone https://github.com/obedjoshua/flask-youtube-downloader.git
cd flask-youtube-downloader
```

### 3. Create and Activate a Virtual Environment
Set up an isolated Python environment for the project:

* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate
  ```
* **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 4. Install Project Dependencies
Install all required Python packages using pip:
```bash
pip install -r requirements.txt
```

### 5. Configure Optional Spotify API Credentials (Recommended for Spotify Playlists)
If you plan to fetch Spotify playlist tracklists, set up your Spotify Developer credentials as environment variables before starting the server:

* **Windows (PowerShell):**
  ```powershell
  $env:SPOTIPY_CLIENT_ID="your_spotify_client_id"
  $env:SPOTIPY_CLIENT_SECRET="your_spotify_client_secret"
  ```
* **macOS / Linux:**
  ```bash
  export SPOTIPY_CLIENT_ID="your_spotify_client_id"
  export SPOTIPY_CLIENT_SECRET="your_spotify_client_secret"
  ```
*(Note: If left unconfigured, the app will still function fully for YouTube links, video searches, and universal platform links).*

### 6. Run the Flask Development Server
Start your application locally:
```bash
python app.py
```

### 7. Access the App
Open your web browser and navigate to:
```text
http://127.0.0.1:5001
```
