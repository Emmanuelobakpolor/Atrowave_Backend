# Deployment Checklist

## Pre-Deployment

- [ ] Repository is public or Render has access to it
- [ ] `render.yaml` file exists and is configured
- [ ] `Procfile` exists and is correctly configured
- [ ] `requirements.txt` includes all necessary packages
- [ ] `settings.py` is configured for Render deployment
- [ ] All sensitive information is removed from the codebase

## Environment Variables

- [ ] `DEBUG` is set to `false` in production
- [ ] `SECRET_KEY` is a secure random string
- [ ] `DATABASE_URL` is correctly formatted
- [ ] Flutterwave API keys are valid
- [ ] Bybit API keys are valid
- [ ] Email configuration is set (optional)

## Database Configuration

- [ ] PostgreSQL database is created on Render
- [ ] Database user has appropriate permissions
- [ ] Connection string is correctly formatted
- [ ] SSL connection is enabled

## Static Files

- [ ] `STATIC_ROOT` is configured correctly
- [ ] `collectstatic` command works
- [ ] Static files are being served correctly

## App Configuration

- [ ] All required Django apps are installed
- [ ] CORS settings are configured for your domain
- [ ] Allowlist includes your app's domain
- [ ] Middleware is correctly configured

## Testing

- [ ] All migrations are applied
- [ ] Superuser account is created
- [ ] API endpoints are accessible
- [ ] Admin panel is working
- [ ] Webhooks are configured

## Performance

- [ ] Database connection pooling is enabled
- [ ] Static files are compressed
- [ ] Caching is configured (optional)
- [ ] Logging is configured

## Security

- [ ] Debug mode is disabled
- [ ] Secret key is secure
- [ ] CORS settings are restrictive
- [ ] SSL is enabled
- [ ] CSRF protection is enabled
