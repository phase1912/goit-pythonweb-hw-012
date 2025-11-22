import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True
)


class CloudinaryService:

    @staticmethod
    async def upload_avatar(file: UploadFile, user_id: int) -> str:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (jpeg, png, gif, etc.)"
            )

        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 5MB"
            )

        await file.seek(0)

        try:
            result = cloudinary.uploader.upload(
                file.file,
                folder=f"contacts_app/avatars",
                public_id=f"user_{user_id}",
                overwrite=True,
                transformation=[
                    {'width': 250, 'height': 250, 'crop': 'fill', 'gravity': 'face'},
                    {'quality': 'auto', 'fetch_format': 'auto'}
                ]
            )

            return result.get('secure_url')

        except Exception as e:
            print(f"Error uploading to Cloudinary: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload image: {str(e)}"
            )

    @staticmethod
    def delete_avatar(public_id: str) -> bool:
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")
            return False

    @staticmethod
    def get_avatar_url(public_id: str, transformation: dict = None) -> str:
        try:
            if transformation:
                return cloudinary.CloudinaryImage(public_id).build_url(**transformation)
            return cloudinary.CloudinaryImage(public_id).build_url()
        except Exception as e:
            print(f"Error building Cloudinary URL: {e}")
            return ""


cloudinary_service = CloudinaryService()

