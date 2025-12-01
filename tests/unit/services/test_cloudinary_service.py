"""
Unit tests for CloudinaryService.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from io import BytesIO
from fastapi import UploadFile, HTTPException
from app.services.cloudinary_service import CloudinaryService


class TestCloudinaryService:
    """Test cases for CloudinaryService."""

    def test_upload_avatar_success(self):
        """Test successfully uploading an avatar."""
        # Create mock file
        mock_file_content = b"fake image content"
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=mock_file_content)
        mock_file.seek = AsyncMock()
        mock_file.file = BytesIO(mock_file_content)

        with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
            mock_upload.return_value = {'secure_url': 'https://cloudinary.com/avatar.jpg'}

            result = asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=1))

            assert result == 'https://cloudinary.com/avatar.jpg'
            mock_upload.assert_called_once()
            assert mock_upload.call_args[1]['folder'] == 'contacts_app/avatars'
            assert mock_upload.call_args[1]['public_id'] == 'user_1'
            assert mock_upload.call_args[1]['overwrite'] is True

    def test_upload_avatar_invalid_content_type(self):
        """Test uploading non-image file raises error."""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "text/plain"

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=1))

        assert exc_info.value.status_code == 400
        assert "must be an image" in exc_info.value.detail

    def test_upload_avatar_no_content_type(self):
        """Test uploading file with no content type raises error."""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = None

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=1))

        assert exc_info.value.status_code == 400
        assert "must be an image" in exc_info.value.detail

    def test_upload_avatar_file_too_large(self):
        """Test uploading file larger than 5MB raises error."""
        # Create 6MB of fake data
        large_content = b"x" * (6 * 1024 * 1024)

        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=large_content)

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=1))

        assert exc_info.value.status_code == 400
        assert "less than 5MB" in exc_info.value.detail

    def test_upload_avatar_cloudinary_error(self):
        """Test handling Cloudinary upload error."""
        mock_file_content = b"fake image content"
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/png"
        mock_file.read = AsyncMock(return_value=mock_file_content)
        mock_file.seek = AsyncMock()
        mock_file.file = BytesIO(mock_file_content)

        with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
            mock_upload.side_effect = Exception("Cloudinary API error")

            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=1))

            assert exc_info.value.status_code == 500
            assert "Failed to upload image" in exc_info.value.detail

    def test_upload_avatar_with_png(self):
        """Test uploading PNG image."""
        mock_file_content = b"fake png content"
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/png"
        mock_file.read = AsyncMock(return_value=mock_file_content)
        mock_file.seek = AsyncMock()
        mock_file.file = BytesIO(mock_file_content)

        with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
            mock_upload.return_value = {'secure_url': 'https://cloudinary.com/avatar.png'}

            result = asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=2))

            assert result == 'https://cloudinary.com/avatar.png'

    def test_upload_avatar_with_gif(self):
        """Test uploading GIF image."""
        mock_file_content = b"fake gif content"
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/gif"
        mock_file.read = AsyncMock(return_value=mock_file_content)
        mock_file.seek = AsyncMock()
        mock_file.file = BytesIO(mock_file_content)

        with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
            mock_upload.return_value = {'secure_url': 'https://cloudinary.com/avatar.gif'}

            result = asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=3))

            assert result == 'https://cloudinary.com/avatar.gif'

    def test_upload_avatar_transformation_applied(self):
        """Test that image transformations are applied."""
        mock_file_content = b"fake image content"
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=mock_file_content)
        mock_file.seek = AsyncMock()
        mock_file.file = BytesIO(mock_file_content)

        with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
            mock_upload.return_value = {'secure_url': 'https://cloudinary.com/avatar.jpg'}

            asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=1))

            # Verify transformations
            call_args = mock_upload.call_args[1]
            assert 'transformation' in call_args
            transformations = call_args['transformation']
            assert len(transformations) == 2
            assert transformations[0]['width'] == 250
            assert transformations[0]['height'] == 250
            assert transformations[0]['crop'] == 'fill'
            assert transformations[0]['gravity'] == 'face'

    def test_upload_avatar_exactly_5mb(self):
        """Test uploading file exactly 5MB (boundary test)."""
        # Create exactly 5MB of fake data
        exact_5mb = b"x" * (5 * 1024 * 1024)

        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=exact_5mb)
        mock_file.seek = AsyncMock()
        mock_file.file = BytesIO(exact_5mb)

        with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
            mock_upload.return_value = {'secure_url': 'https://cloudinary.com/avatar.jpg'}

            result = asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=1))

            # Should succeed - exactly 5MB is allowed
            assert result == 'https://cloudinary.com/avatar.jpg'

    def test_upload_avatar_different_user_ids(self):
        """Test that different user IDs create different public_ids."""
        mock_file_content = b"fake image"

        for user_id in [1, 42, 999]:
            mock_file = Mock(spec=UploadFile)
            mock_file.content_type = "image/jpeg"
            mock_file.read = AsyncMock(return_value=mock_file_content)
            mock_file.seek = AsyncMock()
            mock_file.file = BytesIO(mock_file_content)

            with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
                mock_upload.return_value = {'secure_url': f'https://cloudinary.com/user_{user_id}.jpg'}

                result = asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=user_id))

                assert result == f'https://cloudinary.com/user_{user_id}.jpg'
                assert mock_upload.call_args[1]['public_id'] == f'user_{user_id}'

    def test_delete_avatar_success(self):
        """Test successfully deleting an avatar."""
        with patch('app.services.cloudinary_service.cloudinary.uploader.destroy') as mock_destroy:
            mock_destroy.return_value = {'result': 'ok'}

            result = CloudinaryService.delete_avatar('user_1')

            assert result is True
            mock_destroy.assert_called_once_with('user_1')

    def test_delete_avatar_failure(self):
        """Test deleting avatar when Cloudinary returns failure."""
        with patch('app.services.cloudinary_service.cloudinary.uploader.destroy') as mock_destroy:
            mock_destroy.return_value = {'result': 'not found'}

            result = CloudinaryService.delete_avatar('user_1')

            assert result is False

    def test_delete_avatar_exception(self):
        """Test handling exception during avatar deletion."""
        with patch('app.services.cloudinary_service.cloudinary.uploader.destroy') as mock_destroy:
            mock_destroy.side_effect = Exception("Cloudinary error")

            result = CloudinaryService.delete_avatar('user_1')

            assert result is False

    def test_get_avatar_url_without_transformation(self):
        """Test getting avatar URL without transformation."""
        with patch('app.services.cloudinary_service.cloudinary.CloudinaryImage') as mock_image:
            mock_instance = Mock()
            mock_instance.build_url.return_value = 'https://cloudinary.com/avatar.jpg'
            mock_image.return_value = mock_instance

            result = CloudinaryService.get_avatar_url('user_1')

            assert result == 'https://cloudinary.com/avatar.jpg'
            mock_image.assert_called_once_with('user_1')
            mock_instance.build_url.assert_called_once_with()

    def test_get_avatar_url_with_transformation(self):
        """Test getting avatar URL with transformation."""
        transformation = {'width': 100, 'height': 100}

        with patch('app.services.cloudinary_service.cloudinary.CloudinaryImage') as mock_image:
            mock_instance = Mock()
            mock_instance.build_url.return_value = 'https://cloudinary.com/avatar_100x100.jpg'
            mock_image.return_value = mock_instance

            result = CloudinaryService.get_avatar_url('user_1', transformation)

            assert result == 'https://cloudinary.com/avatar_100x100.jpg'
            mock_image.assert_called_once_with('user_1')
            mock_instance.build_url.assert_called_once_with(**transformation)

    def test_get_avatar_url_exception(self):
        """Test handling exception when building avatar URL."""
        with patch('app.services.cloudinary_service.cloudinary.CloudinaryImage') as mock_image:
            mock_image.side_effect = Exception("URL build error")

            result = CloudinaryService.get_avatar_url('user_1')

            assert result == ""

    def test_upload_avatar_webp_format(self):
        """Test uploading WebP image format."""
        mock_file_content = b"fake webp content"
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/webp"
        mock_file.read = AsyncMock(return_value=mock_file_content)
        mock_file.seek = AsyncMock()
        mock_file.file = BytesIO(mock_file_content)

        with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
            mock_upload.return_value = {'secure_url': 'https://cloudinary.com/avatar.webp'}

            result = asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=4))

            assert result == 'https://cloudinary.com/avatar.webp'

    def test_upload_avatar_quality_optimization(self):
        """Test that quality optimization is included in transformations."""
        mock_file_content = b"fake image"
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=mock_file_content)
        mock_file.seek = AsyncMock()
        mock_file.file = BytesIO(mock_file_content)

        with patch('app.services.cloudinary_service.cloudinary.uploader.upload') as mock_upload:
            mock_upload.return_value = {'secure_url': 'https://cloudinary.com/avatar.jpg'}

            asyncio.run(CloudinaryService.upload_avatar(mock_file, user_id=1))

            # Check quality optimization
            transformations = mock_upload.call_args[1]['transformation']
            assert transformations[1]['quality'] == 'auto'
            assert transformations[1]['fetch_format'] == 'auto'

    def test_delete_avatar_with_folder_path(self):
        """Test deleting avatar with folder path in public_id."""
        with patch('app.services.cloudinary_service.cloudinary.uploader.destroy') as mock_destroy:
            mock_destroy.return_value = {'result': 'ok'}

            result = CloudinaryService.delete_avatar('contacts_app/avatars/user_1')

            assert result is True
            mock_destroy.assert_called_once_with('contacts_app/avatars/user_1')

    def test_get_avatar_url_with_multiple_transformations(self):
        """Test getting avatar URL with multiple transformation parameters."""
        transformation = {
            'width': 150,
            'height': 150,
            'crop': 'thumb',
            'gravity': 'center'
        }

        with patch('app.services.cloudinary_service.cloudinary.CloudinaryImage') as mock_image:
            mock_instance = Mock()
            mock_instance.build_url.return_value = 'https://cloudinary.com/avatar_custom.jpg'
            mock_image.return_value = mock_instance

            result = CloudinaryService.get_avatar_url('user_1', transformation)

            assert result == 'https://cloudinary.com/avatar_custom.jpg'
            mock_instance.build_url.assert_called_once_with(**transformation)

