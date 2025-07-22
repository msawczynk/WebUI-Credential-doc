import subprocess
import os
import tempfile
from flask import Flask, render_template, request, session, redirect, url_for, flash
from docxtpl import DocxTemplate
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change in production

KEEPER_CMD = 'keeper'  # Assume globally installed

# Best judgement: Folders like 'Customers/' and 'Templates/'
CUSTOMER_FOLDER = 'Customers'
TEMPLATE_FOLDER = 'Templates'
GENERATED_FOLDER = 'GeneratedDocs'

def run_keeper_command(args, input_data=None):
    try:
        result = subprocess.run([KEEPER_CMD] + args, capture_output=True, text=True, input=input_data, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('portal'))
    if request.method == 'POST':
        user = request.form['user']
        passw = request.form['pass']
        session['user'] = user
        session['pass'] = passw
        # Test login
        test = run_keeper_command(['--user', user, '--password', passw, 'whoami'])
        if 'Error' in test:
            flash('Login failed')
            return redirect(url_for('login'))
        return redirect(url_for('portal'))
    return render_template('login.html')

@app.route('/portal', methods=['GET', 'POST'])
def portal():
    if 'user' not in session:
        return redirect(url_for('login'))
    user, passw = session['user'], session['pass']
    # List customer folders: best judgement subfolders under Customers
    folders = run_keeper_command(['--user', user, '--password', passw, 'ls', '--format=json', CUSTOMER_FOLDER])
    # List templates
    templates = run_keeper_command(['--user', user, '--password', passw, 'ls', '--format=json', TEMPLATE_FOLDER])
    # Simpler UI: form to select customer record, template, fields to map
    if request.method == 'POST':
        record_uid = request.form['record_uid']  # From selected customer record
        template_uid = request.form['template_uid']
        mappings = {}  # e.g., {'placeholder': 'field_value'} from form
        for key in request.form:
            if key.startswith('map_'):
                placeholder = key[4:]
                field = request.form[key]
                # Get field value from record
                record_data = run_keeper_command(['--user', user, '--password', passw, 'get', '--format=json', record_uid])
                # Assume parse json, extract field (simplified)
                value = 'dummy_value'  # TODO: proper parsing
                mappings[placeholder] = value
        # Download template
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, 'template.docx')
            run_keeper_command(['--user', user, '--password', passw, 'download', '--record', template_uid, '--file', template_path])
            doc = DocxTemplate(template_path)
            doc.render(mappings)
            output_path = os.path.join(tmpdir, 'generated.docx')
            doc.save(output_path)
            # Create new record in GeneratedDocs
            new_title = f"Generated_Doc_{record_uid}_{int(time.time())}"
            create_cmd = run_keeper_command(['--user', user, '--password', passw, 'create', '--folder', GENERATED_FOLDER, '--title', new_title, '--format=json'])
            new_uid = 'dummy_uid'  # Parse from create_cmd
            # Upload attachment
            run_keeper_command(['--user', user, '--password', passw, 'upload', '--record', new_uid, output_path])
            # Generate share link: default 24h, adjustable
            expire = request.form.get('expire', '24h')
            share = run_keeper_command(['--user', user, '--password', passw, 'share-record', '--record', new_uid, '--one-time', f'--expire-in={expire}'])
            direct_link = f"https://keepersecurity.com/vault#detail/{new_uid}"
            flash(f"Document created! Share: {share} Direct: {direct_link}")
    return render_template('portal.html', folders=folders, templates=templates)

@app.route('/admin')
def admin():
    # Check role via whoami or enterprise command
    # Best judgement: simple form to upload templates and define placeholders, store as attachment in Templates
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 