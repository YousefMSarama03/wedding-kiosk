# Cloudinary Environment Variables for Railway

Add these variables to your Railway project:

## Required for Production (Railway)

```
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

## Steps to Add to Railway

1. Go to your Railway project dashboard
2. Click on the backend service
3. Go to **Variables** tab
4. Add three new variables:

   | Variable Name | Value |
   |---|---|
   | `CLOUDINARY_CLOUD_NAME` | Your Cloudinary Cloud Name |
   | `CLOUDINARY_API_KEY` | Your Cloudinary API Key |
   | `CLOUDINARY_API_SECRET` | Your Cloudinary API Secret |

5. **Deploy** - Railway will auto-redeploy with new variables

## How to Get Your Credentials

1. Go to [cloudinary.com](https://cloudinary.com)
2. Sign up (free tier available)
3. Log in to dashboard
4. Go to **Settings > API Keys**
5. Copy the three values shown

## For Local Development

Create a `.env` file in `/backend/` with the same variables:

```env
# .env (add to .gitignore - never commit!)
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

Then run:
```bash
cd backend
pip install -r requirements.txt
python manage.py runserver
```

## Verify Setup

### Local:
```bash
# Test upload via admin or API
curl -X POST http://localhost:8000/api/events/1/photos/ \
  -F "guest_image=@test.jpg"

# Should return Cloudinary URL:
# "guest_image": "https://res.cloudinary.com/your_cloud_name/image/upload/v123/..."
```

### Railway:
1. Check logs - no "CLOUDINARY" errors
2. Go to admin - upload image
3. Image appears and links to Cloudinary URL
4. No local `/media/` files stored

## Free Tier Limits

- Up to 25 GB of storage
- 25 GB/month bandwidth
- No time limit (free forever)
- Perfect for development and small productions

For wedding kiosk usage (hundreds of guest photos), you'll likely stay well within free tier limits.

## Troubleshooting

**Issue:** Images return 404 after upload
**Fix:** Verify environment variables are set in Railway Variables tab

**Issue:** "Invalid API key/secret"
**Fix:** Double-check credentials from Cloudinary dashboard

**Issue:** Upload slow or fails
**Fix:** Check Cloudinary API usage on dashboard for quota limits

---

See `CLOUDINARY_INTEGRATION.md` for full integration guide and testing instructions.
