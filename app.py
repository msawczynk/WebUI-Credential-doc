import subprocess
import os
import tempfile
from flask import Flask, render_template, request, session, redirect, url_for, flash
from docxtpl import DocxTemplate
import json
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
    folders_json = run_keeper_command(['--user', user, '--password', passw, 'ls', '--format=json', CUSTOMER_FOLDER])
    templates_json = run_keeper_command(['--user', user, '--password', passw, 'ls', '--format=json', TEMPLATE_FOLDER])
    if 'Error' in folders_json or 'Error' in templates_json:
        flash('Error listing folders or templates')
        folders_list = []
        templates_list = []
    else:
        folders_data = json.loads(folders_json)
        templates_data = json.loads(templates_json)
        folders_list = [{'uid': item['record_uid'], 'title': item.get('title', 'Untitled')} for item in folders_data if 'record_uid' in item]
        templates_list = [{'uid': item['record_uid'], 'title': item.get('title', 'Untitled'), 'notes': item.get('notes', '')} for item in templates_data if 'record_uid' in item]
    selected_template = request.form.get('template_uid', None) if request.method == 'POST' else None
    placeholders = []
    if selected_template:
        template = next((t for t in templates_list if t['uid'] == selected_template), None)
        if template and template['notes']:
            placeholders = [p.strip() for p in template['notes'].split(',')]
    if request.method == 'POST' and 'generate' in request.form:
        record_uid = request.form['record_uid']
        template_uid = request.form['template_uid']
        mappings = {}
        for ph in placeholders:
            field = request.form.get(f'map_{ph}', '')
            record_json = run_keeper_command(['--user', user, '--password', passw, 'get', '--format=json', record_uid])
            if 'Error' in record_json:
                flash(record_json)
                return render_template('portal.html', folders=folders_list, templates=templates_list, placeholders=placeholders, selected_template=template_uid)
            record_data = json.loads(record_json)
            value = record_data.get('custom_fields', {}).get(field, record_data.get(field, '') or '')
            mappings[ph] = value
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                template_path = os.path.join(tmpdir, 'template.docx')
                attach_result = run_keeper_command(['--user', user, '--password', passw, 'download-attachment', '--record', template_uid, '--name=template.docx', template_path])
                if 'Error' in attach_result:
                    raise ValueError(attach_result)
                doc = DocxTemplate(template_path)
                doc.render(mappings)
                output_path = os.path.join(tmpdir, 'generated.docx')
                doc.save(output_path)
                new_title = f"Generated_Doc_{record_uid}_{int(time.time())}"
                create_result = run_keeper_command(['--user', user, '--password', passw, 'create', '--record-type=general', '--folder', GENERATED_FOLDER, '--title', new_title, '--format=json'])
                if 'Error' in create_result:
                    raise ValueError(create_result)
                new_record = json.loads(create_result)
                new_uid = new_record['uid']
                upload_result = run_keeper_command(['--user', user, '--password', passw, 'upload-attachment', '--record', new_uid, '--name=generated.docx', output_path])
                if 'Error' in upload_result:
                    raise ValueError(upload_result)
                expire_minutes = {'1h': 60, '24h': 1440, '7d': 10080}.get(request.form.get('expire', '24h'), 1440)
                share_result = run_keeper_command(['--user', user, '--password', passw, 'share-record', '--record', new_uid, '--expire-in', str(expire_minutes), '--account', 'dummy@share.com'])  # Dummy sharee for link generation
                direct_link = f"https://keepersecurity.com/vault#detail/{new_uid}"
                flash(f"Document created! Share result: {share_result} Direct: {direct_link}")
        except Exception as e:
            flash(f"Error generating document: {str(e)}")
    return render_template('portal.html', folders=folders_list, templates=templates_list, placeholders=placeholders, selected_template=selected_template)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))
    user, passw = session['user'], session['pass']
    enterprise_info = run_keeper_command(['--user', user, '--password', passw, 'enterprise-info', '--format=json'])
    if 'Error' in enterprise_info:
        flash('Unable to check roles')
        return redirect(url_for('portal'))
    info = json.loads(enterprise_info)
    is_admin = any(role.get('admin', False) for role in info.get('roles', []))  # Simplified check
    if not is_admin:
        flash('Admin access required')
        return redirect(url_for('portal'))
    if request.method == 'POST':
        template_file = request.files['template']
        placeholders = request.form['placeholders']
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, 'new_template.docx')
            template_file.save(temp_path)
            new_title = f"Template_{int(time.time())}"
            create_result = run_keeper_command(['--user', user, '--password', passw, 'create', '--record-type=general', '--folder', TEMPLATE_FOLDER, '--title', new_title, '--notes', placeholders, '--format=json'])
            new_uid = json.loads(create_result)['uid']
            run_keeper_command(['--user', user, '--password', passw, 'upload-attachment', '--record', new_uid, '--name=template.docx', temp_path])
            flash('Template uploaded')
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc') 