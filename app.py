import os
import shutil
from typing import Any, cast

import spotipy
import yt_dlp
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp.utils import DownloadError, download_range_func

# Load environment variables from .env file securely
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enables Cross-Origin Requests for the browser extension

DOWNLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "downloads"
)
MUSIC_FOLDER = os.path.join(DOWNLOAD_FOLDER, "music")
UNIVERSAL_FOLDER = os.path.join(DOWNLOAD_FOLDER, "universal")

for folder in [DOWNLOAD_FOLDER, MUSIC_FOLDER, UNIVERSAL_FOLDER]:
  os.makedirs(folder, exist_ok=True)

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID", "")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "")


def find_ffmpeg() -> str:
  """Automatically searches the system for ffmpeg.exe."""
  # 1. Check if already in system PATH
  found = shutil.which("ffmpeg")
  if found:
    return os.path.dirname(found)

  # 2. Check common manual paths
  common_paths = [
      r"C:\ffmpeg\bin",
      r"C:\Program Files\Gyan\FFmpeg\bin",
      r"C:\Program Files\FFmpeg\bin",
  ]
  for path in common_paths:
    if os.path.exists(os.path.join(path, "ffmpeg.exe")):
      return path

  # 3. Search WinGet packages directory dynamically
  winget_root = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
  if os.path.exists(winget_root):
    for root, dirs, files in os.walk(winget_root):
      if "ffmpeg.exe" in files:
        return root

  return ""


FFMPEG_DIR = find_ffmpeg()
if FFMPEG_DIR:
  print(f"[INFO] Successfully located FFmpeg at: {FFMPEG_DIR}")
else:
  print(
      "[WARNING] FFmpeg could not be automatically located. Ensure it is"
      " installed."
  )


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
  data = request.json or {}
  url = data.get("url")
  resolution = data.get("resolution")
  embed_cc = data.get("embed_cc", False)
  cc_lang = data.get("cc_lang", "en")

  if not url or not resolution:
    return jsonify({"error": "URL and Resolution are required"}), 400

  format_str = (
      f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"
  )
  output_template = os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")

  ydl_opts: dict[str, Any] = {
      "format": format_str,
      "outtmpl": output_template,
      "merge_output_format": "mp4",
      "quiet": True,
  }

  if FFMPEG_DIR and os.path.exists(FFMPEG_DIR):
    ydl_opts["ffmpeg_location"] = FFMPEG_DIR

  if embed_cc:
    ydl_opts.update({
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [cc_lang] if cc_lang != "all" else ["all"],
        "postprocessors": [{
            "key": "FFmpegEmbedSubtitle",
            "already_have_subtitle": False,
        }],
    })

  try:
    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
      info = ydl.extract_info(url, download=True)
      if not info:
        return jsonify({"error": "Failed to extract video info"}), 500
      filename = ydl.prepare_filename(info)
      filename = os.path.splitext(filename)[0] + ".mp4"

      return jsonify(
          {"message": "Download complete!", "filename": os.path.basename(filename)}
      )
  except Exception:
    app.logger.exception("Download failed")
    return jsonify({"error": "An unexpected error occurred during download."}), 500


@app.route("/download-universal", methods=["POST"])
def download_universal():
  data = request.json or {}
  url = str(data.get("url", "")).strip()
  media_type = str(data.get("media_type", "video"))
  start_time = str(data.get("start_time", "")).strip()
  end_time = str(data.get("end_time", "")).strip()
  embed_cc = bool(data.get("embed_cc", False))
  cc_lang = str(data.get("cc_lang", "en"))

  if not url:
    return jsonify({"error": "URL is required"}), 400

  output_template = os.path.join(
      UNIVERSAL_FOLDER, "%(extractor_key)s_%(title)s.%(ext)s"
  )

  ydl_opts: dict[str, Any] = {
      "outtmpl": output_template,
      "quiet": True,
      "no_warnings": True,
      "format": (
          "bestvideo+bestaudio/best"
          if media_type == "video"
          else "bestaudio/best"
      ),
      "merge_output_format": "mp4" if media_type == "video" else None,
  }

  if FFMPEG_DIR and os.path.exists(FFMPEG_DIR):
    ydl_opts["ffmpeg_location"] = FFMPEG_DIR

  if media_type == "audio_only":
    ydl_opts["postprocessors"] = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "320",
    }]
  elif embed_cc:
    ydl_opts.update({
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [cc_lang] if cc_lang != "all" else ["all"],
        "postprocessors": [{
            "key": "FFmpegEmbedSubtitle",
            "already_have_subtitle": False,
        }],
    })

  if start_time or end_time:
    start = start_time if start_time else "0"
    end = end_time if end_time else "inf"
    start_val = int(start) if start.isdigit() else start
    end_val = int(end) if end.isdigit() else end
    ydl_opts["download_ranges"] = download_range_func(
        [], [(int(start_val), int(end_val))]
    )
    ydl_opts["force_keyframes_at_cuts"] = True

  try:
    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
      info = ydl.extract_info(url, download=True)
      if not info:
        return jsonify({"error": "Failed to extract media info"}), 500

      info_dict = cast(dict[str, Any], info)
      entries = info_dict.get("entries")
      if entries:
        first_entry = next(iter(entries), None)
        if first_entry:
          info_dict = cast(dict[str, Any], first_entry)

      filename = ydl.prepare_filename(cast(Any, info_dict))
      ext = ".mp3" if media_type == "audio_only" else ".mp4"
      filename = os.path.splitext(filename)[0] + ext

      return jsonify({
          "message": "Download successful!",
          "site": info_dict.get("extractor_key", "Universal"),
          "title": info_dict.get("title", "Downloaded Media"),
          "filename": os.path.basename(filename),
      })
  except Exception:
    app.logger.exception("Universal download failed")
    return jsonify({"error": "An unexpected error occurred during universal download."}), 500


