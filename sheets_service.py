def _create_sheets_service(self, credentials_json: Optional[str]):
    """Create and return an authorized Sheets API service instance."""
    try:
        if credentials_json:
            # Use the provided credentials JSON
            info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(info)
        else:
            # Fallback to credentials file if specified via environment variable
            credentials_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_file and os.path.exists(credentials_file):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_file
                )
            else:
                # Last resort - try default credentials
                credentials, _ = google.auth.default()
        
        # Build the service
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        logging.error(f"Error creating Sheets service: {e}")
        return None
