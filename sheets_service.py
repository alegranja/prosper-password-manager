import json
import logging
import os
from typing import Any, List, Optional

import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build


class GoogleSheetsService:
    """Service for interacting with Google Sheets API."""

    def __init__(self, credentials_json: Optional[str] = None, spreadsheet_id: Optional[str] = None):
        """
        Initialize the Google Sheets service.
        
        Args:
            credentials_json: JSON string containing service account credentials
            spreadsheet_id: ID of the Google Sheets document
        """
        # Set up spreadsheet ID from parameter or environment variable
        self.spreadsheet_id = spreadsheet_id
        if not self.spreadsheet_id:
            self.spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID")
            if not self.spreadsheet_id:
                logging.warning("No spreadsheet ID provided")

        # Create the Google Sheets service
        self.service = self._create_sheets_service(credentials_json)
        if not self.service:
            logging.error("Failed to create Google Sheets service")

    def _create_sheets_service(self, credentials_json: Optional[str]):
        """Create and return an authorized Sheets API service instance."""
        try:
            # Tenta usar as credenciais da variável de ambiente GOOGLE_CREDENTIALS primeiro
            credentials_env = os.environ.get('GOOGLE_CREDENTIALS')
            if credentials_env:
                try:
                    credentials_info = json.loads(credentials_env)
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_info, 
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                    return build('sheets', 'v4', credentials=credentials)
                except Exception as e:
                    logging.error(f"Error using GOOGLE_CREDENTIALS env var: {e}")
            
            # Se não tiver a variável de ambiente, tenta os outros métodos
            if credentials_json:
                # Use the provided credentials JSON
                info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    info, scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                # Fallback to credentials file if specified via environment variable
                credentials_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                if credentials_file and os.path.exists(credentials_file):
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_file, scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                else:
                    # Last resort - try default credentials
                    credentials, _ = google.auth.default(
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
            
            # Build the service
            service = build('sheets', 'v4', credentials=credentials)
            return service
        except Exception as e:
            logging.error(f"Error creating Sheets service: {e}")
            return None

    def fetch_sheet_data(self, sheet_range: str = "A1:G100") -> List[List[Any]]:
        """
        Fetch data from the specified range in the Google Sheet.
        
        Args:
            sheet_range: The range to fetch (e.g., "A1:G100")
            
        Returns:
            List of rows with values
        """
        if not self.service or not self.spreadsheet_id:
            logging.error("Sheets service or spreadsheet ID not initialized")
            return []

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=sheet_range
            ).execute()
            return result.get("values", [])
        except Exception as e:
            logging.error(f"Error fetching sheet data: {e}")
            return []

    def update_cell(self, row: int, column: str, value: str) -> bool:
        """
        Update a specific cell in the Google Sheet.
        
        Args:
            row: Row number (1-based)
            column: Column letter (e.g., 'G')
            value: Value to set in the cell
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service or not self.spreadsheet_id:
            logging.error("Sheets service or spreadsheet ID not initialized")
            return False

        cell_range = f"{column}{row}"
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=cell_range,
                valueInputOption="RAW",
                body={"values": [[value]]}
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating cell {cell_range}: {e}")
            return False

    def mark_password_as_used(self, row_index: int) -> bool:
        """
        Mark a password as used by updating the 'Usada' column.
        
        Args:
            row_index: The row index (1-based) of the password to mark
            
        Returns:
            True if successful, False otherwise
        """
        # Column G is the 'Usada' column
        return self.update_cell(row_index, "G", "Sim")

    def mark_password_as_unused(self, row_index: int) -> bool:
        """
        Mark a password as unused by clearing the 'Usada' column.
        
        Args:
            row_index: The row index (1-based) of the password to mark
            
        Returns:
            True if successful, False otherwise
        """
        # Column G is the 'Usada' column
        return self.update_cell(row_index, "G", "")
