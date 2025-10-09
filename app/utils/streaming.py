"""
Streaming upload utilities for handling large files efficiently.
Implements chunked uploads with progress tracking and resumability.
"""

import asyncio
import hashlib
import os
import tempfile
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import aiofiles
from fastapi import HTTPException, UploadFile
from starlette.datastructures import FormData

from app.utils.monitoring import performance_metrics


class ChunkedUploadManager:
    """Manages chunked file uploads with resumability."""

    def __init__(self, chunk_size: int = 8192, max_file_size: int = 100 * 1024 * 1024):
        self.chunk_size = chunk_size
        self.max_file_size = max_file_size
        self.active_uploads = {}
        self.upload_dir = Path(tempfile.gettempdir()) / "uploads"
        self.upload_dir.mkdir(exist_ok=True)

    async def start_upload(self, filename: str, total_size: int, content_type: str) -> str:
        """Start a new chunked upload session."""
        if total_size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.max_file_size} bytes"
            )

        upload_id = hashlib.md5(f"{filename}{time.time()}".encode()).hexdigest()
        upload_info = {
            'filename': filename,
            'total_size': total_size,
            'content_type': content_type,
            'uploaded_size': 0,
            'chunks': [],
            'created_at': time.time(),
            'temp_file': self.upload_dir / f"{upload_id}.tmp"
        }

        self.active_uploads[upload_id] = upload_info
        return upload_id

    async def upload_chunk(self, upload_id: str, chunk_data: bytes, chunk_index: int) -> Dict:
        """Upload a chunk of data."""
        if upload_id not in self.active_uploads:
            raise HTTPException(status_code=404, detail="Upload session not found")

        upload_info = self.active_uploads[upload_id]

        # Write chunk to temporary file
        async with aiofiles.open(upload_info['temp_file'], 'ab') as f:
            await f.write(chunk_data)

        # Update upload progress
        upload_info['uploaded_size'] += len(chunk_data)
        upload_info['chunks'].append({
            'index': chunk_index,
            'size': len(chunk_data),
            'uploaded_at': time.time()
        })

        # Calculate progress
        progress = (upload_info['uploaded_size'] / upload_info['total_size']) * 100

        # Record metrics
        performance_metrics.record_function_call("upload_chunk", len(chunk_data))

        return {
            'upload_id': upload_id,
            'progress': round(progress, 2),
            'uploaded_size': upload_info['uploaded_size'],
            'total_size': upload_info['total_size'],
            'chunks_received': len(upload_info['chunks']),
            'is_complete': upload_info['uploaded_size'] >= upload_info['total_size']
        }

    async def complete_upload(self, upload_id: str, final_destination: Path) -> Dict:
        """Complete the upload and move file to final destination."""
        if upload_id not in self.active_uploads:
            raise HTTPException(status_code=404, detail="Upload session not found")

        upload_info = self.active_uploads[upload_id]

        if upload_info['uploaded_size'] != upload_info['total_size']:
            raise HTTPException(status_code=400, detail="Upload incomplete")

        # Move temp file to final destination
        final_destination.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(upload_info['temp_file'], 'rb') as src:
            async with aiofiles.open(final_destination, 'wb') as dst:
                async for chunk in self._read_chunks(src):
                    await dst.write(chunk)

        # Clean up temp file
        upload_info['temp_file'].unlink(missing_ok=True)

        # Remove from active uploads
        result = {
            'upload_id': upload_id,
            'filename': upload_info['filename'],
            'size': upload_info['total_size'],
            'destination': str(final_destination),
            'upload_time': time.time() - upload_info['created_at']
        }

        del self.active_uploads[upload_id]
        return result

    async def cancel_upload(self, upload_id: str):
        """Cancel an active upload session."""
        if upload_id in self.active_uploads:
            upload_info = self.active_uploads[upload_id]
            upload_info['temp_file'].unlink(missing_ok=True)
            del self.active_uploads[upload_id]

    async def get_upload_status(self, upload_id: str) -> Dict:
        """Get the current status of an upload."""
        if upload_id not in self.active_uploads:
            raise HTTPException(status_code=404, detail="Upload session not found")

        upload_info = self.active_uploads[upload_id]
        progress = (upload_info['uploaded_size'] / upload_info['total_size']) * 100

        return {
            'upload_id': upload_id,
            'filename': upload_info['filename'],
            'progress': round(progress, 2),
            'uploaded_size': upload_info['uploaded_size'],
            'total_size': upload_info['total_size'],
            'chunks_received': len(upload_info['chunks']),
            'elapsed_time': time.time() - upload_info['created_at']
        }

    async def _read_chunks(self, file_handle) -> AsyncGenerator[bytes, None]:
        """Read file in chunks."""
        while True:
            chunk = await file_handle.read(self.chunk_size)
            if not chunk:
                break
            yield chunk

    def cleanup_stale_uploads(self, max_age_hours: int = 24):
        """Clean up uploads older than specified hours."""
        current_time = time.time()
        stale_uploads = []

        for upload_id, info in self.active_uploads.items():
            age_hours = (current_time - info['created_at']) / 3600
            if age_hours > max_age_hours:
                stale_uploads.append(upload_id)

        for upload_id in stale_uploads:
            asyncio.create_task(self.cancel_upload(upload_id))


