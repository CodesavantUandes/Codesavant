import * as vscode from "vscode";
import axios from "axios";

async function runFlaskServer() {
  const { spawn } = require("child_process");
  const pythonProcess = await spawn("python", [
    "C:/Users/danie/OneDrive - Universidad de los Andes/2023_2/codesavant-dev/Codesavant/src/server.py",
  ]);
  const result = pythonProcess.stdout?.toString()?.trim();
  const error = pythonProcess.stderr?.toString()?.trim();
  const exit = pythonProcess.status?.toString()?.trim();
  pythonProcess.stdout.on("data", (result: any) => {
    console.log(`Flask Server Output: ${result}`);
  });

  pythonProcess.stderr.on("data", (error: any) => {
    console.error(`Flask Server Error: ${error}`);
  });

  pythonProcess.on("close", (exit: any) => {
    console.log(`Flask Server Process exited with code ${exit}`);
  });
}

async function createFileInWorkspace(content:string) {
  let name = vscode.workspace.name;
  console.log("Nombre de carpeta: " + name);
  if (name == undefined) {
    const opt = await vscode.window.showErrorMessage(
      "Debe abrir una carpeta de trabajo",
      "Abrir carpeta"
    );
    if (opt == "Abrir carpeta") {
      let carpeta = await vscode.commands.executeCommand("vscode.openFolder");
    }
    name = vscode.workspace.name;
    console.log("carpeta abierta: "+name);
    console.log(opt);
    
  }
  const fileName = await vscode.window.showInputBox();
  console.log("registrando nombre de archivo .py: "+ fileName)
  const newFilePath = vscode.Uri.joinPath(
    vscode.workspace.workspaceFolders![0].uri,
    fileName+".txt" // Replace with the desired file name
  );

  const fileContent = Buffer.from(content, "utf8"); // Replace with the desired content

  try {
    await vscode.workspace.fs.writeFile(newFilePath, fileContent);
    vscode.window.showInformationMessage("File created successfully.");
  } catch (error: any) {
    vscode.window.showErrorMessage(`Error creating file: ${error.message}`);
  }
}

async function stopFlaskServer() {
  try {
    const response = await axios.post("http://localhost:3000/shutdown");
    console.log(response.data);
  } catch (error: any) {
    console.error(error.message);
  }
}

export function activate(context: vscode.ExtensionContext) {
  runFlaskServer();
  let disposable = vscode.commands.registerCommand(
    "intelliuml.disposable",
    async (fileUri) => {
      console.log(fileUri);
    }
  );
  let openFile = vscode.commands.registerCommand(
    "intelliuml.openFile",
    async () => {
      // The code you place here will be executed every time your command is executed
      // Display a message box to the user
      console.log("Abriendo archivo");
      vscode.window.showInformationMessage("Abrir archivo");
      const serverURL = "http://localhost:3000/open-file";
      const response = await axios.post(serverURL, { content: "~" });
      console.log(response);
    }
  );

  let sendRequestToServer = vscode.commands.registerCommand(
    "intelliuml.sendRequestToServer",
    async () => {
      try {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
          vscode.window.showErrorMessage("No hay ningún editor activado");
          return;
        } else if (activeEditor.document.fileName.slice(-3) != "xmi") {
          vscode.window.showErrorMessage("Debe subir un archivo .XMI");
          return;
        }

        // Obtén el contenido del archivo abierto actualmente en el editor
        const document = activeEditor.document;
        const fileContent = document.getText();

        // Define la URL de tu servidor
        const serverURL = "http://localhost:3000/process-file";

        // Realiza una solicitud POST al servidor con el contenido del archivo
        let thisapikey = await vscode.window.showInputBox();
        const response = await axios.post(serverURL, { content: fileContent, apikey: thisapikey});
        //console.log(response);
        const fileReturn = response.data.fileReturn;
        const cwd = response.data.cwd;
        const prompt = response.data.prompt;

        console.log(prompt);
        console.log("retornofinal: \n" +fileReturn);
        // Si el servidor responde con éxito, muestra una notificación
        if (response.status === 200) {
          vscode.window.showInformationMessage(
            "Solicitud al servidor completada con éxito"
          );
          createFileInWorkspace(prompt);
        }
      } catch (error) {
        if (error instanceof Error) {
          // Maneja errores de conexión o del servidor
          vscode.window.showErrorMessage(
            "Error al enviar la solicitud al servidor: " + error.message
          );
        }
      }
    }
  );
  let helloWorld = vscode.commands.registerCommand(
    "intelliuml.helloWorld",
    () => {
      // The code you place here will be executed every time your command is executed
      // Display a message box to the user
      vscode.window.showInformationMessage("Hello World from test-extension!");
    }
  );
  let stopServer = vscode.commands.registerCommand(
    "intelliuml.stopServer",
    () => {
      // The code you place here will be executed every time your command is executed
      // Display a message box to the user
      stopFlaskServer();
      vscode.window.showWarningMessage("Servidor Flask detenido");
    }
  );
  let createFile = vscode.commands.registerCommand(
    "intelliuml.createFile",
    async () => {

      createFileInWorkspace("hola perro");
    }
  );

  context.subscriptions.push(openFile);
  context.subscriptions.push(sendRequestToServer);
  context.subscriptions.push(helloWorld);
  context.subscriptions.push(disposable);
  context.subscriptions.push(stopServer);
  context.subscriptions.push(createFile);
}

// This method is called when your extension is deactivated
export function deactivate() {
  stopFlaskServer();
}
