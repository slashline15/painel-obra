const fs = require('fs');
const path = require('path');

function scanDirectory(dirPath) {
    const results = {
        files: [],
        folders: []
    };
    
    fs.readdirSync(dirPath).forEach(item => {
        const fullPath = path.join(dirPath, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
            results.folders.push(item);
        } else {
            results.files.push({
                name: item,
                type: path.extname(item).slice(1),
                size: (stat.size / 1048576).toFixed(1) + 'MB',
                modified: stat.mtime.toISOString().split('T')[0],
                path: dirPath
            });
        }
    });
    
    return results;
}

// Executar periodicamente
setInterval(() => {
    const data = scanDirectory('I:\\Meu Drive\\DRIVE PREDIO ADM');
    fs.writeFileSync('file-data.json', JSON.stringify(data));
}, 60000); // A cada minuto