const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileSelectBtn = document.getElementById('file-select-btn');
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
const clearConfigBtn = document.getElementById('clear-config-btn');
const sessionNumberInput = document.getElementById('session-number');
const autoDetectSessionBtn = document.getElementById('auto-detect-session');

// Configuration fields
const confluenceUrl = document.getElementById('confluence-url');
const confluenceApiToken = document.getElementById('confluence-api-token');
const confluenceParentPageId = document.getElementById('confluence-parent-page-id');
const openaiApiKey = document.getElementById('openai-api-key');
// Global variables - will be initialized when DOM loads
let themeToggle, themeIcon, toggleConfigBtn, configFields;
let socket = null;

// Story management
let currentStory = null;
let currentTranscription = null;
let currentSessionData = {
    sessionNumber: null,
    fileName: null,
    processedAt: null,
    story: null,
    transcription: null
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');

    // Initialize DOM elements
    themeToggle = document.getElementById('theme-toggle');
    themeIcon = document.getElementById('theme-icon');
    toggleConfigBtn = document.getElementById('toggle-config');
    configFields = document.getElementById('config-fields');    // Set up event listeners after elements are available
    setupEventListeners();

    // Initialize WebSocket connection (only if Socket.IO is available and not disabled)
    const enableSocketIO = localStorage.getItem('enableSocketIO') !== 'false'; // Default to enabled

    if (typeof io !== 'undefined' && enableSocketIO) {
        socket = io({
            // Optimize connection settings
            transports: ['websocket', 'polling'], // Prefer websocket over polling
            upgrade: true, // Allow upgrade from polling to websocket
            timeout: 20000, // 20 second timeout
            forceNew: false, // Reuse existing connection
            reconnection: true, // Enable reconnection
            reconnectionDelay: 1000, // Wait 1 second before reconnecting
            reconnectionAttempts: 5, // Try 5 times then give up
            maxReconnectionAttempts: 5,
            pingInterval: 25000, // 25 seconds
            pingTimeout: 20000, // 20 seconds
        });
        console.log('Socket.IO initialized with optimized settings');
        setupSocketEventHandlers();
    } else {
        console.log('Socket.IO disabled or not available - chat functionality will be limited');
        // Add a message to let users know they can enable it
        if (typeof io !== 'undefined' && !enableSocketIO) {
            console.log('To enable chat functionality, run: localStorage.setItem("enableSocketIO", "true"); then reload');
        }
    }

    loadConfiguration();
    loadThemePreference();
    setupKeyboardShortcuts();
});

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + S to save configuration
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (saveConfigBtn && !saveConfigBtn.disabled) {
                saveConfiguration();
            }
        }

        // Ctrl/Cmd + U to focus file upload
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            fileInput.click();
        }

        // Ctrl/Cmd + D to toggle dark mode
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            if (themeToggle) {
                themeToggle.click();
            }
        }

        // Ctrl/Cmd + E to toggle configuration
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            if (toggleConfigBtn) {
                toggleConfigBtn.click();
            }
        }

        // Escape to clear file selection
        if (e.key === 'Escape' && fileInput.files.length > 0) {
            clearFileBtn.click();
        }
    });

    // Show keyboard shortcuts hint
    addMessage('system', '⌨️ Keyboard shortcuts: Ctrl+S (save config), Ctrl+U (upload file), Ctrl+D (toggle theme), Ctrl+E (toggle config), Esc (clear file)');
}

