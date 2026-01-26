import reflex as rx
import random
from typing import TypedDict, Optional
import datetime
import os
import asyncio
from pathlib import Path
import ffmpeg
import logging
import shutil
import re


class FileJob(TypedDict):
    id: str
    filename: str
    size_str: str
    status: str
    progress: float
    uploaded_at: str
    resolution: str
    quality: str
    converted_filename: Optional[str]
    converted_size_str: Optional[str]
    error_message: Optional[str]


class AppState(rx.State):
    """The central state for the application."""

    MAX_CAPACITY_GB: float = 100.0
    used_capacity_gb: float = 0.0
    is_uploading: bool = False
    selected_resolution: str = "Original"
    selected_quality: str = "High"
    resolution_options: list[str] = ["Original", "1080p", "720p", "480p"]
    quality_options: list[str] = ["Standard", "High", "Maximum"]
    allowed_extensions: list[str] = ["avi", "mov", "mkv", "wmv", "mp4", "webm"]
    recent_jobs: list[FileJob] = []

    async def _update_job_progress(self, job_id: str, progress: float):
        async with self:
            for idx, job in enumerate(self.recent_jobs):
                if job["id"] == job_id:
                    self.recent_jobs[idx]["progress"] = round(progress, 2)
                    break

    @rx.event
    def set_resolution(self, resolution: str):
        self.selected_resolution = resolution

    @rx.event
    def set_quality(self, quality: str):
        self.selected_quality = quality

    @rx.event
    def remove_job(self, job_id: str):
        job = next((j for j in self.recent_jobs if j["id"] == job_id), None)
        if job:
            try:
                upload_dir = rx.get_upload_dir()
                if job["filename"]:
                    (upload_dir / job["filename"]).unlink(missing_ok=True)
                if job.get("converted_filename"):
                    (upload_dir / job["converted_filename"]).unlink(missing_ok=True)
            except Exception as e:
                logging.exception(f"Error removing files for job {job_id}: {e}")
        self.recent_jobs = [j for j in self.recent_jobs if j["id"] != job_id]

    @rx.event
    def retry_job(self, job_id: str):
        for job in self.recent_jobs:
            if job["id"] == job_id:
                job["status"] = "Queued"
                job["progress"] = 0.0
                job["error_message"] = None
                yield AppState.process_job(job_id)
                break
        yield rx.toast.info("Job requeued for processing.")

    @rx.var
    def remaining_capacity_gb(self) -> float:
        return self.MAX_CAPACITY_GB - self.used_capacity_gb

    @rx.var
    def usage_percentage(self) -> float:
        return self.used_capacity_gb / self.MAX_CAPACITY_GB * 100

    @rx.var
    def usage_color(self) -> str:
        pct = self.usage_percentage
        if pct > 90:
            return "bg-red-500"
        if pct > 75:
            return "bg-amber-500"
        return "bg-indigo-600"

    def _format_size(self, size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle the file upload event."""
        self.is_uploading = True
        uploaded_count = 0
        errors = []
        jobs_to_process = []
        upload_dir = rx.get_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)
        for file in files:
            try:
                upload_data = await file.read()
                filename = file.name
                base_name = Path(filename).stem
                ext = Path(filename).suffix.lower()
                if ext[1:] not in self.allowed_extensions:
                    errors.append(f"{filename}: Invalid file type {ext}")
                    continue
                unique_filename = f"{base_name}_{random.randint(1000, 9999)}{ext}"
                file_path = upload_dir / unique_filename
                file_size = len(upload_data)
                file_size_gb = file_size / (1024 * 1024 * 1024)
                if self.used_capacity_gb + file_size_gb > self.MAX_CAPACITY_GB:
                    errors.append(f"{filename}: Not enough capacity.")
                    continue
                with open(file_path, "wb") as f:
                    f.write(upload_data)
                self.used_capacity_gb += file_size_gb
                job_id = f"job_{random.randint(10000, 99999)}"
                new_job: FileJob = {
                    "id": job_id,
                    "filename": unique_filename,
                    "size_str": self._format_size(file_size),
                    "status": "Queued",
                    "progress": 0.0,
                    "uploaded_at": datetime.datetime.now().strftime("%H:%M"),
                    "resolution": self.selected_resolution,
                    "quality": self.selected_quality,
                    "converted_filename": None,
                    "converted_size_str": None,
                    "error_message": None,
                }
                self.recent_jobs.insert(0, new_job)
                uploaded_count += 1
                jobs_to_process.append(job_id)
            except Exception as e:
                logging.exception(f"Failed to upload {file.name}: {str(e)}")
                errors.append(f"Failed to upload {file.name}: {str(e)}")
        self.is_uploading = False
        if uploaded_count > 0:
            yield rx.toast.success(f"Successfully uploaded {uploaded_count} file(s).")
            for job_id in jobs_to_process:
                yield AppState.process_job(job_id)
        for err in errors:
            yield rx.toast.error(err)

    @rx.event(background=True)
    async def process_job(self, job_id: str):
        """Process the conversion job in the background."""
        async with self:
            job_idx = -1
            for i, job in enumerate(self.recent_jobs):
                if job["id"] == job_id:
                    job_idx = i
                    break
            if job_idx == -1:
                return
            if not shutil.which("ffmpeg"):
                self.recent_jobs[job_idx]["status"] = "Error"
                self.recent_jobs[job_idx]["error_message"] = (
                    "Server Error: FFmpeg not installed"
                )
                return
            job = self.recent_jobs[job_idx]
            self.recent_jobs[job_idx]["status"] = "Processing"
            self.recent_jobs[job_idx]["progress"] = 5.0
            input_filename = job["filename"]
            resolution_mode = job["resolution"]
            quality_mode = job["quality"]
        upload_dir = rx.get_upload_dir()
        input_path = upload_dir / input_filename
        output_filename = f"converted_{Path(input_filename).stem}.mp4"
        output_path = upload_dir / output_filename
        try:
            if not input_path.exists():
                raise FileNotFoundError(f"Input file {input_filename} not found")
            duration_seconds = get_media_duration(input_path)
            stream = ffmpeg.input(input_path)
            if resolution_mode == "1080p":
                stream = stream.filter("scale", -1, 1080)
            elif resolution_mode == "720p":
                stream = stream.filter("scale", -1, 720)
            elif resolution_mode == "480p":
                stream = stream.filter("scale", -1, 480)
            crf = 23
            preset = "medium"
            if quality_mode == "High":
                crf = 18
                preset = "slow"
            elif quality_mode == "Maximum":
                crf = 15
                preset = "veryslow"
            elif quality_mode == "Standard":
                crf = 28
                preset = "fast"
            async with self:
                self.recent_jobs[job_idx]["progress"] = 10.0
            loop = asyncio.get_running_loop()
            progress_callback = None
            if duration_seconds and duration_seconds > 0:
                def progress_callback(pct: float):
                    asyncio.run_coroutine_threadsafe(
                        self._update_job_progress(job_id, pct), loop
                    )
            await asyncio.to_thread(
                run_ffmpeg,
                stream,
                output_path,
                crf,
                preset,
                duration_seconds,
                progress_callback,
            )
            if not output_path.exists():
                raise Exception("Conversion failed: Output file not created")
            converted_size = output_path.stat().st_size
            async with self:
                self.recent_jobs[job_idx]["status"] = "Complete"
                self.recent_jobs[job_idx]["progress"] = 100.0
                self.recent_jobs[job_idx]["converted_filename"] = output_filename
                self.recent_jobs[job_idx]["converted_size_str"] = self._format_size(
                    converted_size
                )
                self.used_capacity_gb += converted_size / (1024 * 1024 * 1024)
        except Exception as e:
            logging.exception(f"Conversion error for job {job_id}")
            async with self:
                self.recent_jobs[job_idx]["status"] = "Error"
                self.recent_jobs[job_idx]["error_message"] = str(e)


_TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")
_OUT_TIME_MS_RE = re.compile(r"out_time_ms=(\d+)")


def _parse_ffmpeg_time(line: str) -> Optional[float]:
    match = _TIME_RE.search(line)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def get_media_duration(path: Path) -> Optional[float]:
    try:
        probe = ffmpeg.probe(str(path))
        if "format" in probe and "duration" in probe["format"]:
            return float(probe["format"]["duration"])
        for stream in probe.get("streams", []):
            if "duration" in stream:
                return float(stream["duration"])
    except Exception:
        return None
    return None


def run_ffmpeg(stream, output_path, crf, preset, duration_seconds, progress_callback):
    """Helper to run ffmpeg synchronously with optional progress callback."""
    output_file = str(output_path)
    stream = ffmpeg.output(
        stream, output_file, vcodec="libx264", crf=crf, preset=preset, acodec="aac"
    )
    if duration_seconds and progress_callback:
        stream = stream.global_args("-progress", "pipe:1", "-nostats")
        process = stream.run_async(pipe_stdout=True, pipe_stderr=True, overwrite_output=True)
        last_percent = 0.0
        while True:
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break
                continue
            text = line.decode("utf-8", errors="ignore").strip()
            match = _OUT_TIME_MS_RE.match(text)
            if not match:
                continue
            out_time_ms = int(match.group(1))
            elapsed = out_time_ms / 1_000_000
            percent = min(99.99, max(0.0, (elapsed / duration_seconds) * 100))
            if percent - last_percent >= 0.01:
                last_percent = percent
                progress_callback(percent)
        process.wait()
    else:
        stream.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)