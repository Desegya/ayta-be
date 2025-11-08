#!/bin/bash

# ZeptoMail API Test Script
# This script tests the ZeptoMail API directly using curl

echo "Testing ZeptoMail API..."
echo "========================"

# ZeptoMail configuration
API_URL="https://api.zeptomail.com/v1.1/email"
API_KEY="wSsVR6128hH2D699lWL8ILs7yghXAAmkHUwv2lWgvyStSKvGocczwk3HAlOhHfMaGWdhRTcU9ekvzhwGgztbjIgry1AHXSiF9mqRe1U4J3x17qnvhDzDWG5akxuJKIgJwg1qn2JkFcsq+g=="
FROM_EMAIL="noreply@ayta.com.ng"
TO_EMAIL="info@ayta.com.ng"

echo "Sending test email via ZeptoMail API..."
echo "From: $FROM_EMAIL"
echo "To: $TO_EMAIL"
echo ""

# Send test email
curl "$API_URL" \
    -X POST \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Zoho-enczapikey $API_KEY" \
    -d '{
        "from": {"address": "'$FROM_EMAIL'", "name": "AyTa"},
        "to": [{"email_address": {"address": "'$TO_EMAIL'", "name": "AyTa Team"}}],
        "subject": "ZeptoMail API Test - Success!",
        "htmlbody": "<div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;\"><h2 style=\"color: #333;\">ZeptoMail Integration Test</h2><p>This email was sent successfully using the ZeptoMail REST API!</p><div style=\"background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;\"><h3>Configuration Details:</h3><ul><li><strong>Domain:</strong> ayta.com.ng</li><li><strong>Host:</strong> api.zeptomail.com</li><li><strong>From:</strong> '$FROM_EMAIL'</li><li><strong>Method:</strong> REST API</li></ul></div><p>If you received this email, your ZeptoMail integration is working correctly!</p><p>Best regards,<br>The AyTa Team</p></div>",
        "textbody": "ZeptoMail Integration Test - This email was sent successfully using the ZeptoMail REST API! If you received this email, your ZeptoMail integration is working correctly."
    }' \
    --write-out "\n\nHTTP Status: %{http_code}\n" \
    --show-error \
    --fail

echo ""
echo "Test completed!"
echo "If you see HTTP Status: 200, the test was successful."
echo "Check your inbox at $TO_EMAIL for the test email."