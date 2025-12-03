#!/usr/bin/env python3
"""
PhazeVPN Unified Web Portal
Integrates Email, File Storage, and Productivity Suite
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# API Endpoints
EMAIL_API = "http://15.204.11.19:5001/api/v1"
STORAGE_API = "http://15.204.11.19:5002/api/v1/storage"
PRODUCTIVITY_API = "http://15.204.11.19:5003/api/v1/productivity"

# Default user (in production, use proper auth)
DEFAULT_USER = "admin@phazevpn.duckdns.org"

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/email')
def email():
    """Email interface"""
    return render_template('email.html')

@app.route('/files')
def files():
    """File storage interface"""
    return render_template('files.html')

@app.route('/productivity')
def productivity():
    """Productivity suite interface"""
    return render_template('productivity.html')

@app.route('/calendar')
def calendar():
    """Calendar interface"""
    return render_template('calendar.html')

@app.route('/extensibility')
def extensibility():
    """Extensibility interface"""
    return render_template('extensibility.html')

# API Proxy Endpoints
@app.route('/api/email/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def email_api_proxy(endpoint):
    """Proxy email API requests"""
    url = f"{EMAIL_API}/{endpoint}"
    headers = {'X-API-Key': request.headers.get('X-API-Key', 'default-key')}
    
    if request.method == 'GET':
        response = requests.get(url, headers=headers, params=request.args)
    elif request.method == 'POST':
        response = requests.post(url, headers=headers, json=request.json)
    elif request.method == 'PUT':
        response = requests.put(url, headers=headers, json=request.json)
    elif request.method == 'DELETE':
        response = requests.delete(url, headers=headers)
    
    return jsonify(response.json()), response.status_code

@app.route('/api/storage/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def storage_api_proxy(endpoint):
    """Proxy storage API requests"""
    url = f"{STORAGE_API}/{endpoint}"
    headers = {'Authorization': request.headers.get('Authorization', 'Bearer default')}
    
    if request.method == 'GET':
        response = requests.get(url, headers=headers, params=request.args)
    elif request.method == 'POST':
        if 'file' in request.files:
            files = {'file': request.files['file']}
            data = request.form.to_dict()
            response = requests.post(url, headers=headers, files=files, data=data)
        else:
            response = requests.post(url, headers=headers, json=request.json)
    elif request.method == 'PUT':
        response = requests.put(url, headers=headers, json=request.json)
    elif request.method == 'DELETE':
        response = requests.delete(url, headers=headers)
    
    return jsonify(response.json()), response.status_code

@app.route('/api/productivity/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def productivity_api_proxy(endpoint):
    """Proxy productivity API requests"""
    url = f"{PRODUCTIVITY_API}/{endpoint}"
    headers = {'Authorization': request.headers.get('Authorization', 'Bearer default')}
    
    if request.method == 'GET':
        response = requests.get(url, headers=headers, params=request.args)
    elif request.method == 'POST':
        response = requests.post(url, headers=headers, json=request.json)
    elif request.method == 'PUT':
        response = requests.put(url, headers=headers, json=request.json)
    elif request.method == 'DELETE':
        response = requests.delete(url, headers=headers)
    
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
