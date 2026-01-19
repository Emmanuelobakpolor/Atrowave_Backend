# Render Deployment Guide for Atrowave Payment Gateway

## Prerequisites
1. A Render account (sign up at https://render.com)
2. Your codebase hosted on GitHub, GitLab, or Bitbucket
3. Flutterwave and Bybit API keys

## Deployment Methods

### Method 1: One-Click Deploy (Recommended)
This method uses the `render.yaml` file to deploy the entire app and database automatically.

1. Fork this repository to your GitHub account
2. Go to https://render.com/deploy?repo=https://github.com/your-username/atrowave_payment_gateway
3. Replace `your-username` with your actual GitHub username
4. Review the configuration:
   - App name: `atrowave-payment-gateway` (you can change this)
   - Region: Select your preferred region (e.g., Oregon)
5. Add your secret environment variables:
   - `FLUTTERWAVE_SECRET_KEY`: Your Flutterwave secret key
   - `BYBIT_API_KEY`: Your Bybit API key
   - `BYBIT_API_SECRET`: Your Bybit API secret
6. Click "Deploy"

### Method 2: Manual Deployment
If you prefer to configure everything manually:

#### Step 1: Deploy PostgreSQL Database
1. Go to https://dashboard.render.com/new/database
2. Configure your database:
   - Name: `atrowave-db`
   - Database Name: `payment_gateway`
   - User: `atrowave_user`
   - Plan: Select a plan (Starter plan works for testing)
   - Region: Same region as your web service
3. Click "Create Database"
4. Once created, copy the **External Database URL**

#### Step 2: Deploy Web Service
1. Go to https://dashboard.render.com/new/web
2. Connect your repository
3. Configure the web service:
   - Name: `atrowave-payment-gateway`
   - Environment: Python 3.10+
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - Start Command: `gunicorn config.wsgi:application`
   - Plan: Select a plan (Starter plan works for testing)
   - Region: Same region as your database
4. Add environment variables:
   - `DEBUG`: `false`
   - `SECRET_KEY`: Click "Generate" to create a secure secret key
   - `DATABASE_URL`: Paste the External Database URL from Step 1
   - `FLUTTERWAVE_BASE_URL`: `https://api.flutterwave.com/v3`
   - `FLUTTERWAVE_SECRET_KEY`: Your Flutterwave secret key
   - `BYBIT_BASE_URL`: `https://api.bybit.com`
   - `BYBIT_API_KEY`: Your Bybit API key
   - `BYBIT_API_SECRET`: Your Bybit API secret
5. Click "Deploy"

## Post-Deployment Steps

### 1. Create a Superuser
Once your app is deployed, you need to create a superuser to access the Django admin:

1. Go to your web service in Render dashboard
2. Click "Shell"
3. Run the command:
   ```bash
   python manage.py createsuperuser
   ```
4. Follow the prompts to create your superuser account

### 2. Test the API
- Admin panel: `https://your-app-url.onrender.com/admin/`
- API endpoints: `https://your-app-url.onrender.com/api/`

### 3. Update Your Flutter App
Update the API base URL in your Flutter app to point to your new Render backend:

In `lib/core/api/api_client.dart`:
```dart
class ApiClient {
  static const String baseUrl = 'https://your-app-url.onrender.com/api';
  // ...
}
```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `DEBUG` | Enable/disable debug mode (set to `false` in production) | Yes |
| `SECRET_KEY` | Django secret key for cryptographic operations | Yes |
| `DATABASE_URL` | PostgreSQL connection string from Render | Yes |
| `FLUTTERWAVE_BASE_URL` | Flutterwave API base URL | Yes |
| `FLUTTERWAVE_SECRET_KEY` | Flutterwave secret API key | Yes |
| `BYBIT_BASE_URL` | Bybit API base URL | Yes |
| `BYBIT_API_KEY` | Bybit API key | Yes |
| `BYBIT_API_SECRET` | Bybit API secret | Yes |

## Performance Optimization Tips

1. **Enable Database Connection Pooling**: Render automatically provides this
2. **Use Redis for Caching**: For production, consider adding a Redis instance
3. **Configure CDN**: Use Render's built-in CDN for static files
4. **Monitor Performance**: Use Render's metrics and logs to identify bottlenecks

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Ensure `DATABASE_URL` is correctly formatted
   - Verify that your web service and database are in the same region
   - Check if your IP is whitelisted (Render handles this automatically)

2. **Static Files Not Loading**:
   - Check that `collectstatic` ran successfully during deployment
   - Verify that `STATIC_ROOT` and `STATIC_URL` are correctly configured

3. **API Key Issues**:
   - Ensure all API keys are correctly entered in the environment variables
   - Check that your Flutterwave and Bybit accounts are active

### Debugging
1. View logs in Render dashboard
2. Check environment variables
3. Use `render logs` CLI command for more detailed debugging

## Updating the App
1. Push changes to your repository
2. Render will automatically deploy the new version
3. Database migrations are run automatically on each deploy

## Scaling
- Upgrade your web service plan for more resources
- Enable auto-scaling for high traffic
- Add read replicas for database scaling

## Backup and Restore
Render automatically backs up your database daily. You can restore from a backup via the dashboard.
