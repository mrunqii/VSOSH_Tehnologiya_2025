# server.py
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO
from blockchain import Blockchain
from pbft import PBFT
import os

app = Flask(__name__)
socketio = SocketIO(app)

blockchain = Blockchain()
pbft = PBFT([blockchain])

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    # Отображение главной страницы
    return render_template('index.html')

@app.route('/send_document', methods=['POST'])
def send_document():
    # Обработка запроса на отправку документа
    file = request.files['document']
    to = request.form['to']
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    data = {
        'document': filename,
        'to': to,
        'from': 'client1'  # Указываем отправителя
    }
    pbft.request(data)
    return jsonify({"status": "success"})

@app.route('/get_documents', methods=['GET'])
def get_documents():
    # Обработка запроса на получение документов
    user_id = request.args.get('user_id')
    documents = [block.data for block in blockchain.chain if isinstance(block.data, dict) and block.data.get('to') == user_id]
    return jsonify(documents)

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Обработка запроса на скачивание файла
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)