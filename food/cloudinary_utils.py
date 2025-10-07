"""
Cloudinary utilities for handling image uploads
"""
import cloudinary.uploader
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status


def upload_to_cloudinary(file, folder="uploads", resource_type="image"):
    """
    Upload file to Cloudinary with the configured upload preset
    
    Args:
        file: The file object to upload
        folder: Cloudinary folder to organize uploads
        resource_type: Type of resource (image, video, raw)
    
    Returns:
        dict: Cloudinary upload response or error dict
    """
    try:
        # Upload with upload preset (no API key/secret needed)
        upload_result = cloudinary.uploader.upload(
            file,
            upload_preset=settings.CLOUDINARY_STORAGE['UPLOAD_PRESET'],
            folder=folder,
            resource_type=resource_type,
            quality="auto",
            fetch_format="auto"
        )
        
        return {
            'success': True,
            'public_id': upload_result['public_id'],
            'url': upload_result['secure_url'],
            'width': upload_result.get('width'),
            'height': upload_result.get('height'),
            'format': upload_result.get('format'),
            'bytes': upload_result.get('bytes')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def delete_from_cloudinary(public_id):
    """
    Delete image from Cloudinary
    
    Args:
        public_id: The public ID of the image to delete
    
    Returns:
        dict: Success/error response
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return {
            'success': result.get('result') == 'ok',
            'result': result
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_cloudinary_url(public_id, transformation=None):
    """
    Get Cloudinary URL for an image with optional transformations
    
    Args:
        public_id: The public ID of the image
        transformation: Dict of transformation parameters
    
    Returns:
        str: The Cloudinary URL
    """
    if not public_id:
        return None
        
    try:
        from cloudinary import CloudinaryImage
        
        if transformation:
            return CloudinaryImage(public_id).build_url(**transformation)
        else:
            return CloudinaryImage(public_id).build_url()
    except Exception:
        return None