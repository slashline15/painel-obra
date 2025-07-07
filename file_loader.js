/**
 * HDAM File Loader - Integração com o scanner Python
 * 
 * Este script deve ser incluído no HTML após o script principal
 * Ele carrega os dados do arquivo JSON gerado pelo Python
 */

// Configuração
const FILE_LOADER_CONFIG = {
    dataFile: 'file_data.json',
    notesFile: 'file_notes.json',
    refreshInterval: 30000, // 30 segundos
    autoRefresh: true
};

// Função para carregar dados do arquivo JSON
async function loadFileData() {
    try {
        const response = await fetch(FILE_LOADER_CONFIG.dataFile + '?t=' + Date.now());
        if (!response.ok) {
            throw new Error('Arquivo não encontrado');
        }
        
        const data = await response.json();
        
        // Atualizar o objeto fileSystem global
        if (data.disciplines) {
            Object.keys(data.disciplines).forEach(key => {
                if (fileSystem[key]) {
                    fileSystem[key].files = data.disciplines[key].files || [];
                    fileSystem[key].folders = data.disciplines[key].folders || [];
                    
                    // Atualizar estatísticas nos cards
                    updateDisciplineStats(key, data.disciplines[key]);
                }
            });
        }
        
        // Se estiver visualizando uma disciplina, recarregar a tabela
        if (currentDiscipline) {
            loadFiles(currentDiscipline);
        }
        
        console.log('[FILE_LOADER] Dados carregados:', new Date().toLocaleTimeString());
        
        // Atualizar indicador de sync
        const syncIndicator = document.getElementById('syncStatus');
        if (syncIndicator) {
            const dot = syncIndicator.querySelector('.status-dot');
            dot.classList.remove('local', 'sync');
            dot.classList.add('sync');
            syncIndicator.querySelector('span').textContent = 'SYNCED';
            
            // Voltar ao estado normal após 2 segundos
            setTimeout(() => {
                dot.classList.remove('sync');
                dot.classList.add('local');
                syncIndicator.querySelector('span').textContent = 'LOCAL MODE';
            }, 2000);
        }
        
    } catch (error) {
        console.error('[FILE_LOADER] Erro ao carregar dados:', error);
    }
}

// Função para atualizar estatísticas das disciplinas
function updateDisciplineStats(discipline, data) {
    const mapping = {
        'architecture': 'arch',
        'structure': 'struct',
        'hydraulic': 'hydro',
        'metallic': 'metal'
    };
    
    const prefix = mapping[discipline];
    if (!prefix) return;
    
    // Atualizar contadores
    const filesElement = document.getElementById(`${prefix}-files`);
    const foldersElement = document.getElementById(`${prefix}-folders`);
    const sizeElement = document.getElementById(`${prefix}-size`);
    
    if (filesElement) {
        filesElement.textContent = data.total_files || 0;
    }
    if (foldersElement) {
        foldersElement.textContent = data.folders ? data.folders.length : 0;
    }
    if (sizeElement) {
        sizeElement.textContent = data.total_size || '0MB';
    }
}

// Sobrescrever a função syncFiles para usar o loader
const originalSyncFiles = window.syncFiles;
window.syncFiles = async function() {
    const btn = document.getElementById('syncBtn');
    const modal = document.getElementById('loadingModal');
    
    btn.classList.add('syncing');
    modal.classList.add('active');
    
    try {
        await loadFileData();
        console.log('[SYNC] Sincronização completa');
    } catch (error) {
        console.error('[SYNC] Erro:', error);
        alert('Erro na sincronização. Verifique se o scanner Python está rodando.');
    } finally {
        btn.classList.remove('syncing');
        modal.classList.remove('active');
    }
};

// Carregar dados ao iniciar
document.addEventListener('DOMContentLoaded', () => {
    // Aguardar um pouco para garantir que tudo foi inicializado
    setTimeout(() => {
        loadFileData();
        
        // Auto-refresh se habilitado
        if (FILE_LOADER_CONFIG.autoRefresh) {
            setInterval(loadFileData, FILE_LOADER_CONFIG.refreshInterval);
        }
    }, 500);
});

// Função para salvar notas via requisição
async function saveNoteToFile(discipline, fileName, note) {
    try {
        // Em produção, isso seria uma chamada para um servidor
        // Por enquanto, apenas salva no localStorage
        const savedNotes = localStorage.getItem('fileNotes');
        const notes = savedNotes ? JSON.parse(savedNotes) : {};
        const noteKey = `${discipline}_${fileName}`;
        
        if (note.trim()) {
            notes[noteKey] = note;
        } else {
            delete notes[noteKey];
        }
        
        localStorage.setItem('fileNotes', JSON.stringify(notes));
        
        // Se tiver um servidor rodando, enviar para ele
        if (window.location.protocol !== 'file:') {
            try {
                await fetch('/api/notes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        discipline,
                        fileName,
                        note
                    })
                });
            } catch (e) {
                // Ignorar erro se não houver servidor
            }
        }
        
    } catch (error) {
        console.error('[NOTES] Erro ao salvar nota:', error);
    }
}

// Sobrescrever a função saveNote original
window.saveNote = saveNoteToFile;

console.log('[FILE_LOADER] Script de integração carregado');