// PIKE-RAG Web App JavaScript
class PikeRagApp {
    constructor() {
        this.apiBase = '';
        this.conversationHistory = [];
        this.isLoading = false;
        
        this.initElements();
        this.initEventListeners();
        this.checkHealth();
        this.loadExamples();
    }
    
    initElements() {
        this.questionInput = document.getElementById('question-input');
        this.askButton = document.getElementById('ask-button');
        this.loadingDiv = document.getElementById('loading');
        this.resultsSection = document.getElementById('results-section');
        this.conversation = document.getElementById('conversation');
        this.clearButton = document.getElementById('clear-button');
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        this.examplesContainer = document.getElementById('examples-container');
    }
    
    initEventListeners() {
        // Question input events
        this.questionInput.addEventListener('input', () => {
            this.updateAskButton();
        });
        
        this.questionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !this.isLoading) {
                this.askQuestion();
            }
        });
        
        // Ask button
        this.askButton.addEventListener('click', () => {
            if (!this.isLoading) {
                this.askQuestion();
            }
        });
        
        // Clear button
        this.clearButton.addEventListener('click', () => {
            this.clearConversation();
        });
        
        // Auto-resize textarea
        this.questionInput.addEventListener('input', () => {
            this.autoResize(this.questionInput);
        });
    }
    
    updateAskButton() {
        const hasText = this.questionInput.value.trim().length > 0;
        this.askButton.disabled = !hasText || this.isLoading;
    }
    
    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(80, textarea.scrollHeight) + 'px';
    }
    
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiBase}/api/health`);
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('connected', 'Connected to PIKE-RAG');
            } else {
                this.updateStatus('error', 'Connection issues detected');
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
    
    async loadExamples() {
        try {
            const response = await fetch(`${this.apiBase}/api/examples`);
            const examples = await response.json();
            
            this.renderExamples(examples);
        } catch (error) {
            console.error('Failed to load examples:', error);
            this.examplesContainer.innerHTML = '<div class="loading-examples">Failed to load examples</div>';
        }
    }
    
    renderExamples(examples) {
        this.examplesContainer.innerHTML = '';
        
        examples.forEach(category => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'example-category';
            
            const titleDiv = document.createElement('div');
            titleDiv.className = 'category-title';
            titleDiv.textContent = category.category;
            categoryDiv.appendChild(titleDiv);
            
            const questionsDiv = document.createElement('div');
            questionsDiv.className = 'example-questions';
            
            category.questions.forEach(question => {
                const questionBtn = document.createElement('button');
                questionBtn.className = 'example-question';
                questionBtn.textContent = question;
                questionBtn.addEventListener('click', () => {
                    this.questionInput.value = question;
                    this.updateAskButton();
                    this.autoResize(this.questionInput);
                    this.questionInput.focus();
                });
                questionsDiv.appendChild(questionBtn);
            });
            
            categoryDiv.appendChild(questionsDiv);
            this.examplesContainer.appendChild(categoryDiv);
        });
    }
    
    async askQuestion() {
        const question = this.questionInput.value.trim();
        if (!question || this.isLoading) return;
        
        this.setLoading(true);
        this.addMessage('question', question);
        
        try {
            const response = await fetch(`${this.apiBase}/api/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addMessage('answer', data.answer, {
                    rationale: data.rationale,
                    processingTime: data.processing_time,
                    model: data.model,
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
            this.showResults();
            this.scrollToBottom();
        }
    }
    
    showResults() {
        this.resultsSection.style.display = 'block';
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
            
            const timeSpan = document.createElement('span');
            timeSpan.className = 'processing-time';
            timeSpan.innerHTML = `<i class="fas fa-clock"></i> ${metadata.processingTime}s`;
            
            const modelSpan = document.createElement('span');
            modelSpan.innerHTML = `<i class="fas fa-brain"></i> ${metadata.model}`;
            
            metaDiv.appendChild(timeSpan);
            metaDiv.appendChild(modelSpan);
            messageDiv.appendChild(metaDiv);
        }
        
        this.conversation.appendChild(messageDiv);
        this.conversationHistory.push({ type, content, metadata });
        
        this.scrollToBottom();
        this.showResults();
    }
    
    clearConversation() {
        if (this.conversationHistory.length === 0) return;
        
        if (confirm('Are you sure you want to clear the conversation?')) {
            this.conversation.innerHTML = '';
            this.conversationHistory = [];
            this.resultsSection.style.display = 'none';
        }
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.conversation.scrollTop = this.conversation.scrollHeight;
        }, 100);
    }
    
    // Utility methods
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pikeRagApp = new PikeRagApp();
});

// Handle errors gracefully
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});