class StreamingUploadHandler:
    """Handler for streaming file uploads with validation."""

    def __init__(self, max_file_size: int = 100 * 1024 * 1024):
        self.max_file_size = max_file_size
        self.allowed_extensions = {'.txt', '.pdf', '.doc', '.docx', '.rtf', '.odt'}
        self.allowed_mime_types = {
            'text/plain',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/rtf',
            'application/vnd.oasis.opendocument.text'
        }

    async def validate_upload(self, file: UploadFile) -> Tuple[bool, str]:
        """Validate uploaded file."""
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size:
            return False, f"File too large. Maximum size is {self.max_file_size // (1024*1024)}MB"

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            return False, f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"

        # Check MIME type
        if file.content_type not in self.allowed_mime_types:
            return False, f"Content type not allowed: {file.content_type}"

        # Check for empty files
        if hasattr(file, 'size') and file.size == 0:
            return False, "Empty files are not allowed"

        return True, "Valid file"

    async def stream_upload_to_file(self, file: UploadFile, destination: Path) -> Dict:
        """Stream upload directly to destination with progress tracking."""
        start_time = time.time()
        total_bytes = 0
        chunk_count = 0

        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(destination, 'wb') as dst:
                async for chunk in self._read_upload_chunks(file):
                    await dst.write(chunk)
                    total_bytes += len(chunk)
                    chunk_count += 1

                    # Check size limit during streaming
                    if total_bytes > self.max_file_size:
                        # Clean up partial file
                        destination.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=413,
                            detail="File too large"
                        )
        except Exception as e:
            # Clean up on error
            destination.unlink(missing_ok=True)
            raise e

        upload_time = time.time() - start_time

        # Record metrics
        performance_metrics.record_function_call("stream_upload", upload_time)

        return {
            'filename': file.filename,
            'size': total_bytes,
            'destination': str(destination),
            'upload_time': upload_time,
            'chunks_processed': chunk_count,
            'avg_chunk_size': total_bytes // chunk_count if chunk_count > 0 else 0
        }

    async def _read_upload_chunks(self, file: UploadFile) -> AsyncGenerator[bytes, None]:
        """Read upload file in chunks."""
        chunk_size = 8192

        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            yield chunk


class ProgressTracker:
    """Track upload progress for real-time updates."""

    def __init__(self):
        self.progress_data = {}

    def start_tracking(self, session_id: str, total_size: int) -> None:
        """Start tracking progress for a session."""
        self.progress_data[session_id] = {
            'total_size': total_size,
            'uploaded_size': 0,
            'start_time': time.time(),
            'last_update': time.time(),
            'speed_history': []
        }

    def update_progress(self, session_id: str, bytes_uploaded: int) -> Dict:
        """Update progress and calculate metrics."""
        if session_id not in self.progress_data:
            return {}

        data = self.progress_data[session_id]
        current_time = time.time()

        # Update uploaded bytes
        previous_size = data['uploaded_size']
        data['uploaded_size'] += bytes_uploaded

        # Calculate speed
        time_diff = current_time - data['last_update']
        if time_diff > 0:
            speed = bytes_uploaded / time_diff
            data['speed_history'].append(speed)

            # Keep only recent speed samples
            if len(data['speed_history']) > 10:
                data['speed_history'] = data['speed_history'][-10:]

        data['last_update'] = current_time

        # Calculate metrics
        progress_percent = (data['uploaded_size'] / data['total_size']) * 100
        avg_speed = sum(data['speed_history']) / len(data['speed_history']) if data['speed_history'] else 0

        # Estimate remaining time
        remaining_bytes = data['total_size'] - data['uploaded_size']
        eta_seconds = remaining_bytes / avg_speed if avg_speed > 0 else 0

        return {
            'session_id': session_id,
            'progress_percent': round(progress_percent, 2),
            'uploaded_size': data['uploaded_size'],
            'total_size': data['total_size'],
            'speed_bytes_per_sec': round(avg_speed, 2),
            'eta_seconds': round(eta_seconds, 2),
            'elapsed_seconds': round(current_time - data['start_time'], 2)
        }

    def finish_tracking(self, session_id: str) -> Dict:
        """Finish tracking and return final stats."""
        if session_id not in self.progress_data:
            return {}

        data = self.progress_data[session_id]
        total_time = time.time() - data['start_time']
        avg_speed = data['total_size'] / total_time if total_time > 0 else 0

        result = {
            'session_id': session_id,
            'total_size': data['total_size'],
            'total_time': round(total_time, 2),
            'average_speed': round(avg_speed, 2)
        }

        # Clean up
        del self.progress_data[session_id]
        return result

    def get_progress(self, session_id: str) -> Optional[Dict]:
        """Get current progress for a session."""
        if session_id not in self.progress_data:
            return None

        data = self.progress_data[session_id]
        progress_percent = (data['uploaded_size'] / data['total_size']) * 100

        return {
            'session_id': session_id,
            'progress_percent': round(progress_percent, 2),
            'uploaded_size': data['uploaded_size'],
            'total_size': data['total_size'],
            'elapsed_seconds': round(time.time() - data['start_time'], 2)
        }


# Global instances
chunked_upload_manager = ChunkedUploadManager()
streaming_upload_handler = StreamingUploadHandler()
progress_tracker = ProgressTracker()