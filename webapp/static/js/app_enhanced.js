// PIKE-RAG Enhanced Web App JavaScript
class PikeRagEnhancedApp {
    constructor() {
        this.apiBase = '';
        this.currentSession = null;
        this.isLoading = false;
        this.selectedFiles = [];
        this.knowledgeBases = [];
        this.currentSection = 'chat';
        
        this.initElements();
        this.initEventListeners();
        this.checkHealth();
        this.loadInitialData();
    }
    
    initElements() {
        // Navigation
        this.navItems = document.querySelectorAll('.nav-item');
        this.contentSections = document.querySelectorAll('.content-section');
        
        // Chat elements
        this.questionInput = document.getElementById('question-input');
        this.askButton = document.getElementById('ask-button');
        this.conversation = document.getElementById('conversation');
        this.loadingDiv = document.getElementById('loading');
        this.reasoningStrategySelect = document.getElementById('reasoning-strategy');
        this.knowledgeBaseSelect = document.getElementById('knowledge-base');
        this.useRetrievalCheckbox = document.getElementById('use-retrieval');
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.currentStrategySpan = document.getElementById('current-strategy');
        this.examplesContainer = document.getElementById('examples-container');
        
        // Knowledge base elements
        this.uploadBtn = document.getElementById('upload-btn');
        this.uploadArea = document.getElementById('upload-area');
        this.dropzone = document.getElementById('dropzone');
        this.fileInput = document.getElementById('file-input');
        this.collectionNameInput = document.getElementById('collection-name');
        this.uploadFilesBtn = document.getElementById('upload-files-btn');
        this.cancelUploadBtn = document.getElementById('cancel-upload-btn');
        this.knowledgeBasesList = document.getElementById('knowledge-bases-list');
        
        // Sessions elements
        this.sessionsList = document.getElementById('sessions-list');
        this.clearOldSessionsBtn = document.getElementById('clear-old-sessions-btn');
        
        // Settings elements
        this.defaultStrategySelect = document.getElementById('default-strategy');
        this.systemInfo = document.getElementById('system-info');
        
        // Status elements
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        
        // Modals
        this.uploadProgressModal = document.getElementById('upload-progress-modal');
        this.uploadProgressFill = document.getElementById('upload-progress-fill');
        this.uploadStatus = document.getElementById('upload-status');
    }
    
