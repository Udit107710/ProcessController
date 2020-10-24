from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, Flask
)
from werkzeug.utils import secure_filename
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
import os, io, base64, binascii
from werkzeug.datastructures import FileStorage

EXECUTOR_REDIS_PASSWORD='x8z0diKDAp6AxHe56TJw'
REDIS_URL = "redis://redis:6379/0"
POSTGRESQL_URL = "db+postgresql://process_app:process_app@db:5432/process_app_dev"
temp_base="/tmp/flask_uploads"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='OfFKzEMuDTDeMJVynN3T',
    DEBUG=False,
    CELERY_BROKER_URL=REDIS_URL,
    CELERY_RESULT_BACKEND=POSTGRESQL_URL,
    CELERY_ACCEPT_CONTENT=['auth'],
    CELERY_TASK_SERIALIZER = 'auth',
    RESULT_EXTENDED=True,
    SQLALCHEMY_DATABASE_URI=POSTGRESQL_URL,
    CELERY_SECURITY_KEY='/etc/ssl/private/worker.key',
    CELERY_SECURITY_CERTIFICATE='/etc/ssl/certs/worker.pem',
    CELERY_SECURITY_CERT_STORE='/etc/ssl/certs/*.cer',
    CELERY_SECURITY_DIGEST='sha256',
)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], result_backend=app.config['CELERY_RESULT_BACKEND'],
    task_serializer='auth', security_key='/etc/ssl/private/worker.key',
    security_certificate='/etc/ssl/certs/worker.pem',
    security_cert_store='/etc/ssl/certs/*.cer', accept_content=['auth']
)
celery.conf.update(app.config)
celery.setup_security()

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/test', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file_' not in request.files:
            return jsonify({'message': 'Missing data'}), 406
        file_ = request.files['file_']
        if file_.filename == '':
            return jsonify({'message': 'Missing data'}), 406
        filename = secure_filename(file_.filename)
        file_.stream.seek(0)
        data = {
            'stream': base64.b64encode(file_.read()),
            'filename': file_.filename,
            'content_type': file_.content_type,
        }
        task = resumable_executor.delay(data=data, base=temp_base)
        return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}

@app.route('/api/status/<task_id>', methods=['GET'])
def taskstatus(task_id):
    task = resumable_executor.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),
        }
    return jsonify(response)

@app.route('/api/action/<task_id>/<action>', methods=['GET'])
def taskaction(task_id, action):
    if action == 'stop':
        app.control.revoke(task_id, terminate=True, signal='SIGKILL')
        # Delete the saved content
    elif action == 'pause':
        app.control.revoke(task_id, terminate=True, signal='SIGKILL')
    elif action == 'resume':
        # Get the saved state from db and resume the file saving process
        pass

@celery.task(bind=True, trail=True, track_started=True)
def resumable_executor(self, data, base):
    stream = binascii.a2b_base64(data['stream'])
    file_ = base64.b64edecode(stream)
    file_ = io.BytesIO(file_)
    file_ = FileStorage(file_)
    file_.seek(0, os.SEEK_END)
    file_length = file_.tell()
    file_.seek(0)
    data = file_.read(1024)
    count = 0
    filename = data['stream']
    with open(base + "/" + filename, "a") as f:
        while data:
            count += 1
            f.write(data)
            self.update_status(state="PROGRESS", 
                meta={
                    'current': count*1024 , 'total': file_length
                }
            )

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': "Uploaded"}