function setupEventListeners() {
    // Theme toggle functionality
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            const isDark = document.documentElement.classList.contains('dark');
            console.log('Dark mode toggled:', isDark);
            console.log('HTML classes:', document.documentElement.className);
            localStorage.setItem('darkMode', isDark ? 'true' : 'false');
            updateThemeIcons(isDark);
        });
    } else {
        console.error('Theme toggle element not found!');
    }

    // Config toggle functionality
    if (toggleConfigBtn) {
        toggleConfigBtn.addEventListener('click', () => {
            const isVisible = configFields.style.display !== 'none';
            configFields.style.display = isVisible ? 'none' : 'flex';
            localStorage.setItem('configVisible', (!isVisible).toString());
            toggleConfigBtn.textContent = isVisible ? 'Show Config' : 'Hide Config';
        });
    }

    // Socket.IO toggle functionality
    const toggleSocketBtn = document.getElementById('toggle-socket-btn');
    if (toggleSocketBtn) {
        const updateSocketButtonText = () => {
            const enabled = localStorage.getItem('enableSocketIO') !== 'false';
            toggleSocketBtn.textContent = `Chat: ${enabled ? 'ON' : 'OFF'}`;
            toggleSocketBtn.className = enabled
                ? 'bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 dark:bg-green-600 dark:hover:bg-green-700'
                : 'bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700';
        };

        updateSocketButtonText();

        toggleSocketBtn.addEventListener('click', () => {
            const currentlyEnabled = localStorage.getItem('enableSocketIO') !== 'false';
            localStorage.setItem('enableSocketIO', (!currentlyEnabled).toString());
            updateSocketButtonText();

            // Show message about reload
            addMessage('system', `Chat functionality ${!currentlyEnabled ? 'enabled' : 'disabled'}. Please reload the page for changes to take effect.`);
        });
    }

    // Story Refinement Prompts functionality
    const togglePromptsBtn = document.getElementById('toggle-prompts');
    const promptsPanel = document.getElementById('prompts-panel');
    const promptsArrow = document.getElementById('prompts-arrow');

    if (togglePromptsBtn && promptsPanel) {
        togglePromptsBtn.addEventListener('click', () => {
            const isVisible = !promptsPanel.classList.contains('hidden');

            if (isVisible) {
                promptsPanel.classList.add('hidden');
                promptsArrow.style.transform = 'rotate(0deg)';
            } else {
                promptsPanel.classList.remove('hidden');
                promptsArrow.style.transform = 'rotate(180deg)';
            }
        });
    }

    // Prompt option click handlers
    document.addEventListener('click', (e) => {
        if (e.target.closest('.prompt-option')) {
            const promptOption = e.target.closest('.prompt-option');
            const promptText = promptOption.getAttribute('data-prompt');
            const messageInput = document.getElementById('message-input');

            if (messageInput && promptText) {
                // Populate the input field with the prompt text
                messageInput.value = promptText;
                messageInput.focus();

                // Optional: Auto-collapse the prompts panel after selection
                if (promptsPanel && !promptsPanel.classList.contains('hidden')) {
                    promptsPanel.classList.add('hidden');
                    promptsArrow.style.transform = 'rotate(0deg)';
                }

                // Add visual feedback
                promptOption.classList.add('scale-95');
                setTimeout(() => {
                    promptOption.classList.remove('scale-95');
                }, 150);
            }
        }
    });

    // Session Number Auto-detect functionality
    if (autoDetectSessionBtn) {
        autoDetectSessionBtn.addEventListener('click', () => {
            const currentFileName = fileName.textContent;
            if (currentFileName) {
                const detectedSession = extractSessionNumber(currentFileName);
                if (detectedSession) {
                    sessionNumberInput.value = detectedSession;
                    addMessage('system', `📝 Auto-detected session: "${detectedSession}"`);
                } else {
                    addMessage('system', '⚠️ Could not auto-detect session number from filename. Please enter manually.');
                }
            }
        });
    }
}

// Initialize theme on page load
function initializeTheme() {
    const savedDarkMode = localStorage.getItem('darkMode');
    const systemDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = savedDarkMode === 'true' || (savedDarkMode === null && systemDarkMode);

    if (isDark) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }

    updateThemeIcons(isDark);
}

function loadThemePreference() {
    // Handle config visibility
    const configVisible = localStorage.getItem('configVisible') !== 'false';
    if (configFields) {
        configFields.style.display = configVisible ? 'flex' : 'none';
    }
    if (toggleConfigBtn) {
        toggleConfigBtn.textContent = configVisible ? 'Hide Config' : 'Show Config';
    }

    // Initialize theme
    initializeTheme();
}

function updateThemeIcons(isDark) {
    if (themeIcon) {
        themeIcon.textContent = isDark ? '☀️' : '🌙';
    }
}

// Drag and drop handlers
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-blue-500', 'bg-blue-50', 'dark:bg-blue-900');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-blue-500', 'bg-blue-50', 'dark:bg-blue-900');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-blue-500', 'bg-blue-50', 'dark:bg-blue-900');
    handleFile(e.dataTransfer.files[0]);
});

// File select button click handler
fileSelectBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

// Make the entire drop zone clickable (except when clicking the button)
dropZone.addEventListener('click', (e) => {
    // Don't trigger if clicking the button directly
    if (e.target.id !== 'file-select-btn') {
        fileInput.click();
    }
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

    // Clear session number when file is cleared
    if (sessionNumberInput) {
        sessionNumberInput.value = '';
    }

    // Reset prompts to default when file is cleared
    resetPromptsToDefault();
    addMessage('system', '🗑️ File cleared and session reset.');
});

