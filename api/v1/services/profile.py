import cloudinary
import cloudinary.uploader

from api.core.config import settings

cloudinary.config(
	cloud_name = settings.CLOUD_NAME,
	api_key = settings.API_KEY,
	api_secret = settings.API_SECRETS
)

