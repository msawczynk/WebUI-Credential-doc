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

MIT License. 