function handleFile(file) {
    if (!file) return;

    // Enhanced file validation with visual feedback
    const validation = validateFile(file);
    const validationDiv = document.getElementById('file-validation');

    if (validation.errors.length > 0) {
        validationDiv.textContent = validation.errors.join(', ');
        validationDiv.classList.remove('hidden', 'text-green-600', 'dark:text-green-400');
        validationDiv.classList.add('text-red-600', 'dark:text-red-400');
        addMessage('error', `File validation failed: ${validation.errors.join(', ')}`);
        return;
    }

    // Show success validation
    validationDiv.textContent = `✅ Valid ${validation.type} file (${formatFileSize(file.size)})`;
    validationDiv.classList.remove('hidden', 'text-red-600', 'dark:text-red-400', 'text-yellow-600', 'dark:text-yellow-400');
    validationDiv.classList.add('text-green-600', 'dark:text-green-400');

    fileName.textContent = file.name;
    fileInfo.classList.remove('hidden');
    addMessage('system', `📎 File selected: ${file.name} (${formatFileSize(file.size)})`);

    // Auto-detect and populate session number
    const detectedSession = extractSessionNumber(file.name);
    if (detectedSession && sessionNumberInput) {
        sessionNumberInput.value = detectedSession;
        addMessage('system', `📝 Auto-detected session: "${detectedSession}"`);
    } else if (sessionNumberInput && !sessionNumberInput.value) {
        // Clear previous value if no session detected and field is empty
        addMessage('system', '💡 Consider adding a session number for better story organization.');
    }

    // Add to recent files
    addToRecentFiles(file.name, file.size, file.type);

    // For text files, read content and enhance prompts
    if (file.type === 'text/plain' || file.name.toLowerCase().endsWith('.txt')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            if (content && content.length > 100) { // Only enhance if there's substantial content
                enhancePromptsWithContext(content, file.name);
                addMessage('system', '✨ Story refinement prompts have been enhanced based on your content!');
            }
        };
        reader.readAsText(file);
    } else {
        // For audio files, we'll enhance prompts after processing
        addMessage('system', '🎵 Audio file detected. Prompts will be enhanced after transcription.');
    }
}

function validateFile(file) {
    const errors = [];
    const maxSize = 5 * 1024 * 1024 * 1024; // 5GB for D&D session recordings
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/flac', 'text/plain'];
    const allowedExtensions = /\.(mp3|wav|m4a|ogg|flac|txt)$/i;

    if (file.size > maxSize) {
        errors.push(`File too large (${formatFileSize(file.size)} > ${formatFileSize(maxSize)})`);
    }

    if (!allowedTypes.includes(file.type) && !allowedExtensions.test(file.name)) {
        errors.push('Unsupported file type (use MP3, WAV, M4A, OGG, FLAC, or TXT)');
    }

    let type = 'unknown';
    if (file.type.startsWith('audio/') || /\.(mp3|wav|m4a|ogg|flac)$/i.test(file.name)) {
        type = 'audio';
    } else if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
        type = 'text';
    }

    return { errors, type };
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Extract session number from filename
function extractSessionNumber(filename) {
    if (!filename) return null;

    // Remove file extension for cleaner matching
    const nameWithoutExt = filename.replace(/\.[^/.]+$/, '');

    // Common patterns for D&D session naming
    const patterns = [
        // "Session 1", "Session-1", "Session_1", "session1"
        /(?:session[\s\-_]*)?(\d+)/i,

        // "Episode 42", "Episode-42", "Ep_42", "ep42"
        /(?:episode|ep)[\s\-_]*(\d+)/i,

        // "Chapter 5", "Chapter-5", "Ch_5", "ch5"
        /(?:chapter|ch)[\s\-_]*(\d+)/i,

        // "Part 3", "Part-3", "Pt_3", "pt3"
        /(?:part|pt)[\s\-_]*(\d+)/i,

        // "Campaign 2 Session 15" - gets the session number
        /campaign[\s\-_]*\d+[\s\-_]*session[\s\-_]*(\d+)/i,

        // "DnD_12" or "DND-12" - just the number
        /(?:dnd|d&d)[\s\-_]*(\d+)/i,

        // Just a number at the end: "Something_42"
        /[\s\-_](\d+)$/,

        // Number at the beginning: "42_Something"
        /^(\d+)[\s\-_]/
    ];

    for (const pattern of patterns) {
        const match = nameWithoutExt.match(pattern);
        if (match && match[1]) {
            const sessionNum = parseInt(match[1]);
            // Only accept reasonable session numbers (1-999)
            if (sessionNum >= 1 && sessionNum <= 999) {
                // Format nicely based on the pattern matched
                if (pattern.source.includes('episode|ep')) {
                    return `Episode ${sessionNum}`;
                } else if (pattern.source.includes('chapter|ch')) {
                    return `Chapter ${sessionNum}`;
                } else if (pattern.source.includes('part|pt')) {
                    return `Part ${sessionNum}`;
                } else {
                    return `Session ${sessionNum}`;
                }
            }
        }
    }

    return null; // No session number found
}

// Recent files management
function addToRecentFiles(fileName, fileSize, fileType) {
    const recentFiles = JSON.parse(localStorage.getItem('recentFiles') || '[]');
    const fileInfo = {
        name: fileName,
        size: fileSize,
        type: fileType,
        timestamp: new Date().toISOString()
    };

    // Remove if already exists
    const existingIndex = recentFiles.findIndex(f => f.name === fileName);
    if (existingIndex !== -1) {
        recentFiles.splice(existingIndex, 1);
    }

    // Add to beginning
    recentFiles.unshift(fileInfo);

    // Keep only last 5 files
    if (recentFiles.length > 5) {
        recentFiles.pop();
    }

    localStorage.setItem('recentFiles', JSON.stringify(recentFiles));
    updateRecentFilesDisplay();
}