@app.route("/search", methods=["POST"])
def search_videos():
  data = request.json or {}
  query = str(data.get("query", "")).strip()
  max_results = int(data.get("limit", 10))
  sort_by = str(data.get("sort_by", "relevance"))
  min_res = str(data.get("min_res", "0"))

  if not query:
    return jsonify({"error": "Search query is required"}), 400

  search_prefix = f"ytsearch{max_results}:"
  if sort_by == "date":
    search_prefix = f"ytsearchdate{max_results}:"

  ydl_opts: dict[str, Any] = {
      "quiet": True,
      "extract_flat": True,
      "skip_download": True,
  }

  if FFMPEG_DIR and os.path.exists(FFMPEG_DIR):
    ydl_opts["ffmpeg_location"] = FFMPEG_DIR

  try:
    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
      search_results = ydl.extract_info(f"{search_prefix}{query}", download=False)
      if not search_results:
        return jsonify({"results": []})
      entries = search_results.get("entries", []) or []

    detailed_results = []
    min_res_int = int(min_res) if min_res.isdigit() else 0

    for entry in entries:
      if not entry:
        continue
      vid_id = entry.get("id")
      v_url = entry.get("url") or f"https://www.youtube.com/watch?v={vid_id}"

      try:
        detail_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        if FFMPEG_DIR and os.path.exists(FFMPEG_DIR):
          detail_opts["ffmpeg_location"] = FFMPEG_DIR

        with yt_dlp.YoutubeDL(cast(Any, detail_opts)) as ydl_detail:
          info = ydl_detail.extract_info(v_url, download=False)
          formats = (info.get("formats") or []) if info else []
          max_height = max(
              [f.get("height") or 0 for f in formats if f.get("height")],
              default=1080,
          )
      except (DownloadError, ValueError, TypeError, OSError):
        max_height = 1080

      if max_height >= min_res_int:
        thumb = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        res_label = f"{max_height}p"
        if max_height >= 2160:
          res_label = "4K UHD"
        elif max_height >= 4320:
          res_label = "8K UHD"

        detailed_results.append({
            "id": vid_id,
            "url": v_url,
            "title": entry.get("title", "Unknown Title"),
            "uploader": entry.get("uploader", "Unknown Uploader"),
            "duration": entry.get("duration_string", "N/A"),
            "views": entry.get("view_count", 0),
            "max_resolution": res_label,
            "max_height": max_height,
            "thumbnail": thumb,
        })

    if sort_by == "views":
      detailed_results.sort(key=lambda x: x.get("views") or 0, reverse=True)

    return jsonify({"results": detailed_results})
  except Exception:
    app.logger.exception("Search failed")
    return jsonify({"error": "An unexpected error occurred during search."}), 500


