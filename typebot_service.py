import logging
from typing import Dict, Any
from password_manager import PasswordManager

logger = logging.getLogger(__name__)

class TypebotService:
    """Service for integrating with Typebot."""
    
    def __init__(self):
        """Initialize the Typebot service."""
        pass
    
    def process_webhook(self, data: Dict[str, Any], password_manager: PasswordManager) -> Dict[str, Any]:
        """
        Process a webhook request from Typebot.
        
        Args:
            data: The webhook payload from Typebot
            password_manager: The password manager instance
            
        Returns:
            Response data to send back to Typebot
        """
        try:
            # Extract data from Typebot webhook
            if not data:
                return {"error": "No data provided"}
                
            # Extract vendor information - this should match what Typebot sends
            vendor = data.get('vendor')
            user_id = data.get('userId', 'unknown')
            phone_number = data.get('phoneNumber')
            
            if not vendor:
                return {"error": "No vendor specified"}
                
            # Automatically assign the next password, with optional SMS delivery
            password_data = password_manager.auto_assign_next_password(vendor, phone_number)
            
            # Verificar se há senhas disponíveis
            if not password_data:
                return {
                    "success": False,
                    "message": f"Todas as senhas para {vendor} já foram utilizadas. Por favor, contate o administrador.",
                    "has_password": False
                }
            
            # Create the response
            response = {
                "success": True,
                "vendor": password_data["vendor"],
                "password": password_data["password"],
                "has_password": True,
                "message": f"Senha para {password_data['vendor']} enviada com sucesso!"
            }
            
            # If phone number was provided, include SMS status in response
            if phone_number:
                sms_sent = password_data.get('sms_sent', False)
                if sms_sent:
                    response["sms_status"] = "sent"
                    response["message"] += f" SMS enviado para {phone_number}."
                else:
                    response["sms_status"] = "failed"
                    # Only mention SMS failure if Twilio is properly configured
                    if password_manager.twilio_service.is_configured():
                        response["message"] += f" Falha ao enviar SMS para {phone_number}."
                
            # Format response for Typebot
            return response
            
        except Exception as e:
            logger.error(f"Error processing Typebot webhook: {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao processar solicitação: {str(e)}",
                "has_password": False
            }
