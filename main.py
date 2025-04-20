from yt_dlp import YoutubeDL
import sys
import whisper
import os
import subprocess
import tempfile
import shutil
import re

def parse_video_line(line):
    # Example: url start=00:00:05 end=00:00:15 quality=720p subs=on lang=English
    parts = line.strip().split()
    url = parts[0]
    opts = {
        "url": url,
        "start": None,
        "end": None,
        "quality": "1080p",
        "subs": "on",
        "lang": "Automatic"
    }
    for part in parts[1:]:
        if part.startswith("start="):
            opts["start"] = part.split("=", 1)[1]
        elif part.startswith("end="):
            opts["end"] = part.split("=", 1)[1]
        elif part.startswith("quality="):
            q = part.split("=", 1)[1]
            if q in ("720p", "1080p"):
                opts["quality"] = q
        elif part.startswith("subs="):
            s = part.split("=", 1)[1].lower()
            if s in ("on", "off"):
                opts["subs"] = s
        elif part.startswith("lang="):
            l = part.split("=", 1)[1]
            if l in ("Filipino", "English", "Both", "Automatic"):
                opts["lang"] = l
    return opts

def read_urls(filename):
    try:
        with open(filename, 'r') as file:
            return [parse_video_line(line) for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

def generate_srt_file(video_path, lang="Automatic"):
    try:
        print(f"Generating captions... (lang={lang})")
        # Map lang to whisper model options
        model = whisper.load_model("base")
        options = {}
        if lang == "Filipino":
            options["language"] = "Filipino"
        elif lang == "English":
            options["language"] = "en"
        elif lang == "Both":
            options["task"] = "translate"
            options["language"] = "en"
        # Automatic: don't set language
        result = model.transcribe(video_path, **options)
        temp_srt = tempfile.NamedTemporaryFile(suffix='.srt', delete=False, mode='w', encoding='utf-8')
        for i, segment in enumerate(result["segments"], start=1):
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            text = segment["text"].strip()
            temp_srt.write(f"{i}\n")
            temp_srt.write(f"{start_time} --> {end_time}\n")
            temp_srt.write(f"{text}\n\n")
        temp_srt.close()
        return temp_srt.name
    except Exception as e:
        print(f"Error generating captions: {str(e)}")
        return None

def convert_srt_to_ass(srt_path):
    ass_path = os.path.splitext(srt_path)[0] + ".ass"
    cmd = [
        "ffmpeg",
        "-y",
        "-i", srt_path,
        ass_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return ass_path
    except subprocess.CalledProcessError as e:
        print(f"Error converting SRT to ASS: {e.stderr.decode(errors='ignore') if e.stderr else str(e)}")
        return None

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{msecs:03d}"

def get_video_resolution(video_path):
    """Return (width, height) of the video using ffprobe."""
    import json
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        width = info['streams'][0]['width']
        height = info['streams'][0]['height']
        return width, height
    except Exception as e:
        print(f"Could not get video resolution: {e}")
        return None, None

def enhance_ass_style(ass_path):
    """Modify the ASS file to use bold, larger font and pop-in animation."""
    try:
        with open(ass_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = []
        style_modified = False
        for line in lines:
            if line.startswith("Style:"):
                # Example: Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2.0,2.0,2,30,30,10,1
                parts = line.strip().split(",")
                # Font name, size, colors, bold, etc.
                parts[1] = "Arial Black"  # Bolder font
                parts[2] = "24"           # Larger font size
                parts[3] = "&H0000FFFF"   # Yellow text
                parts[4] = "&H00000000"   # Black border
                parts[5] = "&H64000000"   # Shadow
                parts[7] = "1"            # Bold
                parts[8] = "0"            # Italic
                parts[15] = "3.0"         # Border width
                line = ",".join(parts) + "\n"
                style_modified = True
            new_lines.append(line)
        # Add pop-in animation to each Dialogue line
        for i, line in enumerate(new_lines):
            if line.startswith("Dialogue:"):
                # Insert ASS override tags for pop-in: \t for scale, \fad for fade-in
                # Example: {\fad(200,0)\t(0,200,\fscx120\fscy120)\t(200,400,\fscx100\fscy100)}
                # This will scale from 120% to 100% over 200ms, with a 200ms fade-in
                if "{" in line:
                    line = line.replace("{", "{\\fad(200,0)\\t(0,200,\\fscx120\\fscy120)\\t(200,400,\\fscx100\\fscy100)", 1)
                else:
                    parts = line.split(",", 9)
                    if len(parts) > 9:
                        text = parts[9]
                        text = "{\\fad(200,0)\\t(0,200,\\fscx120\\fscy120)\\t(200,400,\\fscx100\\fscy100)}" + text
                        parts[9] = text
                        line = ",".join(parts)
                new_lines[i] = line
        if style_modified:
            with open(ass_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
    except Exception as e:
        print(f"Error enhancing ASS style: {e}")

def burn_subtitles(video_path, srt_path):
    try:
        print("Burning subtitles into video...")
        output_path = os.path.splitext(video_path)[0] + "_with_subs.mp4"
        video_path = os.path.abspath(video_path)
        srt_path = os.path.abspath(srt_path)
        output_path = os.path.abspath(output_path)
        ass_path = convert_srt_to_ass(srt_path)
        if not ass_path or not os.path.exists(ass_path):
            print("Failed to convert SRT to ASS. Cannot burn subtitles.")
            return None

        # Enhance subtitle style and animation
        enhance_ass_style(ass_path)

        # Fallback for __file__ if running interactively
        try:
            script_dir = os.path.dirname(__file__)
        except NameError:
            script_dir = os.getcwd()
        safe_ass_path = os.path.join(script_dir, "temp_subs.ass")
        shutil.copyfile(ass_path, safe_ass_path)
        # ffmpeg on Windows needs forward slashes and double escaping for colons
        safe_ass_path_ffmpeg = safe_ass_path.replace("\\", "/").replace(":", "\\:")

        # --- Crop to 4:5 aspect ratio (center crop) ---
        width, height = get_video_resolution(video_path)
        if width is None or height is None:
            print("Could not determine video resolution, skipping crop.")
            crop_filter = ""
        else:
            # 4:5 aspect ratio: new_height = width * 5 / 4, or new_width = height * 4 / 5
            target_ratio = 4 / 5
            video_ratio = width / height
            if video_ratio > target_ratio:
                # Video is too wide, crop width
                crop_w = int(height * target_ratio)
                crop_h = height
                crop_x = int((width - crop_w) / 2)
                crop_y = 0
            else:
                # Video is too tall, crop height
                crop_w = width
                crop_h = int(width / target_ratio)
                crop_x = 0
                crop_y = int((height - crop_h) / 2)
            crop_filter = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"

        subtitle_filter = f"{crop_filter}subtitles=filename='{safe_ass_path_ffmpeg}'"

        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-movflags', '+faststart',
            output_path,
            '-y'
        ]

        process = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        os.unlink(ass_path)
        os.unlink(safe_ass_path)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error burning subtitles: {str(e)}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"FFmpeg error output: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error burning subtitles: {str(e)}")
        return None

def trim_video(input_path, start, end):
    # Returns path to trimmed video (or original if no trim)
    if not start and not end:
        return input_path
    output_path = os.path.splitext(input_path)[0] + "_trimmed.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
    ]
    if start:
        cmd += ["-ss", start]
    if end:
        cmd += ["-to", end]
    cmd += [
        "-c", "copy", output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except Exception as e:
        print(f"Error trimming video: {e}")
        return input_path

def download_videos(urls):
    for entry in urls:
        url = entry["url"]
        start = entry.get("start")
        end = entry.get("end")
        quality = entry.get("quality", "1080p")
        subs = entry.get("subs", "on")
        lang = entry.get("lang", "Automatic")
        # Set yt-dlp format string
        fmt = f"bestvideo[height<={quality.replace('p','')}]+bestaudio/best[height<={quality.replace('p','')}]"
        ydl_opts = {
            'format': fmt,
            'merge_output_format': 'mp4',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'ignoreerrors': True,
        }
        os.makedirs('downloads', exist_ok=True)
        with YoutubeDL(ydl_opts) as ydl:
            try:
                print(f"\nDownloading: {url} (quality={quality})")
                info = ydl.extract_info(url, download=True)
                if not info:
                    print(f"Failed to download: {url}")
                    continue
                video_path = ydl.prepare_filename(info)
                if os.path.exists(video_path):
                    # Trim video if needed
                    trimmed_path = trim_video(video_path, start, end)
                    # Subtitles
                    if subs == "on":
                        srt_path = generate_srt_file(trimmed_path, lang)
                        if srt_path:
                            output_path = burn_subtitles(trimmed_path, srt_path)
                            if output_path:
                                print(f"Successfully created video with subtitles: {output_path}")
                            os.unlink(srt_path)
                    else:
                        print("Subtitles disabled for this video.")
                    if trimmed_path != video_path and os.path.exists(trimmed_path):
                        os.unlink(trimmed_path)
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")

def main():
    input_file = 'video_links.txt'
    urls = read_urls(input_file)
    if not urls:
        print("No URLs found in the input file.")
        return
    print(f"Found {len(urls)} URLs to download.")
    download_videos(urls)

if __name__ == "__main__":
    main()