function updateRecentFilesDisplay() {
    const recentFiles = JSON.parse(localStorage.getItem('recentFiles') || '[]');
    const recentFilesContainer = document.getElementById('recent-files');
    const recentFilesList = document.getElementById('recent-files-list');

    if (recentFiles.length === 0) {
        recentFilesContainer.classList.add('hidden');
        return;
    }

    recentFilesContainer.classList.remove('hidden');
    recentFilesList.innerHTML = '';

    recentFiles.forEach((file, index) => {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'flex items-center justify-between text-xs p-2 bg-gray-50 dark:bg-gray-700 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors';

        const fileIcon = file.type.startsWith('audio/') ? '🎵' : '📄';
        const timeAgo = getTimeAgo(new Date(file.timestamp));

        fileDiv.innerHTML = `
            <div class="flex items-center gap-2">
                <span>${fileIcon}</span>
                <span class="font-medium truncate max-w-[120px]" title="${file.name}">${file.name}</span>
                <span class="text-gray-500 dark:text-gray-400">(${formatFileSize(file.size)})</span>
            </div>
            <span class="text-gray-400 dark:text-gray-500">${timeAgo}</span>
        `;

        fileDiv.addEventListener('click', () => {
            addMessage('system', `📎 Recent file: ${file.name} - You can use this as reference for similar files.`);
        });

        recentFilesList.appendChild(fileDiv);
    });
}

function getTimeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

// Clear recent files
document.addEventListener('DOMContentLoaded', function() {
    const clearRecentBtn = document.getElementById('clear-recent-btn');
    if (clearRecentBtn) {
        clearRecentBtn.addEventListener('click', () => {
            if (confirm('Clear all recent files?')) {
                localStorage.removeItem('recentFiles');
                updateRecentFilesDisplay();
                addMessage('system', '🗑️ Recent files cleared');
            }
        });
    }

    // Load recent files on page load
    updateRecentFilesDisplay();
});

// File upload handler with retry logic and better error handling
uploadBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
        addMessage('error', 'Please select a file first.');
        return;
    }

    // Validate file size (5GB limit for D&D session recordings)
    const maxSize = 5 * 1024 * 1024 * 1024; // 5GB
    if (file.size > maxSize) {
        const maxSizeGB = Math.round(maxSize / 1024 / 1024 / 1024 * 10) / 10; // Round to 1 decimal
        addMessage('error', `File too large. Maximum size is ${maxSizeGB}GB for D&D session recordings.`);
        return;
    }

    // Validate file type
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/flac', 'text/plain'];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|ogg|flac|txt)$/i)) {
        addMessage('error', 'Unsupported file type. Please use MP3, WAV, M4A, OGG, FLAC, or TXT files.');
        return;
    }

    await uploadFileWithRetry(file, 3);
});

