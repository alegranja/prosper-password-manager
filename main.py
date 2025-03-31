import os
import json

# Configurar as variáveis de ambiente para Google Sheets
os.environ["GOOGLE_SPREADSHEET_ID"] = "1qLGNAkAVFzAcxQhfFgBzRBfIbDXFrTNFsNA_lTeSZeE"
os.environ["FORCE_DEMO"] = "false"  # Desativar modo de demonstração

# Tentar carregar credenciais do arquivo credentials.json
try:
    with open("credentials.json", "r") as f:
        credentials_content = f.read()
        os.environ["GOOGLE_CREDENTIALS"] = credentials_content
except Exception as e:
    print(f"Erro ao carregar credentials.json: {e}")

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
