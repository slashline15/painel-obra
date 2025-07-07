// Adicione no HTML antes do </body>
<script src="https://apis.google.com/js/api.js"></script>

// Inicialização
function initGoogleDrive() {
    gapi.load('client:auth2', () => {
        gapi.client.init({
            apiKey: 'YOUR_API_KEY',
            clientId: 'YOUR_CLIENT_ID',
            scope: 'https://www.googleapis.com/auth/drive.readonly'
        });
    });
}

// Listar arquivos
async function listDriveFiles(folderId) {
    const response = await gapi.client.drive.files.list({
        q: `'${folderId}' in parents`,
        fields: 'files(id, name, mimeType, size, modifiedTime)'
    });
    return response.result.files;
}