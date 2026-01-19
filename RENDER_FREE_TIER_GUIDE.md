# Render Free Tier Deployment Guide

This guide explains how to deploy your backend on Render's free tier without needing a credit card for the initial setup.

## Prerequisites
1. A Render account (sign up at https://render.com)
2. Your codebase hosted on GitHub, GitLab, or Bitbucket
3. Flutterwave and Bybit API keys

## Step 1: Push Changes to Your Repository
First, commit and push your changes to your repository:

```bash
cd payment_gateway
git add Procfile config/settings.py
git commit -m "Prepare for Render free tier deployment"
git push origin main
```

## Step 2: Deploy PostgreSQL Database (Free Tier)
1. Go to https://dashboard.render.com/new/database
2. Configure your database:
   - **Name**: `atrowave-db`
   - **Database Name**: `payment_gateway`
   - **User**: `atrowave_user`
   - **Plan**: Select **Free** (512 MB RAM, 1 GB storage)
   - **Region**: Select your preferred region (e.g., Oregon)
3. Click "Create Database"
4. Wait for the database to be provisioned (this takes a few minutes)
5. Once created, copy the **External Database URL**

## Step 3: Deploy Web Service (Free Tier)
1. Go to https://dashboard.render.com/new/web
2. Connect your repository
3. Configure the web service:
   - **Name**: `atrowave-payment-gateway`
   - **Environment**: Python 3.10+
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `gunicorn config.wsgi:application`
   - **Plan**: Select **Free** (512 MB RAM, 100 GB bandwidth)
   - **Region**: Same region as your database
4. Add environment variables:
   - `DEBUG`: `false`
   - `SECRET_KEY`: Click "Generate" to create a secure secret key
   - `DATABASE_URL`: Paste the External Database URL from Step 2
   - `FLUTTERWAVE_BASE_URL`: `https://api.flutterwave.com/v3`
   - `FLUTTERWAVE_SECRET_KEY`: Your Flutterwave secret key
   - `BYBIT_BASE_URL`: `https://api.bybit.com`
   - `BYBIT_API_KEY`: Your Bybit API key
   - `BYBIT_API_SECRET`: Your Bybit API secret
5. Click "Deploy"

## Step 4: Create a Superuser
1. After deployment is complete, click on your web service
2. Click "Shell" in the top right corner
3. Run the command:
   ```bash
   python manage.py createsuperuser
   ```
4. Follow the prompts to create your admin account

## Step 5: Verify Deployment
1. Click on your web service to see the external URL (e.g., `https://atrowave-payment-gateway.onrender.com`)
2. Test the admin panel: `https://your-app-url.onrender.com/admin/`
3. Log in with the superuser credentials you created

## Step 6: Update Your Flutter App
1. In your Flutter app, open `lib/core/api/api_client.dart`
2. Update the base URL:
   ```dart
   class ApiClient {
     static const String baseUrl = 'https://your-app-url.onrender.com/api';
     // ...
   }
   ```
3. Replace `your-app-url` with your actual Render URL

## Step 7: Test the API
1. Use tools like Postman or curl to test your API endpoints
2. Test endpoints like:
   - `GET /api/users/`
   - `POST /api/auth/login/`
3. Make sure all endpoints are responding correctly

## Free Tier Limitations
- **Web Service**: 512 MB RAM, 100 GB bandwidth, auto-shuts down after 15 minutes of inactivity
- **Database**: 512 MB RAM, 1 GB storage, no backup
- **No Custom Domains**: Use the `onrender.com` domain
- **Deploy Time Limits**: Builds must complete within 15 minutes
- **No Auto-Scaling**: Manual scaling only

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Ensure `DATABASE_URL` is correctly formatted
   - Verify that your web service and database are in the same region
   - Check if your database is fully provisioned

2. **Build Timeouts**:
   - The free tier has a 15-minute build timeout
   - If your build fails, try optimizing dependencies or splitting tasks

3. **App Crashes**:
   - Check the **Logs** tab for error messages
   - Verify all environment variables are correctly set
   - Check if your database connection is working

### Debugging
1. View logs in the Render dashboard
2. Use the "Shell" to run debug commands
3. Check the "Metrics" tab for performance information

## Updating the App
1. Push changes to your repository
2. Render will automatically deploy the new version
3. Database migrations are run automatically on each deploy

## Important Notes
- The free tier is intended for testing and development, not production
- For production use, consider upgrading to a paid plan
- Free apps are automatically deleted if unused for 30 days

Your backend is now live on Render's free tier! The setup includes automatic database provisioning, SSL certificates, and production-ready configuration.
