import os
import logging
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from sheets_service import GoogleSheetsService
from password_manager import PasswordManager
from typebot_service import TypebotService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize services
# Get the credentials from environment variable or file
credentials_json = None

# Tenta obter credenciais da variável de ambiente GOOGLE_CREDENTIALS primeiro
if os.environ.get("GOOGLE_CREDENTIALS"):
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
    logger.info("Using Google credentials from GOOGLE_CREDENTIALS environment variable")
# Depois tenta GOOGLE_SHEETS_CREDENTIALS (nome usado anteriormente)
elif os.environ.get("GOOGLE_SHEETS_CREDENTIALS"):
    credentials_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    logger.info("Using Google credentials from GOOGLE_SHEETS_CREDENTIALS environment variable")
# Finalmente, tenta carregar do arquivo
else:
    # Tentar primeiro o novo arquivo de credenciais
    credential_path = "credentials.json"
    if os.path.exists(credential_path):
        try:
            logger.info(f"Using Google credentials from file: {credential_path}")
            credentials_json = credential_path  # Passando o caminho do arquivo diretamente
        except Exception as e:
            logger.error(f"Error reading credentials file: {str(e)}")
    # Se não encontrar, tenta o arquivo original
    elif os.path.exists("attached_assets/senha-guest-454313-2a95180ad1cb.json"):
        try:
            credential_path = "attached_assets/senha-guest-454313-2a95180ad1cb.json"
            logger.info(f"Using Google credentials from file: {credential_path}")
            credentials_json = credential_path  # Passando o caminho do arquivo diretamente
        except Exception as e:
            logger.error(f"Error reading credentials file: {str(e)}")

# Extract spreadsheet ID from the environment or use default
spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID") or os.environ.get("GOOGLE_SHEETS_ID", "1qLGNAkAVFzAcxQhfFgBzRBfIbDXFrTNFsNA_lTeSZeE")
logger.info(f"Using spreadsheet ID: {spreadsheet_id}")

# Verificar configuração do modo de demonstração
# Definir como True para garantir o funcionamento do sistema sem credenciais
force_demo = os.environ.get("FORCE_DEMO", "true").lower() == "true"

# Inicializar o serviço do Google Sheets
# Usando o modo de demonstração para garantir o funcionamento
sheets_service = GoogleSheetsService(
    credentials_json=credentials_json,
    spreadsheet_id=spreadsheet_id,
    force_demo=force_demo
)

logger.info(f"Google Sheets service initialized. Demo mode: {sheets_service.demo_mode}")

password_manager = PasswordManager(sheets_service)
typebot_service = TypebotService()

@app.route('/')
def index():
    """Display the main dashboard."""
    try:
        password_stats = password_manager.get_password_statistics()
        
        # Adicionar logs para depuração
        logger.debug(f"Stats returned: {password_stats}")
        
        # Garantir que temos a estrutura correta
        if isinstance(password_stats, dict) and 'vendors' not in password_stats:
            password_stats['vendors'] = {}
            
        return render_template('index.html', stats=password_stats)
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        
        # Fornecer um objeto stats vazio mas com a estrutura correta
        empty_stats = {
            'total_passwords': 0,
            'available_passwords': 0,
            'used_passwords': 0,
            'vendors': {}
        }
        return render_template('index.html', stats=empty_stats)
        
@app.route('/typebot-guide')
def typebot_guide():
    """Display the typebot integration guide."""
    return render_template('typebot_guide.html')

@app.route('/api/get-password', methods=['POST'])
def get_password():
    """API endpoint to get the next available password for a vendor."""
    try:
        data = request.json
        vendor = data.get('vendor')
        user_id = data.get('user_id')
        phone_number = data.get('phone_number')
        
        if not vendor:
            return jsonify({"error": "Vendor parameter is required"}), 400
            
        # Use the auto-assign functionality to get the next password
        # If phone_number is provided, we'll attempt to send an SMS
        password_data = password_manager.auto_assign_next_password(vendor, phone_number)
        
        if password_data:
            # Log usage
            logger.info(f"Password automatically assigned: Vendor={vendor}, User ID={user_id}, Phone={phone_number}")
            
            # Add SMS status to the response if a phone number was provided
            if phone_number:
                sms_status = password_data.get('sms_sent', False)
                if sms_status:
                    password_data['sms_status'] = "sent"
                else:
                    password_data['sms_status'] = "failed"
                    
            return jsonify(password_data)
        else:
            return jsonify({"error": f"No available passwords for vendor: {vendor}"}), 404
            
    except Exception as e:
        logger.error(f"Error in get_password: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync-typebot', methods=['POST'])
def sync_typebot():
    """Webhook to sync with Typebot when a password is requested."""
    try:
        data = request.json
        result = typebot_service.process_webhook(data, password_manager)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in typebot sync: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/typebot-webhook', methods=['POST'])
def typebot_webhook():
    """Webhook para integração com Typebot."""
    try:
        data = request.json
        result = typebot_service.process_webhook(data, password_manager)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in typebot webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Admin endpoint to mark a password as unused again."""
    try:
        data = request.json
        vendor = data.get('vendor')
        password = data.get('password')
        
        if not vendor or not password:
            return jsonify({"error": "Vendor and password parameters are required"}), 400
            
        success = password_manager.reset_password(vendor, password)
        
        if success:
            return jsonify({"status": "success", "message": "Password reset to unused"})
        else:
            return jsonify({"error": "Password not found or could not be reset"}), 404
            
    except Exception as e:
        logger.error(f"Error in reset_password: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/refresh-sheet', methods=['POST'])
def refresh_sheet():
    """Force refresh the sheet data from Google Sheets."""
    try:
        password_manager.refresh_data()
        return jsonify({"status": "success", "message": "Sheet data refreshed"})
    except Exception as e:
        logger.error(f"Error refreshing sheet: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error="Internal server error"), 500
