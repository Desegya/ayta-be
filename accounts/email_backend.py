"""
Custom SMTP backend for Zoho Mail that handles SSL certificate issues
"""

import ssl
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend


class ZohoEmailBackend(DjangoEmailBackend):
    """
    Custom email backend for Zoho Mail that relaxes SSL certificate verification
    """

    def open(self):
        """
        Override the open method to use relaxed SSL context
        """
        if self.connection:
            return False

        # Create SSL context with relaxed verification (like our test script)
        if self.use_ssl:
            import smtplib

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            try:
                timeout = self.timeout or 60  # Default to 60 seconds if None
                self.connection = smtplib.SMTP_SSL(
                    self.host, self.port, context=context, timeout=timeout
                )
            except OSError:
                if not self.fail_silently:
                    raise
                return False
        else:
            # Use the parent's implementation for non-SSL connections
            return super().open()

        # Login
        if self.username and self.password:
            try:
                self.connection.login(self.username, self.password)
            except smtplib.SMTPException:
                if not self.fail_silently:
                    raise
                return False

        return True