async function uploadFileWithRetry(file, maxRetries = 3) {
    const formData = new FormData();
    formData.append('file', file);

    // Add session number if provided
    const sessionNumber = sessionNumberInput ? sessionNumberInput.value.trim() : '';
    if (sessionNumber) {
        formData.append('sessionNumber', sessionNumber);
        console.log('Including session number:', sessionNumber);
    }

    // Show progress with file-type specific messaging
    uploadProgress.classList.remove('hidden');
    uploadBtn.disabled = true;

    const isAudioFile = file.type && file.type.startsWith('audio/');
    if (isAudioFile) {
        uploadBtn.textContent = 'Transcribing Audio...';
        addMessage('system', '🎵 Starting audio transcription (this may take several minutes for large files)...');
    } else {
        uploadBtn.textContent = 'Processing Text...';
        addMessage('system', '📄 Processing text file...');
    }
    uploadBtn.setAttribute('aria-busy', 'true');

    let retryCount = 0;

    while (retryCount < maxRetries) {
        try {
            // Simulate upload progress with stage indicators
            let progress = 0;
            let stage = 0;
            const stages = isAudioFile ?
                ['📤 Uploading file...', '🎵 Transcribing audio...', '📖 Generating story...', '✨ Finalizing...'] :
                ['📤 Uploading file...', '📄 Processing text...', '📖 Generating story...', '✨ Finalizing...'];

            const progressInterval = setInterval(() => {
                progress += Math.random() * 8 + 2; // Slower, more realistic progress

                // Update stage messages at different progress points
                const newStage = Math.floor(progress / 25);
                if (newStage !== stage && newStage < stages.length) {
                    stage = newStage;
                    addMessage('system', stages[stage]);
                }

                if (progress <= 90) {
                    uploadProgressBar.style.width = `${Math.min(progress, 90)}%`;
                    uploadProgressBar.setAttribute('aria-valuenow', Math.min(progress, 90));
                } else {
                    clearInterval(progressInterval);
                }
            }, 500); // Slower update interval for better UX

            const controller = new AbortController();
            // Longer timeout for audio files (15 minutes), shorter for text (5 minutes)
            const timeoutDuration = isAudioFile ? 900000 : 300000; // 15 min for audio, 5 min for text
            const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);

            // Show timeout warning for audio files
            if (isAudioFile) {
                addMessage('system', '⏱️ Audio processing timeout set to 15 minutes for large files.');
            }

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
                signal: controller.signal,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            clearTimeout(timeoutId);
            clearInterval(progressInterval);
            uploadProgressBar.style.width = '100%';
            uploadProgressBar.setAttribute('aria-valuenow', 100);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
                throw new Error(`Upload failed: ${errorData.error || response.statusText}`);
            }

            const data = await response.json();

            // Show different completion messages based on file type
            // Note: isAudioFile is already declared at the top of this function
            if (isAudioFile) {
                addMessage('success', '🎵 Audio transcription completed!');
                if (data.story) {
                    addMessage('success', '📖 Story generation completed successfully!');
                } else {
                    addMessage('system', '📝 Audio has been transcribed. Use the chat to generate your story.');
                }
            } else {
                addMessage('success', '📄 Text file processed successfully!');
                if (data.story) {
                    addMessage('success', '📖 Story generation completed!');
                }
            }

            // Store the session data globally
            currentSessionData = {
                sessionNumber: sessionNumberInput.value || 'Unknown',
                fileName: file.name,
                processedAt: new Date().toISOString(),
                story: data.story || null,
                transcription: data.transcription || null
            };

            // Store story and transcription globally for export
            if (data.story) {
                currentStory = data.story;
            }
            if (data.transcription) {
                currentTranscription = data.transcription;
            }

            // Enhance prompts with any story content returned
            if (data.story && data.story.length > 100) {
                enhancePromptsWithContext(data.story, file.name);
                addMessage('success', '✨ Story refinement prompts enhanced based on your content!');

                // Display the generated story in the chat
                addMessage('assistant', data.story);
            }

            // Show final completion message
            addMessage('success', '✅ Processing complete! Your D&D session is ready for refinement.');

            // Reset the button after processing with a longer delay for user to see completion
            setTimeout(() => {
                resetUploadButton();
                uploadProgress.classList.add('hidden');
            }, 3000);
            return; // Success, exit retry loop

        } catch (error) {
            retryCount++;
            console.error(`Upload attempt ${retryCount} failed:`, error);

            if (error.name === 'AbortError') {
                addMessage('error', 'Upload timed out. Please try again with a smaller file.');
                break;
            }

            if (retryCount >= maxRetries) {
                addMessage('error', `Upload failed after ${maxRetries} attempts: ${error.message}`);
            } else {
                addMessage('system', `Upload failed, retrying... (${retryCount}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, 1000 * retryCount)); // Exponential backoff
            }
        }
    }

    // Reset on failure
    resetUploadButton();
    uploadProgressBar.style.width = '0%';
    uploadProgress.classList.add('hidden');
}

function resetUploadButton() {
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Process File';
    uploadBtn.setAttribute('aria-busy', 'false');
}

// Configuration validation
function validateConfiguration() {
    const errors = [];

    if (confluenceUrl.value && !confluenceUrl.value.match(/^https?:\/\/.+/)) {
        errors.push('Confluence URL must be a valid URL');
    }

    if (confluenceParentPageId.value && !confluenceParentPageId.value.match(/^\d+$/)) {
        errors.push('Confluence Parent Page ID must be a number');
    }

    if (openaiApiKey.value && !openaiApiKey.value.startsWith('sk-')) {
        errors.push('OpenAI API Key should start with "sk-"');
    }

    return errors;
}

// Update input validation visual feedback
function updateInputValidation(input, isValid) {
    if (isValid) {
        input.classList.remove('border-red-500', 'dark:border-red-400');
        input.classList.add('border-green-500', 'dark:border-green-400');
    } else {
        input.classList.remove('border-green-500', 'dark:border-green-400');
        input.classList.add('border-red-500', 'dark:border-red-400');
    }
}

// Configuration handlers
saveConfigBtn.addEventListener('click', saveConfiguration);
clearConfigBtn.addEventListener('click', clearConfiguration);

// Export functionality
const exportPdfBtn = document.getElementById('export-pdf-btn');
const exportWordBtn = document.getElementById('export-word-btn');
const exportConfluenceBtn = document.getElementById('export-confluence-btn');

if (exportPdfBtn) {
    exportPdfBtn.addEventListener('click', exportToPDF);
}
if (exportWordBtn) {
    exportWordBtn.addEventListener('click', exportToWord);
}
if (exportConfluenceBtn) {
    exportConfluenceBtn.addEventListener('click', exportToConfluence);
}

// Add real-time validation
[confluenceUrl, confluenceApiToken, confluenceParentPageId, openaiApiKey].forEach(input => {
    input.addEventListener('input', () => {
        const errors = validateConfiguration();
        const inputName = input.id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const inputErrors = errors.filter(error => error.toLowerCase().includes(inputName.split(' ')[0].toLowerCase()));
        updateInputValidation(input, inputErrors.length === 0);
    });
});

function saveConfiguration() {
    const errors = validateConfiguration();

    if (errors.length > 0) {
        addMessage('error', `Configuration errors: ${errors.join(', ')}`);
        return;
    }

    // Show loading state
    const btnText = saveConfigBtn.querySelector('.config-btn-text');
    const btnLoading = saveConfigBtn.querySelector('.config-loading');

    if (btnText && btnLoading) {
        btnText.classList.add('hidden');
        btnLoading.classList.remove('hidden');
        saveConfigBtn.disabled = true;
    }

    // Simulate API call delay for better UX
    setTimeout(() => {
        const config = {
            confluenceUrl: confluenceUrl.value,
            confluenceApiToken: confluenceApiToken.value,
            confluenceParentPageId: confluenceParentPageId.value,
            openaiApiKey: openaiApiKey.value,
            savedAt: new Date().toISOString()
        };

        localStorage.setItem('dndStoryTellingConfig', JSON.stringify(config));
        addMessage('system', '✅ Configuration saved successfully!');

        // Reset button state
        if (btnText && btnLoading) {
            btnText.classList.remove('hidden');
            btnLoading.classList.add('hidden');
            saveConfigBtn.disabled = false;
        }
    }, 500);
}

function clearConfiguration() {
    if (confirm('Are you sure you want to clear all configuration? This cannot be undone.')) {
        localStorage.removeItem('dndStoryTellingConfig');
        confluenceUrl.value = '';
        confluenceApiToken.value = '';
        confluenceParentPageId.value = '';
        openaiApiKey.value = '';

        // Reset validation styling
        [confluenceUrl, confluenceApiToken, confluenceParentPageId, openaiApiKey].forEach(input => {
            input.classList.remove('border-red-500', 'dark:border-red-400', 'border-green-500', 'dark:border-green-400');
        });

        addMessage('system', '🗑️ Configuration cleared');
    }
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

        // Show last saved time if available
        if (config.savedAt) {
            const savedTime = new Date(config.savedAt).toLocaleString();
            addMessage('system', `Configuration loaded (saved: ${savedTime})`);
        }

        // Validate loaded configuration
        setTimeout(() => {
            [confluenceUrl, confluenceApiToken, confluenceParentPageId, openaiApiKey].forEach(input => {
                if (input.value) {
                    input.dispatchEvent(new Event('input'));
                }
            });
        }, 100);
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
    if (socket) {
        socket.emit('message', { text: message });
    } else {
        addMessage('system', 'Chat functionality not available - Socket.IO not connected');
    }
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
    messageDiv.className = `mb-3 p-3 rounded-lg border-l-4 ${
        type === 'user' ? 'bg-blue-50 dark:bg-blue-900 border-blue-500 ml-8' :
        type === 'system' ? 'bg-gray-50 dark:bg-gray-700 border-gray-400' :
        type === 'error' ? 'bg-red-50 dark:bg-red-900 border-red-500' :
        type === 'success' ? 'bg-green-50 dark:bg-green-900 border-green-500 font-medium' :
        'bg-indigo-50 dark:bg-indigo-900 border-indigo-500 mr-8'
    } transition-all duration-300 shadow-sm hover:shadow-md`;

    // Add timestamp for processing messages
    if (type === 'system' || type === 'success') {
        const timestamp = new Date().toLocaleTimeString();
        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'text-xs text-gray-500 dark:text-gray-400 float-right opacity-70';
        timestampSpan.textContent = timestamp;
        messageDiv.appendChild(timestampSpan);
    }

    const textSpan = document.createElement('span');
    textSpan.textContent = text;
    messageDiv.appendChild(textSpan);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Auto-scroll animation for success/system messages
    if (type === 'system' || type === 'success') {
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(10px)';
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);
    }
}

function setupSocketEventHandlers() {
    if (socket) {
        socket.on('response', (data) => {
            addMessage('assistant', data.text);

            // If this is a substantial response, consider it part of the session story
            if (data.text && data.text.length > 200) {
                // Append to current story if it exists, or create new story content
                if (currentStory) {
                    currentStory += "\n\n---\n\n" + data.text;
                } else {
                    currentStory = data.text;
                }

                // Update session data
                if (currentSessionData) {
                    currentSessionData.story = currentStory;
                    currentSessionData.processedAt = new Date().toISOString();
                }
            }
        });

        socket.on('error', (error) => {
            console.error('Socket error:', error);
            addMessage('error', 'Connection error occurred');
        });

        socket.on('connect', () => {
            console.log('Connected to server');
            addMessage('system', 'Connected to server');
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            addMessage('system', 'Disconnected from server');
        });

        console.log('Socket event handlers set up successfully');
    } else {
        console.warn('Cannot set up socket event handlers - socket is null');
    }
}

// Function to toggle info guides for configuration fields
function toggleInfoGuide(guideId) {
    const guide = document.getElementById(guideId);
    if (guide) {
        const isHidden = guide.classList.contains('hidden');

        // First hide all other open guides to keep UI clean
        const allGuides = document.querySelectorAll('[id$="-guide"]');
        allGuides.forEach(g => {
            if (g.id !== guideId) {
                g.classList.add('hidden');
            }
        });

        // Toggle the clicked guide
        if (isHidden) {
            guide.classList.remove('hidden');
            // Add smooth slide-in animation
            guide.style.opacity = '0';
            guide.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                guide.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                guide.style.opacity = '1';
                guide.style.transform = 'translateY(0)';
            }, 10);
        } else {
            // Smooth slide-out animation
            guide.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            guide.style.opacity = '0';
            guide.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                guide.classList.add('hidden');
                guide.style.transition = '';
                guide.style.opacity = '';
                guide.style.transform = '';
            }, 300);
        }
    }
}

// Make toggleInfoGuide globally accessible for onclick handlers
window.toggleInfoGuide = toggleInfoGuide;

// Context-aware prompt enhancement
function enhancePromptsWithContext(fileContent, fileName) {
    if (!fileContent || !fileName) return;

    console.log('Enhancing prompts with context from:', fileName);

    // Analyze content for context clues
    const hasDialogue = /["'].*?["']|said|replied|whispered|shouted|asked/gi.test(fileContent);
    const hasCombat = /attack|damage|hit|miss|spell|sword|battle|fight|combat/gi.test(fileContent);
    const hasWorldBuilding = /tavern|castle|forest|mountain|city|village|dungeon|temple/gi.test(fileContent);
    const hasCharacters = /character|player|NPC|party|hero|villain|companion/gi.test(fileContent);
    const hasTension = /danger|threat|suspense|fear|excitement|tension|dramatic/gi.test(fileContent);

    // Get all prompt options
    const promptOptions = document.querySelectorAll('.prompt-option');

    promptOptions.forEach(option => {
        const originalPrompt = option.getAttribute('data-prompt');
        let enhancedPrompt = originalPrompt;
        const promptType = option.querySelector('.font-semibold').textContent;

        // Enhance based on content analysis
        switch (promptType) {
            case 'Drama & Tension':
                if (hasCombat) {
                    enhancedPrompt += ' Pay special attention to the combat scenes and battles mentioned in the content.';
                }
                if (hasCharacters) {
                    enhancedPrompt += ' Focus on character conflicts and interpersonal drama.';
                }
                break;

            case 'Character Dialogue':
                if (hasDialogue) {
                    enhancedPrompt += ' Build upon the existing dialogue patterns and speech styles already present.';
                } else {
                    enhancedPrompt += ' Add more conversations where characters can express their personalities.';
                }
                break;

            case 'World Building':
                if (hasWorldBuilding) {
                    enhancedPrompt += ' Expand on the locations and settings already mentioned in the content.';
                } else {
                    enhancedPrompt += ' Create rich, immersive environments that complement the story.';
                }
                break;

            case 'Character Development':
                if (hasCharacters) {
                    enhancedPrompt += ' Focus on the characters already introduced and develop their arcs further.';
                } else {
                    enhancedPrompt += ' Introduce compelling characters with clear motivations and growth potential.';
                }
                break;

            case 'Combat & Action':
                if (hasCombat) {
                    enhancedPrompt += ' Enhance the existing battle sequences and make them more tactical and visceral.';
                } else {
                    enhancedPrompt += ' Add strategic combat encounters that fit naturally into the narrative.';
                }
                break;
        }

        // Update the data-prompt attribute with enhanced version
        option.setAttribute('data-prompt', enhancedPrompt);
    });

    console.log('Prompts enhanced based on content analysis');
}

// Function to reset prompts to original state
function resetPromptsToDefault() {
    const defaultPrompts = {
        'Drama & Tension': 'Add more dramatic tension and exciting moments to this scene. Focus on creating suspense, raising stakes, and making the action more engaging for readers.',
        'Character Dialogue': 'Enhance character dialogue and roleplay interactions. Add more personality, unique speech patterns, and meaningful conversations that reveal character motivations and relationships.',
        'World Building': 'Expand on world-building and environmental descriptions. Add rich details about locations, atmosphere, cultures, and the setting to make the world feel more immersive and alive.',
        'Character Development': 'Focus on character development and backstory elements. Dive deeper into character motivations, personal growth, relationships, and how their past influences their current actions.',
        'Combat & Action': 'Improve combat descriptions and action sequences. Make battles more vivid and tactical, describing movements, strategy, and the visceral impact of each attack and spell.'
    };

    const promptOptions = document.querySelectorAll('.prompt-option');
    promptOptions.forEach(option => {
        const promptType = option.querySelector('.font-semibold').textContent;
        if (defaultPrompts[promptType]) {
            option.setAttribute('data-prompt', defaultPrompts[promptType]);
        }
    });
}

// Export functions
function exportToPDF() {
    if (!currentStory && !currentTranscription) {
        addMessage('error', '❌ No content available to export. Please process a file first.');
        return;
    }

    try {
        // Create content for export
        const content = generateExportContent();

        // Create a new window/tab with the content for PDF generation
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>D&D Session Export - ${currentSessionData.sessionNumber || 'Session'}</title>
                <style>
                    body {
                        font-family: 'Times New Roman', serif;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        line-height: 1.6;
                        color: #333;
                    }
                    h1 { color: #8B4513; border-bottom: 2px solid #8B4513; }
                    h2 { color: #D2691E; margin-top: 30px; }
                    .metadata {
                        background-color: #f5f5f5;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }
                    .story-content {
                        text-align: justify;
                        text-indent: 2em;
                    }
                    .story-content p {
                        margin-bottom: 15px;
                    }
                    @media print {
                        body { margin: 0; }
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                ${content}
                <div class="no-print" style="text-align: center; margin-top: 30px;">
                    <button onclick="window.print()" style="background-color: #8B4513; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">Print to PDF</button>
                    <button onclick="window.close()" style="background-color: #666; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">Close</button>
                </div>
            </body>
            </html>
        `);
        printWindow.document.close();

        addMessage('success', '📄 PDF export window opened. Use your browser\'s print function to save as PDF.');

    } catch (error) {
        console.error('PDF export error:', error);
        addMessage('error', '❌ Failed to export PDF. Please try again.');
    }
}

