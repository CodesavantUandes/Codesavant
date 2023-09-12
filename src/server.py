from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/process-file', methods=['POST'])

def process_file():

    data = request.json
    file_content = data.get('content')
    print(file_content)

    return jsonify(
        {
            'message': 'Archivo procesado correctamente',
            'fileReturn': 'Aqui va el archivo de python'
            })

#Server shutdown
@app.route('/shutdown', methods=['POST'])
def shutdown():
    # Perform any cleanup or additional actions before shutting down, if needed
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    exit()

""" @app.route('/open-file', methods=['POST'])
def open_file():

    print("openfile")
    Tk().withdraw() # prevents an empty tkinter window from appearing

    folder_path = filedialog.askopenfilename(initialdir="~")
    print(folder_path)
    return jsonify({'message': 'Archivo abierto correctamente'})
 """


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)