@app.route("/fetch-playlist", methods=["POST"])
def fetch_playlist():
  data = request.json or {}
  url = str(data.get("url", "")).strip()
  if not url:
    return jsonify({"error": "URL is required"}), 400

  if "music.youtube.com" in url:
    url = url.replace("music.youtube.com", "www.youtube.com")

  tracks = []
  try:
    if "spotify.com" in url:
      if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET:
        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET
            )
        )
        if "track" in url:
          track_id = url.split("track/")[1].split("?")[0]
          item = sp.track(track_id)
          if item:
            artists = item.get("artists", [{}])
            artist_name = (
                artists[0].get("name", "Unknown Artist")
                if artists
                else "Unknown Artist"
            )
            track_name = item.get("name", "Unknown Track")
            album = item.get("album", {})
            images = album.get("images", [])
            thumb = images[0].get("url") if images else ""
            tracks.append({
                "title": f"{artist_name} - {track_name}",
                "url": f"ytsearch1:{artist_name} - {track_name}",
                "thumbnail": thumb,
            })
        elif "playlist" in url:
          playlist_id = url.split("playlist/")[1].split("?")[0]
          results = sp.playlist_items(playlist_id)
          if results:
            for playlist_item in results.get("items", []):
              if playlist_item:
                track = playlist_item.get("track")
                if track:
                  artists = track.get("artists", [{}])
                  artist_name = (
                      artists[0].get("name", "Unknown Artist")
                      if artists
                      else "Unknown Artist"
                  )
                  track_name = track.get("name", "Unknown Track")
                  album = track.get("album", {})
                  images = album.get("images", [])
                  thumb = images[0].get("url") if images else ""
                  tracks.append({
                      "title": f"{artist_name} - {track_name}",
                      "url": f"ytsearch1:{artist_name} - {track_name}",
                      "thumbnail": thumb,
                  })
      else:
        tracks.append({"title": url, "url": url, "thumbnail": ""})
    else:
      ydl_opts: dict[str, Any] = {
          "quiet": True,
          "extract_flat": True,
          "skip_download": True,
      }
      if FFMPEG_DIR and os.path.exists(FFMPEG_DIR):
        ydl_opts["ffmpeg_location"] = FFMPEG_DIR

      with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
          return jsonify({"error": "Failed to extract playlist"}), 400

        info_dict = cast(dict[str, Any], info)
        if "entries" in info_dict:
          entries = info_dict.get("entries") or []
          for entry in entries:
            if entry:
              title = entry.get("title", "Unknown Track")
              vid_id = entry.get("id")
              e_url = entry.get("url")

              if e_url and not e_url.startswith("http"):
                e_url = f"https://www.youtube.com{e_url}"
              elif not e_url and vid_id:
                e_url = f"https://www.youtube.com/watch?v={vid_id}"

              thumb = entry.get("thumbnail") or (
                  entry.get("thumbnails", [{}])[0].get("url")
                  if entry.get("thumbnails")
                  else ""
              )
              if not thumb and vid_id:
                thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

              if e_url:
                tracks.append({
                    "title": title,
                    "url": e_url,
                    "thumbnail": thumb,
                })
        else:
          title = info_dict.get("title", "Unknown Track")
          thumb = info_dict.get("thumbnail", "")
          tracks.append({"title": title, "url": url, "thumbnail": thumb})

    return jsonify({"tracks": tracks})
  except Exception:
    app.logger.exception("Fetch playlist failed")
    return jsonify({"error": "Failed to fetch playlist items."}), 500


@app.route("/download-music", methods=["POST"])
def download_music():
  data = request.json or {}
  selected_tracks = data.get("tracks", [])
  audio_format = str(data.get("format", "mp3"))
  quality = str(data.get("quality", "320"))

  if not selected_tracks:
    return jsonify({"error": "No tracks selected for download"}), 400

  ydl_opts: dict[str, Any] = {
      "format": "bestaudio/best",
      "outtmpl": os.path.join(MUSIC_FOLDER, "%(title)s.%(ext)s"),
      "postprocessors": [{
          "key": "FFmpegExtractAudio",
          "preferredcodec": audio_format,
          "preferredquality": quality,
      }],
      "quiet": True,
      "ignoreerrors": True,
  }

  if FFMPEG_DIR and os.path.exists(FFMPEG_DIR):
    ydl_opts["ffmpeg_location"] = FFMPEG_DIR

  downloaded_files = []
  try:
    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
      for track in selected_tracks:
        target = track.get("url")
        if not target:
          continue
        try:
          info = ydl.extract_info(target, download=True)
          if not info:
            continue

          info_dict = cast(dict[str, Any], info)
          entries = info_dict.get("entries")
          if entries:
            for entry in entries:
              if entry:
                base_path = os.path.splitext(ydl.prepare_filename(entry))[0]
                fn = base_path + f".{audio_format}"
                if os.path.exists(fn):
                  downloaded_files.append(os.path.basename(fn))
          else:
            base_path = os.path.splitext(
                ydl.prepare_filename(cast(Any, info_dict))
            )[0]
            fn = base_path + f".{audio_format}"
            if os.path.exists(fn):
              downloaded_files.append(os.path.basename(fn))
        except (DownloadError, ValueError, TypeError, OSError) as track_err:
          app.logger.warning("Failed to download track %s: %s", target, track_err)
          continue

    if not downloaded_files:
      return jsonify({
          "error": "No files were successfully downloaded. Check server logs."
      }), 500

    return jsonify({
        "message": f"Successfully downloaded {len(downloaded_files)} track(s).",
        "files": downloaded_files,
    })
  except Exception as e:
    app.logger.exception("Music download batch failed")
    return jsonify({"error": f"Server Exception: {e!s}"}), 500


@app.route("/files/<path:filename>")
def serve_file(filename):
  return send_file(
      os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True
  )


@app.route("/files/music/<path:filename>")
def serve_music_file(filename):
  return send_file(os.path.join(MUSIC_FOLDER, filename), as_attachment=True)


@app.route("/files/universal/<path:filename>")
def serve_universal_file(filename):
  return send_file(os.path.join(UNIVERSAL_FOLDER, filename), as_attachment=True)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", "5001"))
  app.run(host="0.0.0.0", port=port)