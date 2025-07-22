                            # Keeper WebUI Credential Doc

This is a lightweight local web portal for interacting with Keeper Commander CLI to manage templates, generate documents, and share them from your Keeper Vault.

## Setup
1. Install Python 3 and Keeper Commander CLI globally.
2. Run `pip install -r requirements.txt`
3. Launch with `python app.py` or the provided run.bat.
4. Access at http://localhost:5000

## Features
- Simple login (email/password, no SSO).
- View customer folders and templates from Vault.
- Select records, fill templates, create new Vault records with attachments.
- Generate one-time share links (default 24h, adjustable).
- Admin configurator based on roles.

## User Guide

1. **Launch the App**: Run `python app.py` or double-click `run.bat` on Windows. Access the portal at https://localhost:5000 (accept self-signed cert warning).
2. **Login**: Enter your Keeper email and password. The app uses Keeper CLI to authenticate.
3. **Portal**:
   - Select a customer record from the dropdown (from 'Customers/' folder).
   - Select a template from the dropdown (from 'Templates/' folder).
   - Click "Load Placeholders" to display mapping fields.
   - Map each placeholder to a field from the record (e.g., 'username', 'custom_field_name').
   - Choose expiration for share link.
   - Click "Generate Document" to fill the template, create a new Vault record in 'GeneratedDocs/', upload the doc, and get share/direct links.
4. **Logout**: Click the logout link to end the session.

## Admin Guide

Admins (detected via Keeper roles) can access the configurator:
1. **Access Admin**: From the portal, click "Admin".
2. **Upload Template**:
   - Choose a .docx file with placeholders (e.g., {{name}}).
   - Enter comma-separated placeholders (e.g., name,email).
   - Submit to create a new record in 'Templates/' with the doc attached and placeholders in notes.
3. **Manage Roles**: Use Keeper Vault to assign enterprise roles for admin access.

Note: Ensure folders exist in your Vault. For multi-language, select language in settings (supports en, de).

MIT License (matching Keeper Commander). 