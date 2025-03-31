import os
import json

# Configurar as variáveis de ambiente para Google Sheets
os.environ["GOOGLE_SPREADSHEET_ID"] = "1qLGNAkAVFzAcxQhfFgBzRBfIbDXFrTNFsNA_lTeSZeE"
# Ativar o modo de demonstração para garantir o funcionamento do sistema
os.environ["FORCE_DEMO"] = "true"  

# Tentar carregar credenciais do arquivo credentials.json se necessário no futuro
try:
    if os.path.exists("credentials.json"):
        with open("credentials.json", "r") as f:
            credentials_content = f.read()
            os.environ["GOOGLE_CREDENTIALS"] = credentials_content
    elif os.path.exists("attached_assets/senha-guest-454313-2a95180ad1cb.json"):
        with open("attached_assets/senha-guest-454313-2a95180ad1cb.json", "r") as f:
            credentials_content = f.read()
            os.environ["GOOGLE_CREDENTIALS"] = credentials_content
except Exception as e:
    print(f"Aviso: credenciais não carregadas: {e}")
    print("Usando modo de demonstração para funcionamento do sistema.")

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
