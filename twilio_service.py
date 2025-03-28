import os
import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

class TwilioService:
    """Service for sending SMS messages via Twilio."""
    
    def __init__(self):
        """Initialize the Twilio service with credentials from environment variables."""
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_phone = os.environ.get("TWILIO_PHONE_NUMBER")
        self.client = None
        
        # Check if Twilio is configured
        if self.account_sid and self.auth_token and self.from_phone:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio service initialized")
        else:
            logger.warning("Twilio service not fully configured. SMS functionality will be disabled.")
    
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return self.client is not None
    
    def send_sms(self, to_phone: str, message: str) -> Optional[str]:
        """
        Send an SMS message using Twilio.
        
        Args:
            to_phone: The recipient's phone number
            message: The message content
            
        Returns:
            Message SID if successful, None if failed
        """
        if not self.is_configured():
            logger.error("Twilio is not configured. Cannot send SMS.")
            return None
            
        try:
            # Format the phone number with + if not present
            if not to_phone.startswith('+'):
                to_phone = f"+{to_phone}"
                
            message = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=to_phone
            )
            logger.info(f"SMS sent successfully. SID: {message.sid}")
            return message.sid
        except TwilioRestException as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {str(e)}")
            return None