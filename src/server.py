from flask import Flask, request, jsonify
import xml.etree.ElementTree as ET
import os
import shutil
import xmi2nl
import api_azure2openai as azuapi
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/process-file', methods=['POST'])

def process_file():

    data = request.json
    file_content = data.get('content')
    apikey = data.get('apikey')
    cwd = os. getcwd()
    with open('data.txt', 'w') as archivo:
        archivo.write(file_content)
    shutil.copy('data.txt', 'data.xmi')
    dataXMI = xmi2nl.openFile('data.xmi')
    info = xmi2nl.filter(dataXMI)
    prompt = xmi2nl.interpreter(info)
    thrd = len(prompt)//3
    p_vals = prompt[:thrd], prompt[thrd:2*thrd], prompt[2*thrd:] 
    jointprompt = " ".join(p_vals[0])
    try:
        ans = process(apikey, p_vals[0])
    except Exception as e:
        ans = "Un error ha ocurrido: " + str(e)
    #print(prompt) 
    # file_nl = xmi2nl.openFile("data.xmi")
    #print(file_content)
    return jsonify({'message': 'Archivo procesado correctamente', 'fileReturn':ans, 'cwd':cwd, 'prompt':jointprompt, 'apikey': apikey})

def process(apikey,promtp):
    p = azuapi.API(apikey,'davinci',promtp,3500,0.5)
    ans = p.response_code().choices[0].text
    return ans

    

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