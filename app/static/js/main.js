const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const uploadBtn = document.getElementById('upload-btn');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const clearFileBtn = document.getElementById('clear-file-btn');
const uploadProgress = document.getElementById('upload-progress');
const uploadProgressBar = document.getElementById('upload-progress-bar');
const saveConfigBtn = document.getElementById('save-config-btn');

// Configuration fields
const confluenceUrl = document.getElementById('confluence-url');
const confluenceApiToken = document.getElementById('confluence-api-token');
const confluenceParentPageId = document.getElementById('confluence-parent-page-id');
const openaiApiKey = document.getElementById('openai-api-key');
const themeToggle = document.getElementById('theme-toggle');
const moonIcon = document.getElementById('moon-icon');
const sunIcon = document.getElementById('sun-icon');
const toggleConfigBtn = document.getElementById('toggle-config');
const configFields = document.getElementById('config-fields');

// WebSocket connection
const socket = io();

// Load saved configuration and preferences
loadConfiguration();
loadThemePreference();

// Theme toggle functionality
themeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    localStorage.setItem('darkMode', isDark ? 'true' : 'false');
    updateThemeIcons(isDark);
});

// Config toggle functionality
toggleConfigBtn.addEventListener('click', () => {
    const isVisible = configFields.style.display !== 'none';
    configFields.style.display = isVisible ? 'none' : 'flex';
    localStorage.setItem('configVisible', (!isVisible).toString());
    toggleConfigBtn.textContent = isVisible ? 'Show Config' : 'Hide Config';
});

function loadThemePreference() {
    const darkMode = localStorage.getItem('darkMode') === 'true';
    if (darkMode) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    updateThemeIcons(darkMode);

    // Handle config visibility
    const configVisible = localStorage.getItem('configVisible') !== 'false';
    configFields.style.display = configVisible ? 'flex' : 'none';
    toggleConfigBtn.textContent = configVisible ? 'Hide Config' : 'Show Config';
}

function updateThemeIcons(isDark) {
    if (isDark) {
        moonIcon.classList.add('hidden');
        sunIcon.classList.remove('hidden');
    } else {
        moonIcon.classList.remove('hidden');
        sunIcon.classList.add('hidden');
    }
}

// Drag and drop handlers
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-blue-500');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-blue-500');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-blue-500');
    handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', (e) => {
    handleFile(e.target.files[0]);
});

clearFileBtn.addEventListener('click', () => {
    fileInput.value = '';
    fileName.textContent = '';
    fileInfo.classList.add('hidden');
    uploadProgress.classList.add('hidden');
    uploadProgressBar.style.width = '0%';
});

function handleFile(file) {
    if (!file) return;
    fileName.textContent = file.name;
    fileInfo.classList.remove('hidden');
    // Show the file was selected immediately
    addMessage('system', `File selected: ${file.name}`);
}

// File upload handler
uploadBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    // Show progress
    uploadProgress.classList.remove('hidden');
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Processing...';

    try {
        // Simulate upload progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                uploadProgressBar.style.width = `${progress}%`;
            } else {
                clearInterval(progressInterval);
            }
        }, 200);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        // Complete the progress bar
        clearInterval(progressInterval);
        uploadProgressBar.style.width = '100%';

        const data = await response.json();
        addMessage('system', 'File processed successfully. Starting analysis...');

        // Reset the button after processing
        setTimeout(() => {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Process File';
        }, 1000);
    } catch (error) {
        uploadProgressBar.style.width = '0%';
        uploadProgress.classList.add('hidden');
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Process File';
        addMessage('error', 'Error processing file. Please try again.');
    }
});

// Configuration handlers
saveConfigBtn.addEventListener('click', saveConfiguration);

function saveConfiguration() {
    // Save to localStorage
    const config = {
        confluenceUrl: confluenceUrl.value,
        confluenceApiToken: confluenceApiToken.value,
        confluenceParentPageId: confluenceParentPageId.value,
        openaiApiKey: openaiApiKey.value
    };

    localStorage.setItem('dndStoryTellingConfig', JSON.stringify(config));
    addMessage('system', 'Configuration saved successfully!');
}

function loadConfiguration() {
    // Load from localStorage
    const savedConfig = localStorage.getItem('dndStoryTellingConfig');
    if (savedConfig) {
        const config = JSON.parse(savedConfig);
        confluenceUrl.value = config.confluenceUrl || '';
        confluenceApiToken.value = config.confluenceApiToken || '';
        confluenceParentPageId.value = config.confluenceParentPageId || '';
        openaiApiKey.value = config.openaiApiKey || '';
    }
}

// Chat handlers
sendBtn.addEventListener('click', () => sendMessage());
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    addMessage('user', message);
    socket.emit('message', { text: message });
    messageInput.value = '';

    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.id = 'typing-indicator';
    typingIndicator.className = 'flex items-center mb-2 p-2';
    typingIndicator.innerHTML = '<div class="typing-dot bg-gray-500 rounded-full h-2 w-2 mr-1 animate-pulse"></div><div class="typing-dot bg-gray-500 rounded-full h-2 w-2 mr-1 animate-pulse delay-150"></div><div class="typing-dot bg-gray-500 rounded-full h-2 w-2 animate-pulse delay-300"></div>';
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addMessage(type, text) {
    // Remove typing indicator if it exists
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `mb-2 p-2 rounded ${
        type === 'user' ? 'bg-blue-100 dark:bg-blue-900 ml-8' :
        type === 'system' ? 'bg-gray-100 dark:bg-gray-700' :
        type === 'error' ? 'bg-red-100 dark:bg-red-900' : 'bg-green-100 dark:bg-green-900 mr-8'
    } transition-colors`;
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Socket event handlers
socket.on('response', (data) => {
    addMessage('assistant', data.text);
});