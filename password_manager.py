import logging
from typing import Dict, Any, List, Optional, Tuple
from sheets_service import GoogleSheetsService
from twilio_service import TwilioService

logger = logging.getLogger(__name__)

class PasswordManager:
    """Manager for handling password operations."""
    
    def __init__(self, sheets_service: GoogleSheetsService, twilio_service: Optional[TwilioService] = None):
        """
        Initialize the password manager.
        
        Args:
            sheets_service: Google Sheets service instance
            twilio_service: Optional Twilio service for sending SMS
        """
        self.sheets_service = sheets_service
        self.twilio_service = twilio_service or TwilioService()
        self.password_data = []
        self.vendor_map = {}
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh password data from Google Sheets."""
        try:
            data = self.sheets_service.fetch_sheet_data()
            self.password_data = data
            
            # Build vendor map for faster lookups - agora armazenaremos uma lista de índices por vendor
            self.vendor_map = {}
            for i, row in enumerate(data):
                if i == 0:  # Skip header row
                    continue
                    
                if len(row) > 0:
                    vendor = row[0]
                    vendor_key = vendor.lower()
                    
                    if vendor_key not in self.vendor_map:
                        self.vendor_map[vendor_key] = []
                        
                    # Adicionar o índice desta linha ao mapa do vendor
                    self.vendor_map[vendor_key].append(i)
                    
            logger.debug(f"Refreshed password data. Found {len(self.vendor_map)} unique vendor entries.")
            
        except Exception as e:
            logger.error(f"Error refreshing password data: {str(e)}")
            # Em vez de propagar a exceção, inicializa com dados vazios
            self.password_data = []
            self.vendor_map = {}
            logger.warning("Inicializado com dados vazios devido a erro de credenciais ou acesso à planilha.")
    
    def get_next_password(self, vendor: str) -> Optional[Dict[str, Any]]:
        """
        Get the next available password for a vendor and mark it as used.
        
        Args:
            vendor: The vendor name to get a password for
            
        Returns:
            Dictionary with password info or None if no passwords available
        """
        vendor = vendor.lower()
        
        try:
            # Find vendor rows
            row_indices = self.vendor_map.get(vendor)
            if not row_indices:
                logger.warning(f"Vendor not found: {vendor}")
                return None
            
            # Procurar a primeira senha não usada deste vendor
            for row_index in row_indices:
                # Get the row data
                row = self.password_data[row_index]
                
                # Find the first unused password in any of the 5 password columns
                password_index = None
                password_value = None
                
                # Check if the row has the "Usada" column (Column G) and if it's already marked as used
                is_used = len(row) > 6 and row[6] == "Usada"
                
                if not is_used:
                    # Check each password column (B through F) for an available password
                    for i in range(1, 6):  # Columns B through F (indices 1-5)
                        if len(row) > i and row[i] and row[i].strip():
                            password_index = i
                            password_value = row[i]
                            break
                            
                if password_index is not None:
                    # Mark as used
                    self.sheets_service.mark_password_as_used(row_index + 1)  # +1 for 1-based row index
                    
                    # Update our local data
                    if len(row) <= 6:
                        # Extend row if needed
                        row.extend([''] * (7 - len(row)))
                    row[6] = "Usada"
                    
                    # Log that we're automatically sending this password
                    logger.info(f"Automatically sending password '{password_value}' for vendor '{row[0]}'")
                    
                    return {
                        "vendor": row[0],
                        "password": password_value,
                        "password_number": password_index,
                        "row_index": row_index + 1
                    }
            
            # Se chegou aqui, não encontrou nenhuma senha disponível
            logger.warning(f"No available passwords for vendor: {vendor}")
            return None
                
        except Exception as e:
            logger.error(f"Error getting next password for {vendor}: {str(e)}")
            return None
            
    def send_password_by_sms(self, phone_number: str, vendor: str, password: str) -> bool:
        """
        Send a password via SMS using Twilio.
        
        Args:
            phone_number: The phone number to send the SMS to
            vendor: The vendor name for the password
            password: The password to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.twilio_service.is_configured():
            logger.warning("Twilio not configured. Cannot send SMS.")
            return False
            
        try:
            message = f"Olá! Sua senha para {vendor} é: {password}"
            sid = self.twilio_service.send_sms(phone_number, message)
            
            if sid:
                logger.info(f"SMS sent successfully to {phone_number} for {vendor}")
                return True
            else:
                logger.error(f"Failed to send SMS to {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return False
            
    def auto_assign_next_password(self, vendor: str, phone_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Automatically assign and send the next available password for a vendor.
        This method gets the next password and marks the current one as used.
        
        Args:
            vendor: The vendor name to get a password for
            phone_number: Optional phone number to send the password via SMS
            
        Returns:
            Dictionary with password info or None if no passwords available
        """
        # Get the next password
        password_data = self.get_next_password(vendor)
        
        if password_data:
            # We've successfully assigned a password
            
            # If phone number is provided and Twilio is configured, send SMS
            if phone_number and self.twilio_service.is_configured():
                sms_sent = self.send_password_by_sms(
                    phone_number, 
                    password_data['vendor'], 
                    password_data['password']
                )
                password_data['sms_sent'] = sms_sent
            
            logger.info(f"Auto-assigned password: {password_data['password']} for vendor: {vendor}")
            
            # Refresh data to ensure we have the latest state
            self.refresh_data()
            
            return password_data
        else:
            logger.warning(f"No available passwords to auto-assign for vendor: {vendor}")
            return None
    
    def reset_password(self, vendor: str, password: str) -> bool:
        """
        Reset a password to unused status.
        
        Args:
            vendor: The vendor name
            password: The password value to reset
            
        Returns:
            True if successful, False otherwise
        """
        vendor = vendor.lower()
        
        try:
            # Find vendor rows
            row_indices = self.vendor_map.get(vendor)
            if not row_indices:
                logger.warning(f"Vendor not found: {vendor}")
                return False
            
            # Procurar a senha específica nas linhas deste vendor
            for row_index in row_indices:
                # Get the row data
                row = self.password_data[row_index]
                
                # Check if this password exists in any of the 5 password columns
                password_exists = False
                for i in range(1, 6):  # Columns B through F (indices 1-5)
                    if len(row) > i and row[i] == password:
                        password_exists = True
                        break
                
                if password_exists:
                    # Mark as unused
                    result = self.sheets_service.mark_password_as_unused(row_index + 1)
                    
                    # Update our local data
                    if result and len(row) > 6:
                        row[6] = ""
                        
                    logger.info(f"Reset password '{password}' for vendor '{row[0]}'")
                    return result
            
            # Se chegou aqui, não encontrou a senha
            logger.warning(f"Password {password} not found for vendor {vendor}")
            return False
            
        except Exception as e:
            logger.error(f"Error resetting password for {vendor}: {str(e)}")
            return False
    
    def get_password_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about password usage.
        
        Returns:
            Dictionary with password statistics
        """
        try:
            # Usar um conjunto para contar fornecedores únicos
            unique_vendors = set()
            available_passwords = 0
            used_passwords = 0
            
            vendor_stats = {}
            
            for i, row in enumerate(self.password_data):
                if i == 0:  # Skip header row
                    continue
                    
                if len(row) == 0:
                    continue
                    
                vendor = row[0]
                unique_vendors.add(vendor)
                is_used = len(row) > 6 and row[6] == "Usada"
                
                # Inicializar o dicionário de estatísticas do fornecedor se for a primeira vez
                if vendor not in vendor_stats:
                    vendor_stats[vendor] = {
                        "total_passwords": 0,
                        "available_passwords": 0,
                        "used_passwords": 0
                    }
                
                # Conta quantas senhas existem nessa linha (entre colunas B e F)
                password_count = 0
                for i in range(1, 6):  # Columns B through F (indices 1-5)
                    if len(row) > i and row[i] and row[i].strip():
                        password_count += 1
                
                # Atualiza as estatísticas
                if password_count > 0:
                    if is_used:
                        vendor_stats[vendor]["used_passwords"] += 1
                        used_passwords += 1
                    else:
                        vendor_stats[vendor]["available_passwords"] += 1
                        available_passwords += 1
                    
                    vendor_stats[vendor]["total_passwords"] += 1
            
            stats = {
                "total_vendors": len(unique_vendors),
                "total_passwords": available_passwords + used_passwords,
                "available_passwords": available_passwords,
                "used_passwords": used_passwords,
                "vendor_stats": vendor_stats,
                "vendors": vendor_stats  # Duplicado para compatibilidade com o template
            }
            
            # Log das estatísticas para depuração
            logger.debug(f"Calculated statistics: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting password statistics: {str(e)}")
            return {
                "total_vendors": 0,
                "total_passwords": 0,
                "available_passwords": 0,
                "used_passwords": 0,
                "vendor_stats": {},
                "vendors": {}  # Duplicado para compatibilidade com o template
            }