function exportToWord() {
    if (!currentStory && !currentTranscription) {
        addMessage('error', '❌ No content available to export. Please process a file first.');
        return;
    }

    try {
        const content = generateExportContent(true); // Plain text format

        // Create and download text file (which can be opened in Word)
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        const sessionName = currentSessionData.sessionNumber || 'Session';
        const fileName = `DnD_${sessionName}_${new Date().toISOString().split('T')[0]}.txt`;
        a.download = fileName;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        addMessage('success', `📄 Text file "${fileName}" downloaded successfully! You can open this in Word for further editing.`);

    } catch (error) {
        console.error('Word export error:', error);
        addMessage('error', '❌ Failed to export file. Please try again.');
    }
}

function exportToConfluence() {
    if (!currentStory && !currentTranscription) {
        addMessage('error', '❌ No content available to export. Please process a file first.');
        return;
    }

    // Check if Confluence is configured
    const confluenceUrl = document.getElementById('confluence-url').value;
    const confluenceApiToken = document.getElementById('confluence-api-token').value;
    const confluenceParentPageId = document.getElementById('confluence-parent-page-id').value;

    if (!confluenceUrl || !confluenceApiToken || !confluenceParentPageId) {
        addMessage('error', '❌ Confluence configuration incomplete. Please configure all Confluence settings first.');
        return;
    }

    addMessage('system', '🔄 Exporting to Confluence...');

    try {
        // For now, just prepare the content and show what would be sent
        const sessionName = currentSessionData.sessionNumber || 'Session';
        const title = `D&D Session ${sessionName} - ${new Date().toISOString().split('T')[0]}`;

        // This would normally be sent to the backend for Confluence API integration
        addMessage('info', `📋 Ready to export "${title}" to Confluence. Backend integration needed for API calls.`);
        addMessage('system', '💡 For now, use the PDF or Word export options. Confluence integration coming soon!');

    } catch (error) {
        console.error('Confluence export error:', error);
        addMessage('error', '❌ Failed to export to Confluence. Please try again.');
    }
}

