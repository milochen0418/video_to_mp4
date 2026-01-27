import reflex as rx
import random
from typing import TypedDict, Optional
import datetime
import tempfile
import base64
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
    converted_filename: str
    converted_size_str: Optional[str]
    error_message: Optional[str]


class AppState(rx.State):
    """The central state for the application."""

    is_uploading: bool = False
    show_resolution_help: bool = False
    show_quality_help: bool = False
    show_confirm_dialog: bool = False
    pending_files: list[str] = []
    staged_files: list[dict] = []
    selected_resolution: str = "Original"
    selected_quality: str = "High"
    resolution_options: list[str] = ["Original", "4K", "1080p", "720p", "480p"]
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
    def toggle_resolution_help(self):
        self.show_resolution_help = not self.show_resolution_help
        if self.show_resolution_help:
            self.show_quality_help = False

    @rx.event
    def toggle_quality_help(self):
        self.show_quality_help = not self.show_quality_help
        if self.show_quality_help:
            self.show_resolution_help = False

    @rx.event
    def close_help(self):
        self.show_resolution_help = False
        self.show_quality_help = False

    @rx.event
    async def open_confirm(self, files: list[rx.UploadFile]):
        if not files:
            yield rx.toast.error("Please select at least one file.")
            return
        upload_dir = rx.get_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)
        self.pending_files = []
        self.staged_files = []
        errors = []
        for file in files:
            filename = "unknown"
            try:
                filename, upload_data = await self._read_upload_file(file)
                base_name = Path(filename).stem
                ext = Path(filename).suffix.lower()
                if ext[1:] not in self.allowed_extensions:
                    errors.append(f"{filename}: Invalid file type {ext}")
                    continue
                unique_filename = f"{base_name}_{random.randint(1000, 9999)}{ext}"
                file_path = upload_dir / unique_filename
                with open(file_path, "wb") as f:
                    f.write(upload_data)
                self.pending_files.append(filename)
                self.staged_files.append(
                    {
                        "original_name": filename,
                        "stored_name": unique_filename,
                        "size": len(upload_data),
                    }
                )
            except Exception as e:
                logging.exception(f"Failed to stage {filename}: {str(e)}")
                errors.append(f"Failed to stage {filename}: {str(e)}")
        for err in errors:
            yield rx.toast.error(err)
        if not self.staged_files:
            return
        self.show_confirm_dialog = True

    @rx.event
    def close_confirm(self):
        self.show_confirm_dialog = False
        if self.staged_files:
            upload_dir = rx.get_upload_dir()
            for item in self.staged_files:
                stored_name = item.get("stored_name")
                if stored_name:
                    (upload_dir / stored_name).unlink(missing_ok=True)
        self.pending_files = []
        self.staged_files = []

    @rx.event
    async def confirm_upload(self):
        self.show_confirm_dialog = False
        staged = list(self.staged_files)
        self.pending_files = []
        self.staged_files = []
        if not staged:
            yield rx.toast.error("No files to convert.")
            return
        uploaded_count = 0
        jobs_to_process = []
        for item in staged:
            stored_name = item.get("stored_name")
            original_name = item.get("original_name", stored_name)
            size = item.get("size", 0)
            if not stored_name:
                continue
            job_id = f"job_{random.randint(10000, 99999)}"
            new_job: FileJob = {
                "id": job_id,
                "filename": stored_name,
                "size_str": self._format_size(size),
                "status": "Queued",
                "progress": 0.0,
                "uploaded_at": datetime.datetime.now().strftime("%H:%M"),
                "resolution": self.selected_resolution,
                "quality": self.selected_quality,
                "converted_filename": "",
                "converted_size_str": None,
                "error_message": None,
            }
            self.recent_jobs.insert(0, new_job)
            uploaded_count += 1
            jobs_to_process.append(job_id)
        if uploaded_count > 0:
            yield rx.toast.success(f"Successfully uploaded {uploaded_count} file(s).")
            for job_id in jobs_to_process:
                yield AppState.process_job(job_id)

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

    def _format_size(self, size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    async def _read_upload_file(self, file) -> tuple[str, bytes]:
        logging.error(
            "Upload payload type: %s", type(file).__name__
        )
        if hasattr(file, "read"):
            upload_data = await file.read()
            filename = getattr(file, "name", "unknown")
            return filename, upload_data
        if isinstance(file, dict):
            logging.error("Upload payload keys: %s", list(file.keys()))
            logging.error("Upload payload headers: %s", file.get("headers"))
            filename = (
                file.get("name")
                or file.get("filename")
                or Path(file.get("path", "")).name
                or "unknown"
            )
            logging.error("Derived filename: %s", filename)
            if "file" in file:
                inner_file = file["file"]
                logging.error(
                    "Inner file type: %s", type(inner_file).__name__
                )
                if hasattr(inner_file, "read"):
                    upload_data = await inner_file.read()
                    return filename, upload_data
                if isinstance(inner_file, (bytes, bytearray)):
                    return filename, bytes(inner_file)
                if isinstance(inner_file, list):
                    return filename, bytes(inner_file)
                if isinstance(inner_file, str):
                    inner_path = inner_file
                    if inner_path:
                        logging.error("Inner file string value: %s", inner_path)
                        path = Path(inner_path)
                        if not path.is_absolute():
                            path = rx.get_upload_dir() / path
                        if path.exists():
                            return filename or path.name, path.read_bytes()
                if isinstance(inner_file, dict):
                    logging.error(
                        "Inner file keys: %s", list(inner_file.keys())
                    )
                    inner_path = inner_file.get("path") or inner_file.get("file_path")
                    if inner_path:
                        logging.error("Inner file path: %s", inner_path)
                        path = Path(inner_path)
                        if not path.is_absolute():
                            path = rx.get_upload_dir() / path
                        if path.exists():
                            return filename or path.name, path.read_bytes()
                    inner_data = (
                        inner_file.get("data")
                        or inner_file.get("content")
                        or inner_file.get("contents")
                    )
                    if isinstance(inner_data, list):
                        return filename, bytes(inner_data)
                    if isinstance(inner_data, str):
                        try:
                            return filename, base64.b64decode(inner_data)
                        except Exception:
                            return filename, inner_data.encode("utf-8")
            upload_data = file.get("data") or file.get("content") or file.get("contents")
            logging.error(
                "Inline data type: %s", type(upload_data).__name__
            )
            if isinstance(upload_data, list):
                upload_data = bytes(upload_data)
            if isinstance(upload_data, str):
                try:
                    upload_data = base64.b64decode(upload_data)
                except Exception:
                    upload_data = upload_data.encode("utf-8")
            if isinstance(upload_data, bytes):
                return filename, upload_data
            path_value = file.get("path") or file.get("file_path") or file.get("filepath")
            if path_value:
                logging.error("Payload path: %s", path_value)
                path = Path(path_value)
                candidate_paths = []
                if path.is_absolute():
                    candidate_paths.append(path)
                else:
                    candidate_paths.extend(
                        [
                            rx.get_upload_dir() / path,
                            Path.cwd() / path,
                            Path.cwd() / ".web" / path,
                            Path.cwd() / ".web" / "public" / path,
                            Path.cwd() / ".web" / "backend" / path,
                            Path.cwd() / ".web" / "backend" / "uploaded_files" / path,
                            Path(tempfile.gettempdir()) / path,
                        ]
                    )
                logging.error(
                    "Upload candidate paths: %s",
                    [str(p) for p in candidate_paths],
                )
                for candidate in candidate_paths:
                    if candidate.exists():
                        return filename or candidate.name, candidate.read_bytes()
            logging.error(
                "Unsupported upload file payload keys: %s", list(file.keys())
            )
        raise ValueError("Unsupported upload file payload")

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle the file upload event."""
        self.is_uploading = True
        uploaded_count = 0
        errors = []
        jobs_to_process = []
        upload_dir = rx.get_upload_dir()
        logging.error("Upload dir: %s", upload_dir)
        try:
            logging.error(
                "Upload dir contents: %s",
                [p.name for p in upload_dir.iterdir()],
            )
        except Exception as e:
            logging.error("Failed to list upload dir: %s", e)
        upload_dir.mkdir(parents=True, exist_ok=True)
        for file in files:
            filename = "unknown"
            try:
                filename, upload_data = await self._read_upload_file(file)
                base_name = Path(filename).stem
                ext = Path(filename).suffix.lower()
                if ext[1:] not in self.allowed_extensions:
                    errors.append(f"{filename}: Invalid file type {ext}")
                    continue
                unique_filename = f"{base_name}_{random.randint(1000, 9999)}{ext}"
                file_path = upload_dir / unique_filename
                file_size = len(upload_data)
                with open(file_path, "wb") as f:
                    f.write(upload_data)
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
                    "converted_filename": "",
                    "converted_size_str": None,
                    "error_message": None,
                }
                self.recent_jobs.insert(0, new_job)
                uploaded_count += 1
                jobs_to_process.append(job_id)
            except Exception as e:
                logging.exception(f"Failed to upload {filename}: {str(e)}")
                errors.append(f"Failed to upload {filename}: {str(e)}")
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
            if resolution_mode == "4K":
                stream = stream.filter("scale", -1, 2160)
            elif resolution_mode == "1080p":
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