    initEventListeners() {
        // Navigation
        this.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.switchSection(section);
            });
        });
        
        // Chat functionality
        this.questionInput.addEventListener('input', () => {
            this.updateAskButton();
            this.autoResize(this.questionInput);
        });
        
        this.questionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !this.isLoading) {
                this.askQuestion();
            }
        });
        
        this.askButton.addEventListener('click', () => {
            if (!this.isLoading) {
                this.askQuestion();
            }
        });
        
        this.newSessionBtn.addEventListener('click', () => {
            this.createNewSession();
        });
        
        this.reasoningStrategySelect.addEventListener('change', () => {
            this.currentStrategySpan.textContent = this.reasoningStrategySelect.options[this.reasoningStrategySelect.selectedIndex].text;
        });
        
        // Knowledge base functionality
        this.uploadBtn.addEventListener('click', () => {
            this.toggleUploadArea();
        });
        
        this.cancelUploadBtn.addEventListener('click', () => {
            this.hideUploadArea();
        });
        
        this.dropzone.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        this.fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });
        
        this.uploadFilesBtn.addEventListener('click', () => {
            this.uploadFiles();
        });
        
        // Drag and drop
        this.dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropzone.classList.add('dragover');
        });
        
        this.dropzone.addEventListener('dragleave', () => {
            this.dropzone.classList.remove('dragover');
        });
        
        this.dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropzone.classList.remove('dragover');
            this.handleFileSelection(e.dataTransfer.files);
        });
        
        // Sessions functionality
        this.clearOldSessionsBtn.addEventListener('click', () => {
            this.clearOldSessions();
        });
        
        // Settings functionality
        this.defaultStrategySelect.addEventListener('change', () => {
            this.reasoningStrategySelect.value = this.defaultStrategySelect.value;
            this.currentStrategySpan.textContent = this.defaultStrategySelect.options[this.defaultStrategySelect.selectedIndex].text;
        });
    }
    
    switchSection(sectionName) {
        // Update navigation
        this.navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.section === sectionName);
        });
        
        // Update content sections
        this.contentSections.forEach(section => {
            section.classList.toggle('active', section.id === sectionName + '-section');
        });
        
        this.currentSection = sectionName;
        
        // Load section-specific data
        if (sectionName === 'knowledge') {
            this.loadKnowledgeBases();
        } else if (sectionName === 'sessions') {
            this.loadSessions();
        } else if (sectionName === 'settings') {
            this.loadSystemInfo();
        }
    }
    
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiBase}/api/health`);
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('connected', 'All systems operational');
            } else {
                this.updateStatus('error', 'System issues detected');
            }
        } catch (error) {
            this.updateStatus('error', 'Unable to connect to server');
            console.error('Health check failed:', error);
        }
    }
    
    updateStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }
    
    async loadInitialData() {
        await Promise.all([
            this.loadExamples(),
            this.loadKnowledgeBases(),
            this.loadReasoningStrategies()
        ]);
    }
    
    async loadExamples() {
        try {
            const response = await fetch(`${this.apiBase}/api/examples`);
            const examples = await response.json();
            
            this.renderExamples(examples);
        } catch (error) {
            console.error('Failed to load examples:', error);
            this.examplesContainer.innerHTML = '<div class="loading-text">Failed to load examples</div>';
        }
    }
    
    renderExamples(examples) {
        this.examplesContainer.innerHTML = '';
        
        examples.forEach(category => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'example-category';
            
            const titleDiv = document.createElement('div');
            titleDiv.className = 'category-title';
            titleDiv.innerHTML = `
                ${category.category}
                <span class="strategy-badge">${category.strategy}</span>
            `;
            categoryDiv.appendChild(titleDiv);
            
            const questionsDiv = document.createElement('div');
            questionsDiv.className = 'example-questions';
            
            category.questions.forEach(question => {
                const questionBtn = document.createElement('button');
                questionBtn.className = 'example-question';
                questionBtn.textContent = question;
                questionBtn.addEventListener('click', () => {
                    this.questionInput.value = question;
                    this.reasoningStrategySelect.value = category.strategy;
                    this.currentStrategySpan.textContent = this.reasoningStrategySelect.options[this.reasoningStrategySelect.selectedIndex].text;
                    this.updateAskButton();
                    this.autoResize(this.questionInput);
                    this.questionInput.focus();
                    this.switchSection('chat');
                });
                questionsDiv.appendChild(questionBtn);
            });
            
            categoryDiv.appendChild(questionsDiv);
            this.examplesContainer.appendChild(categoryDiv);
        });
    }
    
    async loadKnowledgeBases() {
        try {
            const response = await fetch(`${this.apiBase}/api/knowledge-bases`);
            const data = await response.json();
            
            if (data.success) {
                this.knowledgeBases = data.knowledge_bases;
                this.updateKnowledgeBaseSelect();
                this.renderKnowledgeBases();
            }
        } catch (error) {
            console.error('Failed to load knowledge bases:', error);
        }
    }
    
    updateKnowledgeBaseSelect() {
        // Clear current options except default
        this.knowledgeBaseSelect.innerHTML = '<option value="documents">Default Knowledge Base</option>';
        
        // Add knowledge bases as options
        this.knowledgeBases.forEach(kb => {
            const option = document.createElement('option');
            option.value = kb.name;
            option.textContent = `${kb.name} (${kb.count} documents)`;
            this.knowledgeBaseSelect.appendChild(option);
        });
    }
    
    renderKnowledgeBases() {
        if (this.knowledgeBases.length === 0) {
            this.knowledgeBasesList.innerHTML = `
                <div class="knowledge-item">
                    <div class="knowledge-header">
                        <div>
                            <div class="knowledge-name">No Knowledge Bases</div>
                            <div class="knowledge-stats">Upload some documents to get started</div>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        this.knowledgeBasesList.innerHTML = '';
        
        this.knowledgeBases.forEach(kb => {
            const kbDiv = document.createElement('div');
            kbDiv.className = 'knowledge-item';
            
            kbDiv.innerHTML = `
                <div class="knowledge-header">
                    <div>
                        <div class="knowledge-name">${kb.name}</div>
                        <div class="knowledge-stats">${kb.count} documents</div>
                    </div>
                    <div class="knowledge-actions">
                        <button class="action-button" onclick="pikeRagApp.viewKnowledgeBase('${kb.name}')" title="View Files">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-button danger" onclick="pikeRagApp.deleteKnowledgeBase('${kb.name}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            
            this.knowledgeBasesList.appendChild(kbDiv);
        });
    }
    
    async loadSessions() {
        try {
            const response = await fetch(`${this.apiBase}/api/sessions`);
            const data = await response.json();
            
            if (data.success) {
                this.renderSessions(data.sessions);
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }
    
    renderSessions(sessions) {
        if (sessions.length === 0) {
            this.sessionsList.innerHTML = `
                <div class="session-item">
                    <div class="session-header">
                        <div>
                            <div class="session-id">No Previous Sessions</div>
                            <div class="session-stats">Start a conversation to create a session</div>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        this.sessionsList.innerHTML = '';
        
        sessions.forEach(session => {
            const sessionDiv = document.createElement('div');
            sessionDiv.className = 'session-item';
            
            const createdDate = new Date(session.created_at).toLocaleDateString();
            const lastUpdated = new Date(session.last_updated).toLocaleDateString();
            
            sessionDiv.innerHTML = `
                <div class="session-header">
                    <div>
                        <div class="session-id">${session.session_id.substring(0, 8)}...</div>
                        <div class="session-stats">
                            ${session.message_count} messages • 
                            ${session.reasoning_strategy} • 
                            ${session.knowledge_base}
                        </div>
                        <div class="session-stats">
                            Created: ${createdDate} • Last: ${lastUpdated}
                        </div>
                    </div>
                    <div class="session-actions">
                        <button class="action-button" onclick="pikeRagApp.loadSession('${session.session_id}')" title="Load Session">
                            <i class="fas fa-folder-open"></i>
                        </button>
                        <button class="action-button danger" onclick="pikeRagApp.deleteSession('${session.session_id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            
            this.sessionsList.appendChild(sessionDiv);
        });
    }
    
    async loadSystemInfo() {
        try {
            const response = await fetch(`${this.apiBase}/api/health`);
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.systemInfo.innerHTML = `
                    <h4>System Status</h4>
                    <div class="info-grid">
                        <div><strong>Status:</strong> ${data.status}</div>
                        <div><strong>Knowledge Bases:</strong> ${data.stats.knowledge_bases}</div>
                        <div><strong>Active Sessions:</strong> ${data.stats.active_sessions}</div>
                        <div><strong>Total Documents:</strong> ${data.stats.total_collections_documents}</div>
                    </div>
                    <h4 style="margin-top: 1rem;">Components</h4>
                    <ul>
                        <li>PIKE-RAG Core: ${data.components.pikerag_initialized ? '✅' : '❌'}</li>
                        <li>Azure OpenAI: ${data.components.azure_openai_connected ? '✅' : '❌'}</li>
                        <li>Document Processor: ${data.components.document_processor ? '✅' : '❌'}</li>
                        <li>Conversation Manager: ${data.components.conversation_manager ? '✅' : '❌'}</li>
                        <li>Reasoning Manager: ${data.components.reasoning_manager ? '✅' : '❌'}</li>
                    </ul>
                `;
            }
        } catch (error) {
            console.error('Failed to load system info:', error);
            this.systemInfo.innerHTML = '<div class="error-text">Failed to load system information</div>';
        }
    }
    
    async loadReasoningStrategies() {
        try {
            const response = await fetch(`${this.apiBase}/api/reasoning-strategies`);
            const data = await response.json();
            
            if (data.success) {
                // Update strategy descriptions if needed
                console.log('Available reasoning strategies:', data.strategies);
            }
        } catch (error) {
            console.error('Failed to load reasoning strategies:', error);
        }
    }
    
    updateAskButton() {
        const hasText = this.questionInput.value.trim().length > 0;
        this.askButton.disabled = !hasText || this.isLoading;
    }
    
    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(60, textarea.scrollHeight) + 'px';
    }
    
    async askQuestion() {
        const question = this.questionInput.value.trim();
        if (!question || this.isLoading) return;
        
        this.setLoading(true);
        this.addMessage('question', question);
        
        try {
            const requestData = {
                question: question,
                session_id: this.currentSession,
                reasoning_strategy: this.reasoningStrategySelect.value,
                knowledge_base: this.knowledgeBaseSelect.value,
                use_retrieval: this.useRetrievalCheckbox.checked
            };
            
            const response = await fetch(`${this.apiBase}/api/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = data.session_id;
                this.addMessage('answer', data.answer, {
                    rationale: data.rationale,
                    processingTime: data.processing_time,
                    model: data.model,
                    reasoningStrategy: data.reasoning_strategy,
                    reasoningSteps: data.reasoning_steps,
                    contextUsed: data.context_used,
                    timestamp: data.timestamp
                });
            } else {
                this.addMessage('error', `Error: ${data.error}`);
            }
            
        } catch (error) {
            console.error('API request failed:', error);
            this.addMessage('error', 'Failed to get response from server. Please try again.');
        } finally {
            this.setLoading(false);
            this.questionInput.value = '';
            this.updateAskButton();
            this.autoResize(this.questionInput);
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        this.loadingDiv.style.display = loading ? 'block' : 'none';
        this.updateAskButton();
        
        if (loading) {
            this.scrollToBottom();
        }
    }
    
    addMessage(type, content, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        
        // Message header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        
        const iconDiv = document.createElement('div');
        iconDiv.className = `message-icon ${type}-icon`;
        
        const labelSpan = document.createElement('span');
        
        if (type === 'question') {
            iconDiv.innerHTML = '<i class="fas fa-user"></i>';
            labelSpan.textContent = 'You';
        } else if (type === 'answer') {
            iconDiv.innerHTML = '<i class="fas fa-robot"></i>';
            labelSpan.textContent = 'PIKE-RAG Assistant';
        } else if (type === 'error') {
            iconDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            labelSpan.textContent = 'Error';
            iconDiv.className = 'message-icon answer-icon';
            iconDiv.style.background = 'var(--error-color)';
        }
        
        headerDiv.appendChild(iconDiv);
        headerDiv.appendChild(labelSpan);
        
        // Message content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(headerDiv);
        messageDiv.appendChild(contentDiv);
        
        // Add metadata for answers
        if (type === 'answer' && metadata.processingTime) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            
            const metaItems = [
                `<div class="meta-item"><i class="fas fa-clock"></i> ${metadata.processingTime}s</div>`,
                `<div class="meta-item"><i class="fas fa-brain"></i> ${metadata.model}</div>`,
                `<div class="meta-item"><i class="fas fa-cog"></i> ${metadata.reasoningStrategy}</div>`,
                `<div class="meta-item"><i class="fas fa-database"></i> ${metadata.contextUsed} docs</div>`
            ];
            
            metaDiv.innerHTML = metaItems.join('');
            messageDiv.appendChild(metaDiv);
            
            // Add reasoning steps if available
            if (metadata.reasoningSteps && metadata.reasoningSteps.length > 0) {
                const reasoningDiv = document.createElement('div');
                reasoningDiv.className = 'reasoning-steps';
                
                reasoningDiv.innerHTML = `
                    <h4><i class="fas fa-list-ol"></i> Reasoning Steps:</h4>
                    <ul>
                        ${metadata.reasoningSteps.map(step => `<li>${step}</li>`).join('')}
                    </ul>
                `;
                
                messageDiv.appendChild(reasoningDiv);
            }
        }
        
        this.conversation.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.conversation.scrollTop = this.conversation.scrollHeight;
        }, 100);
    }
    
    // Knowledge base functionality
    toggleUploadArea() {
        const isVisible = this.uploadArea.style.display !== 'none';
        this.uploadArea.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
            this.selectedFiles = [];
            this.fileInput.value = '';
            this.updateUploadButton();
        }
    }
    
    hideUploadArea() {
        this.uploadArea.style.display = 'none';
        this.selectedFiles = [];
        this.fileInput.value = '';
        this.updateUploadButton();
    }
    
    handleFileSelection(files) {
        this.selectedFiles = Array.from(files);
        this.updateUploadButton();
        
        // Show selected files
        const fileNames = this.selectedFiles.map(f => f.name).join(', ');
        this.dropzone.querySelector('.upload-text p').textContent = 
            `${this.selectedFiles.length} file(s) selected: ${fileNames}`;
    }
    
    updateUploadButton() {
        this.uploadFilesBtn.disabled = this.selectedFiles.length === 0;
    }
    
    async uploadFiles() {
        if (this.selectedFiles.length === 0) return;
        
        this.showUploadModal();
        
        for (let i = 0; i < this.selectedFiles.length; i++) {
            const file = this.selectedFiles[i];
            const progress = ((i + 1) / this.selectedFiles.length) * 100;
            
            this.uploadStatus.textContent = `Uploading ${file.name}...`;
            this.uploadProgressFill.style.width = `${progress}%`;
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('collection_name', this.collectionNameInput.value || 'documents');
                
                const response = await fetch(`${this.apiBase}/api/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (!data.success) {
                    console.error(`Failed to upload ${file.name}:`, data.error);
                }
                
            } catch (error) {
                console.error(`Error uploading ${file.name}:`, error);
            }
        }
        
        this.uploadStatus.textContent = 'Upload complete!';
        
        setTimeout(() => {
            this.hideUploadModal();
            this.hideUploadArea();
            this.loadKnowledgeBases();
        }, 1000);
    }
    
    showUploadModal() {
        this.uploadProgressModal.style.display = 'flex';
        this.uploadProgressFill.style.width = '0%';
        this.uploadStatus.textContent = 'Preparing upload...';
    }
    
    hideUploadModal() {
        this.uploadProgressModal.style.display = 'none';
    }
    
    // Session management
    async createNewSession() {
        try {
            const response = await fetch(`${this.apiBase}/api/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    reasoning_strategy: this.reasoningStrategySelect.value,
                    knowledge_base: this.knowledgeBaseSelect.value
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = data.session_id;
                this.conversation.innerHTML = '';
                this.addMessage('system', 'New conversation session started');
            }
        } catch (error) {
            console.error('Failed to create new session:', error);
        }
    }
    
    async loadSession(sessionId) {
        try {
            const response = await fetch(`${this.apiBase}/api/sessions/${sessionId}/history`);
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = sessionId;
                this.conversation.innerHTML = '';
                
                data.messages.forEach(msg => {
                    this.addMessage(msg.role === 'user' ? 'question' : 'answer', msg.content, msg.metadata || {});
                });
                
                this.switchSection('chat');
            }
        } catch (error) {
            console.error('Failed to load session:', error);
        }
    }
    
    async deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this session?')) return;
        
        try {
            const response = await fetch(`${this.apiBase}/api/sessions/${sessionId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadSessions();
                if (this.currentSession === sessionId) {
                    this.currentSession = null;
                    this.conversation.innerHTML = '';
                }
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    }
    
    async clearOldSessions() {
        if (!confirm('Are you sure you want to clear old sessions (30+ days)?')) return;
        
        try {
            // This would need to be implemented in the backend
            console.log('Clearing old sessions...');
            this.loadSessions();
        } catch (error) {
            console.error('Failed to clear old sessions:', error);
        }
    }
    
    // Knowledge base management
    async viewKnowledgeBase(collectionName) {
        try {
            const response = await fetch(`${this.apiBase}/api/knowledge-bases/${collectionName}/files`);
            const data = await response.json();
            
            if (data.success) {
                this.showKnowledgeBaseModal(collectionName, data.files);
            }
        } catch (error) {
            console.error('Failed to view knowledge base:', error);
            alert('Failed to load knowledge base details');
        }
    }

    showKnowledgeBaseModal(collectionName, files) {
        const totalChunks = files.reduce((sum, file) => sum + file.chunks_count, 0);
        const formatFileSize = (bytes) => {
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            if (bytes === 0) return '0 Bytes';
            const i = Math.floor(Math.log(bytes) / Math.log(1024));
            return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
        };

        // Create modal HTML
        const modalHtml = `
            <div class="modal-overlay" id="kb-modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3><i class="fas fa-database"></i> Knowledge Base: ${collectionName}</h3>
                        <button class="modal-close" onclick="pikeRagApp.closeKnowledgeBaseModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="kb-stats">
                            <div class="stat-item">
                                <strong>Total Files:</strong> ${files.length}
                            </div>
                            <div class="stat-item">
                                <strong>Total Chunks:</strong> ${totalChunks}
                            </div>
                        </div>
                        <div class="kb-files-list">
                            ${files.map(file => `
                                <div class="kb-file-item">
                                    <div class="file-header">
                                        <i class="fas fa-file-${this.getFileIcon(file.file_type)}"></i>
                                        <strong>${file.filename || 'Unknown File'}</strong>
                                    </div>
                                    <div class="file-details">
                                        <div class="file-meta">
                                            <span><strong>File Type:</strong> ${file.file_type?.toUpperCase() || 'Unknown'}</span>
                                            <span><strong>File Size:</strong> ${formatFileSize(file.file_size || 0)}</span>
                                            <span><strong>Chunks Created:</strong> ${file.chunks_count || 0}</span>
                                            <span><strong>Uploaded:</strong> ${new Date(file.upload_time).toLocaleString()}</span>
                                        </div>
                                        <div class="file-id">
                                            <strong>File ID:</strong> <code>${file.file_id}</code>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        ${files.length === 0 ? '<div class="no-files">No files found in this knowledge base.</div>' : ''}
                    </div>
                    <div class="modal-footer">
                        <button class="secondary-button" onclick="pikeRagApp.closeKnowledgeBaseModal()">Close</button>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        const existingModal = document.getElementById('kb-modal-overlay');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        document.body.style.overflow = 'hidden';
    }

    getFileIcon(fileType) {
        switch (fileType?.toLowerCase()) {
            case 'pdf': return 'pdf';
            case 'doc':
            case 'docx': return 'word';
            case 'txt': return 'text';
            default: return 'file-alt';
        }
    }

    closeKnowledgeBaseModal() {
        const modal = document.getElementById('kb-modal-overlay');
        if (modal) {
            modal.remove();
            document.body.style.overflow = '';
        }
    }
    
    async deleteKnowledgeBase(collectionName) {
        if (!confirm(`Are you sure you want to delete the knowledge base "${collectionName}"? This cannot be undone.`)) return;
        
        try {
            const response = await fetch(`${this.apiBase}/api/knowledge-bases/${collectionName}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadKnowledgeBases();
            } else {
                alert(`Failed to delete knowledge base: ${data.error}`);
            }
        } catch (error) {
            console.error('Failed to delete knowledge base:', error);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pikeRagApp = new PikeRagEnhancedApp();
});

// Handle errors gracefully
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});