"""Tests for audio download utilities."""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app.utils.audio import download_audio, cleanup_audio, _get_extension_from_content_type


class TestAudioDownload:
    @patch("app.utils.audio.requests.get")
    def test_download_audio_success(self, mock_get):
        """Test successful audio download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "audio/wav"}
        mock_response.iter_content = lambda chunk_size: [b"audio_data_chunk1", b"audio_data_chunk2"]
        mock_get.return_value = mock_response

        url = "https://example.com/call.wav"
        local_path = download_audio(url)

        assert os.path.exists(local_path)
        assert local_path.endswith(".wav")

        # Cleanup
        cleanup_audio(local_path)

    @patch("app.utils.audio.requests.get")
    def test_download_audio_with_retry(self, mock_get):
        """Test retry logic on transient failures."""
        # Fail twice, succeed on third attempt
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "audio/mp3"}
        mock_response.iter_content = lambda chunk_size: [b"audio_data"]

        mock_get.side_effect = [
            Exception("Connection timeout"),
            Exception("Temporary failure"),
            mock_response,
        ]

        url = "https://example.com/call.mp3"
        local_path = download_audio(url, max_retries=3)

        assert os.path.exists(local_path)
        assert local_path.endswith(".mp3")
        assert mock_get.call_count == 3

        cleanup_audio(local_path)

    @patch("app.utils.audio.requests.get")
    def test_download_audio_all_retries_fail(self, mock_get):
        """Test that error is raised after all retries fail."""
        mock_get.side_effect = Exception("Persistent network error")

        url = "https://example.com/call.wav"

        with pytest.raises(Exception, match="Failed to download"):
            download_audio(url, max_retries=2)

    def test_download_audio_invalid_url(self):
        """Test that invalid URLs are rejected."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com/file.wav",
            "/local/path/file.wav",
            "",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid URL"):
                download_audio(url)

    @patch("app.utils.audio.requests.get")
    def test_download_audio_content_type_mapping(self, mock_get):
        """Test correct file extension based on content type."""
        test_cases = [
            ("audio/mpeg", ".mp3"),
            ("audio/wav", ".wav"),
            ("audio/ogg", ".ogg"),
            ("audio/webm", ".webm"),
            ("video/mp4", ".mp4"),
            ("video/webm", ".webm"),
            ("application/octet-stream", ".wav"),  # Default
        ]

        for content_type, expected_ext in test_cases:
            mock_response = MagicMock()
            mock_response.headers = {"content-type": content_type}
            mock_response.iter_content = lambda chunk_size: [b"data"]
            mock_get.return_value = mock_response

            url = f"https://example.com/call"
            local_path = download_audio(url)

            assert local_path.endswith(expected_ext), f"Expected {expected_ext} for {content_type}"
            cleanup_audio(local_path)

    @patch("app.utils.audio.requests.get")
    def test_download_audio_streaming(self, mock_get):
        """Test that large files are streamed in chunks."""
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "audio/wav"}
        chunks = [b"chunk1" * 1000, b"chunk2" * 1000, b"chunk3" * 1000]
        mock_response.iter_content = lambda chunk_size: chunks
        mock_get.return_value = mock_response

        url = "https://example.com/large_call.wav"
        local_path = download_audio(url)

        # Verify file was created with streamed data
        assert os.path.exists(local_path)
        file_size = os.path.getsize(local_path)
        assert file_size > 0

        cleanup_audio(local_path)


class TestContentTypeMapping:
    def test_content_type_to_extension(self):
        """Test content type to file extension mapping."""
        test_cases = {
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/ogg": ".ogg",
            "audio/webm": ".webm",
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "unknown/type": ".wav",  # Default
        }

        for content_type, expected_ext in test_cases.items():
            assert _get_extension_from_content_type(content_type) == expected_ext


class TestAudioCleanup:
    def test_cleanup_existing_file(self):
        """Test cleanup of existing temporary file."""
        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"test data")

        assert os.path.exists(temp_path)

        # Cleanup
        cleanup_audio(temp_path)

        assert not os.path.exists(temp_path)

    def test_cleanup_nonexistent_file(self):
        """Test cleanup doesn't fail on nonexistent file."""
        # Should not raise exception
        cleanup_audio("/nonexistent/path/file.wav")

    def test_cleanup_permission_error(self):
        """Test cleanup handles permission errors gracefully."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name

        # This test is platform-specific; on Unix we can change permissions
        # For now, just verify the function doesn't crash on error
        with patch("os.remove", side_effect=PermissionError("Permission denied")):
            cleanup_audio(temp_path)  # Should log warning but not raise
