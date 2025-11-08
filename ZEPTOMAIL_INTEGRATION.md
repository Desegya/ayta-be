# ZeptoMail Integration for AyTa

This document describes the ZeptoMail transactional email integration for the AyTa backend.

## Overview

We've switched from SMTP-based email sending to ZeptoMail's REST API for improved reliability and deliverability. ZeptoMail is Zoho's transactional email service that provides better performance and detailed analytics.

## Configuration

### Environment Variables

Add these environment variables to your `.env` file or deployment environment:

```bash
# ZeptoMail Configuration
ZEPTOMAIL_API_KEY=wSsVR6128hH2D699lWL8ILs7yghXAAmkHUwv2lWgvyStSKvGocczwk3HAlOhHfMaGWdhRTcU9ekvzhwGgztbjIgry1AHXSiF9mqRe1U4J3x17qnvhDzDWG5akxuJKIgJwg1qn2JkFcsq+g==
ZEPTOMAIL_FROM_EMAIL=noreply@ayta.com.ng
ZEPTOMAIL_FROM_NAME=AyTa
```

### ZeptoMail Settings

- **Domain**: ayta.com.ng
- **Host**: api.zeptomail.com
- **Mail Agent Alias**: 515b18625d6554c7
- **API Endpoint**: https://api.zeptomail.com/v1.1/email

## Implementation Details

### 1. Email Backend

**File**: `accounts/zeptomail_backend.py`

Custom Django email backend that uses ZeptoMail's REST API instead of SMTP. This backend:

- Handles both HTML and text email content
- Supports multiple recipients (TO, CC)
- Provides proper error handling and logging
- Integrates seamlessly with Django's email system

### 2. Utility Functions

**File**: `accounts/zeptomail_utils.py`

Direct ZeptoMail API functions:

- `send_email_via_zeptomail()` - Send single email
- `send_bulk_email_via_zeptomail()` - Send to multiple recipients
- `test_zeptomail_connection()` - Test API connectivity

### 3. Updated Email Functions

**Files Updated**:

- `accounts/email_utils.py` - User onboarding emails
- `food/email_utils.py` - Order receipts and status updates
- `accounts/views.py` - Password reset emails

All email functions now use ZeptoMail for sending.

## Testing

### 1. Direct API Test (curl)

```bash
./test_zeptomail_curl.sh
```

### 2. Python Test Script

```bash
python test_zeptomail.py
```

### 3. Django Management Command

```bash
# Basic test
python manage.py test_zeptomail --test-type=basic

# Onboarding email test
python manage.py test_zeptomail --test-type=onboarding --email=test@example.com

# All tests
python manage.py test_zeptomail --test-type=all --email=test@example.com
```

### 4. Manual API Test

```bash
curl "https://api.zeptomail.com/v1.1/email" \
    -X POST \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Zoho-enczapikey YOUR_API_KEY" \
    -d '{
        "from": {"address": "noreply@ayta.com.ng", "name": "AyTa"},
        "to": [{"email_address": {"address": "test@example.com", "name": "Test User"}}],
        "subject": "Test Email",
        "htmlbody": "<div><b>Test email sent successfully.</b></div>"
    }'
```

## Email Types Supported

### 1. Onboarding Emails

- Welcome new users
- Uses HTML templates from `templates/emails/onboarding_welcome.html`

### 2. Order Emails

- Order confirmations
- Status updates (pending, paid, delivered, etc.)
- Uses templates from `templates/emails/order_receipt.html`

### 3. Password Reset

- OTP codes for password reset
- Uses template from `templates/emails/password_reset_otp.html`

## Migration from SMTP

### What Changed

1. **Email Backend**: Changed from `accounts.email_backend.ZohoEmailBackend` to `accounts.zeptomail_backend.ZeptoMailBackend`

2. **Settings**: Updated `ayta/settings.py` to use ZeptoMail configuration

3. **Direct Email Functions**: Updated utility functions to use REST API instead of SMTP

### Backwards Compatibility

- Django's `send_mail()` function still works through the new backend
- All existing email templates are compatible
- Environment variables for SMTP are kept for compatibility but not used

## Advantages of ZeptoMail

1. **Reliability**: REST API is more reliable than SMTP
2. **Performance**: Faster email delivery
3. **Analytics**: Detailed sending and delivery statistics
4. **No SSL Issues**: Eliminates SMTP SSL certificate problems
5. **Scalability**: Better handling of high-volume email sending
6. **Deliverability**: Improved inbox delivery rates

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check API key is correct
2. **Invalid Domain**: Ensure `ayta.com.ng` is verified in ZeptoMail
3. **Rate Limits**: ZeptoMail has sending limits based on plan

### Debugging

Enable debug logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'accounts.zeptomail_backend': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'accounts.zeptomail_utils': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Logs Location

- Email sending logs: Check Django logs for ZeptoMail backend messages
- API responses: Logged with details for debugging

## API Rate Limits

ZeptoMail has the following limits:

- **Free Plan**: 10,000 emails/month
- **Paid Plans**: Higher limits based on subscription

Monitor usage in the ZeptoMail dashboard.

## Security

- API key is stored in environment variables
- All API calls use HTTPS
- No credentials stored in code
- API key has limited permissions (send-only)

## Support

For issues with ZeptoMail integration:

1. Check the test scripts first
2. Verify environment variables
3. Check ZeptoMail dashboard for delivery status
4. Review Django logs for error details
