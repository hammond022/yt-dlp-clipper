# yt-dlp-clipper

A command-line tool to **download YouTube videos**, **trim clips**, and **automatically generate & burn animated subtitles** using [Whisper AI](https://github.com/openai/whisper).  
Supports custom time ranges, video quality selection, and multiple subtitle languages.

---

## ✨ Features

- 📥 Download YouTube videos in 720p or 1080p
- ✂️ Trim clips to custom start/end times
- 📝 Auto-generate subtitles with Whisper AI (Filipino, English, Both, or Automatic)
- 🔥 Burn animated, styled subtitles directly into the video
- 🎚️ Choose to enable/disable subtitles per video
- 🗂️ Batch process multiple videos via a simple text file

---

## 🚀 Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/yt-dlp-captioned-clipper.git
   cd yt-dlp-captioned-clipper
   ```

2. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

   > **Note:** Requires Python 3.8+ and [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system PATH.

---

## ⚡ Usage

1. **Prepare your `video_links.txt` file:**

   Each line should follow this format:

   ```
   <YouTube URL> start=HH:MM:SS end=HH:MM:SS quality=720p|1080p subs=on|off lang=Filipino|English|Both|Automatic
   ```

   **Example:**

   ```
   https://www.youtube.com/watch?v=_WnwqsVPfiU&t start=00:03:17 end=00:07:17 quality=720p subs=off
   ```

2. **Run the program:**

   ```sh
   python main.py
   ```

   - Downloads will be saved in the `downloads/` folder.
   - Subtitled videos will have `_with_subs` in their filename.

---

## 🛠️ Example Workflow

1. Add your video links and options to `video_links.txt`.
2. Run the script.
3. Find your processed videos in the `downloads/` directory.

---

## 🏷️ Options Explained

| Option  | Description                                            | Example Value    |
| ------- | ------------------------------------------------------ | ---------------- |
| start   | Start time of the clip (optional)                      | `start=00:01:00` |
| end     | End time of the clip (optional)                        | `end=00:02:00`   |
| quality | Video quality                                          | `quality=720p`   |
| subs    | Enable or disable subtitles                            | `subs=on`        |
| lang    | Subtitle language (Filipino, English, Both, Automatic) | `lang=English`   |

---
❤H.
