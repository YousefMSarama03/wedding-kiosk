# Cloudinary Integration Guide

## Overview
Your Django project has been successfully integrated with Cloudinary for production-ready media handling. Images are now stored externally in Cloudinary instead of locally, ensuring persistence in production on Railway.

---

## Changes Made

### 1. **requirements.txt** - Added Dependencies
```
cloudinary>=1.40,<2
django-cloudinary-storage>=0.3,<1
```

**Why these packages?**
- `cloudinary`: Official Python SDK for Cloudinary API
- `django-cloudinary-storage`: Django storage backend for seamless integration with FileField/ImageField

---

### 2. **backend/app/settings.py** - Configuration Updates

#### a) Added to `INSTALLED_APPS`
```python
INSTALLED_APPS = [
    # ... existing apps ...
    "cloudinary",
    "cloudinary_storage",
    "events",
    "photos",
]
```

#### b) Added Cloudinary Configuration
```python
# Cloudinary Configuration for media storage
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", ""),
}

# Use Cloudinary storage for media files in production; fall back to local storage if not configured
if CLOUDINARY_STORAGE["CLOUD_NAME"]:
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    MEDIA_URL = "/media/"
else:
    # Fallback to local storage if Cloudinary is not configured
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"
```

**Key Features:**
- ✅ Environment variable-based configuration (safe for production)
- ✅ Automatic fallback to local storage if Cloudinary is not configured
- ✅ Compatible with both development and production
- ✅ No destructive database migrations required

---

## Environment Variables

Add these to your `.env` file (locally) or Railway environment variables (production):

```env
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### How to Get Your Cloudinary Credentials

1. **Sign up** at [cloudinary.com](https://cloudinary.com) (free tier available)
2. Go to **Settings > API Keys** in your Cloudinary dashboard
3. Copy:
   - **Cloud Name** (e.g., `dxyz123abc`)
   - **API Key** (e.g., `123456789012345`)
   - **API Secret** (e.g., `AbCdEfGhIjKlMnOpQrStUvWxYz`)

4. **For Railway Production:**
   - Go to your Railway project settings
   - Add environment variables:
     - `CLOUDINARY_CLOUD_NAME`
     - `CLOUDINARY_API_KEY`
     - `CLOUDINARY_API_SECRET`

---

## How Media Storage Works

### Image Upload Flow
```
User uploads image via Django API
    ↓
Django FileField/ImageField receives file
    ↓
cloudinary_storage.storage.MediaCloudinaryStorage intercepts
    ↓
Image uploaded to Cloudinary (not saved locally)
    ↓
Cloudinary URL stored in database
    ↓
Client receives Cloudinary URL to access image
```

### File Organization in Cloudinary
Your existing `upload_to` functions are preserved:

| Model | Path | Example |
|-------|------|---------|
| Event bride images | `events/{bride}_{groom}_{date}/bride/` | `events/ahmad_noura_2026-05-08/bride/photo.jpg` |
| Photo guest images | `events/{bride}_{groom}_{date}/guests/` | `events/ahmad_noura_2026-05-08/guests/guest1.jpg` |
| Photo generated images | `events/{bride}_{groom}_{date}/generated/` | `events/ahmad_noura_2026-05-08/generated/result.jpg` |
| Bride reference images | `bride/` | `bride/bride_photo.jpg` |

---

## Models - No Changes Required ✅

Your existing models work **without any modifications**:

### Events App
```python
# No changes needed - still uses ImageField
Event.bride_image = models.ImageField(upload_to=event_bride_upload_to, ...)
Bride.image = models.ImageField(upload_to="bride/")
```

### Photos App
```python
# No changes needed - still uses ImageField
Photo.guest_image = models.ImageField(upload_to=photo_guest_upload_to)
Photo.generated_image = models.ImageField(upload_to=photo_generated_upload_to, ...)
```

**Cloudinary storage is transparent to Django models** — they work exactly the same way.

---

## Testing Image Upload

### 1. **Local Development (Without Cloudinary)**
If `CLOUDINARY_CLOUD_NAME` is not set, the system automatically falls back to local storage:
```bash
# Install dependencies
pip install -r requirements.txt

# Run Django
python manage.py runserver

# Test uploads normally - files go to local /media/ folder
# This allows you to develop without Cloudinary credentials
```

### 2. **Local Development (With Cloudinary)**
If you want to test with Cloudinary locally:

```bash
# Add to .env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Install dependencies
pip install -r requirements.txt

# Run Django
python manage.py runserver

# Upload image via admin or API:
# POST /api/events/{event_id}/photos/
# with multipart/form-data: guest_image=<file>

# Check response - URL should be Cloudinary URL, like:
# https://res.cloudinary.com/your_cloud_name/image/upload/v1234567890/events/...
```

### 3. **Production (Railway)**
```bash
# No additional setup needed!
# Set environment variables in Railway project settings
# Deploys will automatically use Cloudinary

