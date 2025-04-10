import os
import json
import logging
from typing import List, Dict, Any, Optional
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Service for interacting with Google Sheets API."""
    
    def __init__(self, credentials_json: Optional[str] = None, spreadsheet_id: Optional[str] = None, force_demo: bool = False):
        """
        Initialize the Google Sheets service.
        
        Args:
            credentials_json: JSON string containing service account credentials
            spreadsheet_id: ID of the Google Sheets document
            force_demo: Force demo mode regardless of other parameters
        """
        self.spreadsheet_id = spreadsheet_id or os.environ.get("SPREADSHEET_ID")
        self.demo_mode = force_demo
        
        if force_demo or not self.spreadsheet_id:
            # If demo mode is forced or no spreadsheet ID is provided, operate in demo mode
            logger.warning("Running in demo mode with sample data.")
            self.demo_mode = True
            self.service = None
        else:
            try:
                self.service = self._create_sheets_service(credentials_json)
            except Exception as e:
                logger.error(f"Error creating service: {str(e)}. Falling back to demo mode.")
                self.demo_mode = True
                self.service = None
                
        self.sheet_data = {}
        # Map columns to match Google Sheets structure
        # The column_mapping is adjusted to match your spreadsheet:
        # Column A: Vendor name (Senhas : Supervisor, etc.)
        # Columns B-F: Passwords 1-5
        # Column G: Status (Usada column)
        self.column_mapping = {
            'vendor': 0,  # Column A - Vendor name
            'senha1': 1,  # Column B - Password 1
            'senha2': 2,  # Column C - Password 2
            'senha3': 3,  # Column D - Password 3
            'senha4': 4,  # Column E - Password 4
            'senha5': 5,  # Column F - Password 5
            'usada': 6,   # Column G - Status (Usada column)
        }
        
    def _create_sheets_service(self, credentials_json: Optional[str]):
        """Create and return an authorized Sheets API service instance."""
        try:
            # Try to use provided credentials first
            if credentials_json:
                try:
                    info = json.loads(credentials_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        info, scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                except json.JSONDecodeError:
                    # If it's not a JSON string, assume it's a path
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_json, scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
            else:
                # Try default credentials
                credentials, _ = google.auth.default(
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                
            return build('sheets', 'v4', credentials=credentials)
            
        except Exception as e:
            logger.error(f"Error creating Sheets service: {str(e)}")
            raise
    
    def fetch_sheet_data(self, sheet_range: str = "A1:G100") -> List[List[Any]]:
        """
        Fetch data from the specified range in the Google Sheet.
        
        Args:
            sheet_range: The range to fetch (e.g., "A1:G100")
            
        Returns:
            List of rows with values
        """
        if self.demo_mode:
            # Return sample data for demo purposes matching your spreadsheet format
            return [
                ['Vendedor', 'Senhas 1', 'Senhas 2', 'Senhas 3', 'Senhas 4', 'Senhas 5', 'Usada'],
                ['Senhas : Supervisor', '1234-78956', '1234-4569', '1234-4570', '1234-4571', '1234-4572', ''],
                ['Senhas : Vendedor da Equipe Especial', '1234-78957', '1234-78950', '1234-78951', '1234-78952', '1234-78953', ''],
                ['Senhas : Gerente', '1234-78940', '1234-78941', '1234-78942', '1234-78943', '1234-78944', ''],
                ['Senhas : Vendedor Medicamento', '1234-78980', '1234-78981', '1234-78982', '1234-78983', '1234-78984', 'Usada'],
                ['Senhas : Vendedor Alimento', '1234-78990', '1234-78991', '1234-78992', '1234-78993', '1234-78994', '']
            ]
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logger.warning("No data found in the specified sheet range")
            return values
            
        except HttpError as e:
            logger.error(f"Error fetching Google Sheet data: {str(e)}")
            raise
    
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
        if self.demo_mode:
            # In demo mode, we don't actually update the sheet, but return success
            logger.info(f"Demo mode: Would update cell {column}{row} to value '{value}'")
            return True
            
        try:
            range_name = f"{column}{row}"
            body = {
                'values': [[value]]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating Google Sheet cell: {str(e)}")
            return False
    
    def mark_password_as_used(self, row_index: int) -> bool:
        """
        Mark a password as used by updating the 'Usada' column.
        
        Args:
            row_index: The row index (1-based) of the password to mark
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.demo_mode:
                logger.info(f"Demo mode: Marking password at row {row_index} as used")
                return True
            return self.update_cell(row_index, 'G', 'Usada')
        except Exception as e:
            logger.error(f"Error marking password as used: {str(e)}")
            return False
    
    def mark_password_as_unused(self, row_index: int) -> bool:
        """
        Mark a password as unused by clearing the 'Usada' column.
        
        Args:
            row_index: The row index (1-based) of the password to mark
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.demo_mode:
                logger.info(f"Demo mode: Marking password at row {row_index} as unused")
                return True
            return self.update_cell(row_index, 'G', '')
        except Exception as e:
            logger.error(f"Error marking password as unused: {str(e)}")
            return False