function generateExportContent(plainText = false) {
    const sessionNumber = currentSessionData.sessionNumber || 'Unknown Session';
    const fileName = currentSessionData.fileName || 'Unknown File';
    const processedDate = currentSessionData.processedAt ?
        new Date(currentSessionData.processedAt).toLocaleString() : 'Unknown Date';

    if (plainText) {
        // Plain text format
        let content = `D&D SESSION EXPORT\n`;
        content += `==================\n\n`;
        content += `Session: ${sessionNumber}\n`;
        content += `Original File: ${fileName}\n`;
        content += `Processed: ${processedDate}\n\n`;

        if (currentStory) {
            content += `GENERATED STORY\n`;
            content += `==============\n\n`;
            content += currentStory + '\n\n';
        }

        if (currentTranscription) {
            content += `TRANSCRIPTION\n`;
            content += `=============\n\n`;
            content += currentTranscription + '\n\n';
        }

        content += `\n---\nGenerated by D&D Story Generator\n`;
        return content;
    } else {
        // HTML format for PDF
        let content = `<h1>🎲 D&D Session Export</h1>`;
        content += `<div class="metadata">`;
        content += `<strong>Session:</strong> ${sessionNumber}<br>`;
        content += `<strong>Original File:</strong> ${fileName}<br>`;
        content += `<strong>Processed:</strong> ${processedDate}`;
        content += `</div>`;

        if (currentStory) {
            content += `<h2>📖 Generated Story</h2>`;
            content += `<div class="story-content">`;
            // Convert story to paragraphs
            const storyParagraphs = currentStory.split('\n\n').filter(p => p.trim());
            storyParagraphs.forEach(paragraph => {
                content += `<p>${paragraph.trim()}</p>`;
            });
            content += `</div>`;
        }

        if (currentTranscription) {
            content += `<h2>🎵 Original Transcription</h2>`;
            content += `<div class="story-content">`;
            // Convert transcription to paragraphs
            const transcriptionParagraphs = currentTranscription.split('\n\n').filter(p => p.trim());
            transcriptionParagraphs.forEach(paragraph => {
                content += `<p>${paragraph.trim()}</p>`;
            });
            content += `</div>`;
        }

        return content;
    }
}