# Verify in logs:
# - Images upload successfully
# - Django admin displays images from Cloudinary
# - QR codes and download links work
```

### 4. **API Testing Example**

#### Upload a Photo
```bash
curl -X POST http://localhost:8000/api/events/1/photos/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "guest_image=@/path/to/image.jpg" \
  -F "style=keepsake"

# Response:
{
  "id": 42,
  "event": 1,
  "guest_image": "https://res.cloudinary.com/your_cloud/image/upload/v123/events/bride_groom_date/guests/image.jpg",
  "generated_image": null,
  "status": "pending",
  ...
}
```

#### Retrieve Photos
```bash
curl http://localhost:8000/api/events/1/photos/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Images are served from Cloudinary URLs
```

#### Django Admin
1. Navigate to `http://localhost:8000/admin`
2. Go to **Events > Event** or **Photos > Photo**
3. Upload an image via the admin form
4. Save - image is automatically uploaded to Cloudinary
5. Click the image link in admin - opens from Cloudinary CDN

---

## Verification Checklist

- [x] **Packages installed** - `cloudinary` and `django-cloudinary-storage` in requirements.txt
- [x] **Settings configured** - `INSTALLED_APPS`, `CLOUDINARY_STORAGE`, `DEFAULT_FILE_STORAGE`
- [x] **Environment variables** - Ready to configure (CLOUDINARY_CLOUD_NAME, etc.)
- [x] **Models unchanged** - No destructive migrations required
- [x] **Upload paths preserved** - Files organized in Cloudinary by event
- [x] **Fallback support** - Works without Cloudinary in development
- [x] **Admin support** - Django admin displays images from Cloudinary
- [x] **Production ready** - Environment variable configuration for Railway

---

## Development vs. Production

| Aspect | Development | Production (Railway) |
|--------|-------------|----------------------|
| Cloudinary Required? | No (optional) | Yes |
| File Storage | Local `/media/` folder (if no Cloudinary) | Cloudinary cloud |
| Environment Vars | Optional in `.env` | Required in Railway settings |
| Docker Compose | No changes needed | No changes needed |
| Database Migrations | None required | None required |
| Admin Panel | Works with local or Cloudinary images | Works with Cloudinary images |

---

## Troubleshooting

### Issue: "Could not find CLOUDINARY_CLOUD_NAME"
**Solution:** Ensure environment variable is set:
```bash
# Local development
echo 'CLOUDINARY_CLOUD_NAME=your_value' >> .env

# Railway
Go to Project > Variables, add CLOUDINARY_CLOUD_NAME
```

### Issue: Images Not Uploading
**Solution:** Check credentials and API limits:
1. Verify `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` are correct
2. Check Cloudinary dashboard for API errors
3. Ensure upload quota not exceeded (free tier has limits)

### Issue: 404 on Image URLs
**Solution:** Ensure Cloudinary is enabled and credentials are correct:
```python
# In Django shell
from django.conf import settings
print(settings.CLOUDINARY_STORAGE)
print(settings.DEFAULT_FILE_STORAGE)
```

### Issue: Mixed Storage (Some Local, Some Cloudinary)
**Solution:** This is normal during migration. To migrate existing local files to Cloudinary:
1. Download files from local `/media/`
2. Manually upload to Cloudinary in matching paths
3. Update database URLs (or delete local files once verified)

---

## Security Notes

✅ **API Keys are Environment Variables**
- Never commit `.env` file to Git
- API Secret never exposed in frontend code

✅ **CORS & CSRF Configured**
- Your existing CORS settings apply to Cloudinary URLs
- Railway SSL headers properly configured

✅ **No Local Files in Production**
- Images deleted after Railway restarts
- Cloudinary ensures durability

---

## Next Steps

1. **Get Cloudinary Account:**
   - Sign up at [cloudinary.com](https://cloudinary.com)
   - Copy your Cloud Name, API Key, API Secret

2. **Add to Railway:**
   - Go to your Railway project
   - Add environment variables for Cloudinary

3. **Test Locally:**
   - `pip install -r requirements.txt`
   - Add Cloudinary vars to `.env`
   - Run `python manage.py runserver`
   - Upload image via admin or API

4. **Deploy to Railway:**
   - Push changes to Git
   - Railway auto-deploys
   - Monitor logs for any upload errors

---

## Resources

- [Cloudinary Python SDK Documentation](https://cloudinary.com/documentation/python_reference)
- [Django Cloudinary Storage](https://github.com/klis87/django-cloudinary-storage)
- [Cloudinary Pricing & Free Tier](https://cloudinary.com/pricing)
- [Railway Environment Variables](https://docs.railway.app/guides/variables)
