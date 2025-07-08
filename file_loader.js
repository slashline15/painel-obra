/**
 * HDAM File Loader - Integração com API FastAPI
 */

// Configuração
const FILE_LOADER_CONFIG = {
    apiUrl: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000' 
        : 'https://api.dimensaoc137.org',  // ← MUDE AQUI
    refreshInterval: 30000,
    autoRefresh: true
};

// Função para carregar dados da API
async function loadFileData() {
    try {
        const response = await fetch(`${FILE_LOADER_CONFIG.apiUrl}/api/files`);
        if (!response.ok) {
            throw new Error('Erro ao carregar dados');
        }
        
        const data = await response.json();
        
        // Atualizar o objeto fileSystem global
        if (data.disciplines) {
            Object.keys(data.disciplines).forEach(key => {
                if (fileSystem[key]) {
                    fileSystem[key] = {
                        ...fileSystem[key],
                        ...data.disciplines[key]
                    };
                    
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
        updateSyncIndicator('synced');
        
    } catch (error) {
        console.error('[FILE_LOADER] Erro ao carregar dados:', error);
        updateSyncIndicator('error');
    }
}

// Função para atualizar indicador de sincronização
function updateSyncIndicator(status) {
    const syncIndicator = document.getElementById('syncStatus');
    if (!syncIndicator) return;
    
    const dot = syncIndicator.querySelector('.status-dot');
    const text = syncIndicator.querySelector('span');
    
    switch(status) {
        case 'synced':
            dot.classList.remove('local', 'sync', 'error');
            dot.classList.add('sync');
            text.textContent = 'SYNCED';
            
            // Voltar ao estado normal após 2 segundos
            setTimeout(() => {
                dot.classList.remove('sync');
                dot.classList.add('local');
                text.textContent = 'API MODE';
            }, 2000);
            break;
            
        case 'syncing':
            dot.classList.remove('local', 'sync', 'error');
            dot.classList.add('sync');
            text.textContent = 'SYNCING...';
            break;
            
        case 'error':
            dot.classList.remove('local', 'sync');
            dot.classList.add('error');
            text.textContent = 'SYNC ERROR';
            break;
            
        default:
            dot.classList.remove('sync', 'error');
            dot.classList.add('local');
            text.textContent = 'API MODE';
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
    const elements = {
        files: document.getElementById(`${prefix}-files`),
        folders: document.getElementById(`${prefix}-folders`),
        size: document.getElementById(`${prefix}-size`)
    };
    
    if (elements.files) {
        elements.files.textContent = data.total_files || 0;
    }
    if (elements.folders) {
        elements.folders.textContent = data.folders ? data.folders.length : 0;
    }
    if (elements.size) {
        elements.size.textContent = data.total_size || '0MB';
    }
}

// Sobrescrever a função syncFiles
window.syncFiles = async function() {
    const btn = document.getElementById('syncBtn');
    const modal = document.getElementById('loadingModal');
    
    btn.classList.add('syncing');
    modal.classList.add('active');
    updateSyncIndicator('syncing');
    
    try {
        // Chamar API de refresh
        const response = await fetch(`${FILE_LOADER_CONFIG.apiUrl}/api/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao sincronizar');
        }
        
        // Aguardar o backend processar
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Recarregar dados
        await loadFileData();
        
        console.log('[SYNC] Sincronização completa');
    } catch (error) {
        console.error('[SYNC] Erro:', error);
        alert('Erro na sincronização. Verifique se o servidor está rodando.');
        updateSyncIndicator('error');
    } finally {
        btn.classList.remove('syncing');
        modal.classList.remove('active');
    }
};

// Função para salvar notas via API
window.saveNote = async function(discipline, fileName, note) {
    try {
        const response = await fetch(
            `${FILE_LOADER_CONFIG.apiUrl}/api/notes/${discipline}/${encodeURIComponent(fileName)}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: note })
            }
        );
        
        if (!response.ok) {
            throw new Error('Erro ao salvar nota');
        }
        
        // Também salvar localmente para cache
        const savedNotes = localStorage.getItem('fileNotes');
        const notes = savedNotes ? JSON.parse(savedNotes) : {};
        const noteKey = `${discipline}_${fileName}`;
        
        if (note.trim()) {
            notes[noteKey] = note;
        } else {
            delete notes[noteKey];
        }
        
        localStorage.setItem('fileNotes', JSON.stringify(notes));
        
    } catch (error) {
        console.error('[NOTES] Erro ao salvar nota:', error);
        // Fallback para localStorage apenas
        saveNoteToLocalStorage(discipline, fileName, note);
    }
};

// Fallback para localStorage
function saveNoteToLocalStorage(discipline, fileName, note) {
    const savedNotes = localStorage.getItem('fileNotes');
    const notes = savedNotes ? JSON.parse(savedNotes) : {};
    const noteKey = `${discipline}_${fileName}`;
    
    if (note.trim()) {
        notes[noteKey] = note;
    } else {
        delete notes[noteKey];
    }
    
    localStorage.setItem('fileNotes', JSON.stringify(notes));
}

// Adicionar estilo para indicador de erro
const style = document.createElement('style');
style.textContent = `
    .status-dot.error {
        background: var(--matrix-red);
        box-shadow: 0 0 10px var(--matrix-red);
    }
`;
document.head.appendChild(style);

// Carregar dados ao iniciar
document.addEventListener('DOMContentLoaded', () => {
    // Aguardar inicialização
    setTimeout(() => {
        loadFileData();
        
        // Auto-refresh se habilitado
        if (FILE_LOADER_CONFIG.autoRefresh) {
            setInterval(loadFileData, FILE_LOADER_CONFIG.refreshInterval);
        }
    }, 500);
});

console.log('[FILE_LOADER] Script de integração API carregado');