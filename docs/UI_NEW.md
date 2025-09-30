# 🎨 User Interface Documentation

> **Comprehensive guide to the D&D Story Telling web interface, components, and user experience.**

This document provides detailed information about the web interface, user interactions, design patterns, and accessibility features of the D&D Story Telling application.

## 🌟 Interface Overview

### 🎯 **Core Design Principles**

- **🎲 D&D Theme**: Immersive fantasy aesthetic with dragon motifs and medieval colors
- **⚡ Performance First**: Fast loading, responsive interactions, optimized assets
- **♿ Accessibility**: WCAG 2.1 AA compliant, keyboard navigation, screen reader support
- **📱 Mobile Ready**: Progressive Web App with touch-optimized interactions
- **🎨 Modern UX**: Clean layouts, intuitive navigation, consistent interactions

### 🎪 **Visual Identity**

#### Color Palette
```css
:root {
    /* Primary Colors */
    --dragon-red: #dc2626;           /* Primary CTA, highlights */
    --dragon-gold: #f59e0b;          /* Secondary actions, accents */
    --dungeon-dark: #1f2937;         /* Headers, important text */
    --parchment: #fef7ed;            /* Background, content areas */
    
    /* Supporting Colors */
    --forest-green: #16a34a;         /* Success states */
    --wizard-blue: #3b82f6;          /* Information, links */
    --warning-amber: #f59e0b;        /* Warnings, cautions */
    --error-red: #ef4444;            /* Errors, critical actions */
    
    /* Neutral Colors */
    --stone-50: #fafaf9;
    --stone-100: #f5f5f4;
    --stone-200: #e7e5e4;
    --stone-300: #d6d3d1;
    --stone-500: #78716c;
    --stone-700: #44403c;
    --stone-900: #1c1917;
}
```

#### Typography
```css
/* Font Stack */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-display: 'Cinzel', serif;                    /* Headers, titles */
--font-mono: 'JetBrains Mono', 'Courier New', monospace;

/* Font Scales */
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.25rem;      /* 20px */
--text-2xl: 1.5rem;      /* 24px */
--text-3xl: 1.875rem;    /* 30px */
--text-4xl: 2.25rem;     /* 36px */
```

## 🏠 Page Layouts

### 🎮 **Main Dashboard (`/`)**

The primary interface where users interact with the story generation system.

#### Layout Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Progressive Web App metadata -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="manifest" href="/static/manifest.json">
    <link rel="icon" href="/static/images/favicon.ico">
</head>
<body class="bg-parchment text-dungeon-dark">
    <header class="app-header">
        <nav class="navigation-bar">
            <!-- Navigation components -->
        </nav>
    </header>
    
    <main class="main-content">
        <section class="hero-section">
            <!-- Welcome message and quick actions -->
        </section>
        
        <section class="upload-section">
            <!-- Audio upload interface -->
        </section>
        
        <section class="story-section">
            <!-- Generated stories display -->
        </section>
    </main>
    
    <footer class="app-footer">
        <!-- Links, copyright, version info -->
    </footer>
</body>
</html>
```

#### Key Components

##### 🎤 Audio Upload Area
```html
<div class="upload-area" data-testid="upload-area">
    <div class="upload-zone">
        <svg class="upload-icon" width="64" height="64">
            <!-- Microphone or upload icon -->
        </svg>
        <h3 class="upload-title">Upload Your Audio</h3>
        <p class="upload-description">
            Drag & drop your audio file or click to browse
        </p>
        <input type="file" 
               id="audio-upload" 
               accept="audio/*"
               class="file-input"
               aria-label="Select audio file">
        <button class="browse-button" 
                onclick="document.getElementById('audio-upload').click()">
            Browse Files
        </button>
    </div>
    
    <div class="upload-progress hidden" data-testid="progress-bar">
        <div class="progress-bar">
            <div class="progress-fill" style="width: 0%"></div>
        </div>
        <span class="progress-text">Uploading... 0%</span>
    </div>
</div>
```

##### 📚 Story Display Area
```html
<div class="story-container">
    <header class="story-header">
        <h2 class="story-title">Your Generated Story</h2>
        <div class="story-actions">
            <button class="action-button save-button">
                <svg class="icon"><!-- Save icon --></svg>
                Save Story
            </button>
            <button class="action-button share-button">
                <svg class="icon"><!-- Share icon --></svg>
                Share
            </button>
            <button class="action-button export-button">
                <svg class="icon"><!-- Export icon --></svg>
                Export
            </button>
        </div>
    </header>
    
    <div class="story-content">
        <div class="story-metadata">
            <span class="metadata-item">
                <strong>Length:</strong> <span id="word-count">0</span> words
            </span>
            <span class="metadata-item">
                <strong>Generated:</strong> <time id="generation-time"></time>
            </span>
        </div>
        
        <div class="story-text" id="generated-story">
            <!-- Generated story content -->
        </div>
    </div>
</div>
```

### 💬 **Chat Interface (`/chat`)**

Real-time conversation interface for interactive story development.

#### WebSocket Integration
```javascript
class ChatInterface {
    constructor() {
        this.websocket = null;
        this.messageQueue = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.initializeWebSocket();
        this.setupEventListeners();
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = (event) => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.flushMessageQueue();
        };
        
        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleIncomingMessage(message);
        };
        
        this.websocket.onclose = (event) => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    sendMessage(message) {
        if (this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        } else {
            this.messageQueue.push(message);
        }
    }
    
    handleIncomingMessage(message) {
        const chatContainer = document.getElementById('chat-messages');
        const messageElement = this.createMessageElement(message);
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}
```

#### Chat UI Components
```html
<div class="chat-container">
    <header class="chat-header">
        <h1 class="chat-title">
            <svg class="dragon-icon"><!-- Dragon icon --></svg>
            Story Chat
        </h1>
        <div class="chat-status">
            <span class="status-indicator online" id="connection-status"></span>
            <span class="status-text">Connected</span>
        </div>
    </header>
    
    <div class="chat-messages" id="chat-messages">
        <!-- Messages populated dynamically -->
    </div>
    
    <div class="chat-input-area">
        <div class="input-container">
            <textarea id="message-input" 
                      class="message-input"
                      placeholder="Describe your story ideas..."
                      rows="3"
                      maxlength="1000"></textarea>
            <button id="send-button" 
                    class="send-button"
                    aria-label="Send message">
                <svg class="send-icon"><!-- Send icon --></svg>
            </button>
        </div>
        
        <div class="input-actions">
            <button class="action-btn" id="attach-audio">
                <svg class="icon"><!-- Microphone icon --></svg>
                Record Audio
            </button>
            <button class="action-btn" id="clear-chat">
                <svg class="icon"><!-- Clear icon --></svg>
                Clear Chat
            </button>
            <span class="character-count">
                <span id="char-count">0</span>/1000
            </span>
        </div>
    </div>
</div>
```

## 🎛️ Interactive Components

### 🔄 **Loading States**

#### Skeleton Loaders
```html
<div class="skeleton-loader">
    <div class="skeleton-header">
        <div class="skeleton-line skeleton-title"></div>
        <div class="skeleton-line skeleton-subtitle"></div>
    </div>
    <div class="skeleton-content">
        <div class="skeleton-line"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line skeleton-short"></div>
    </div>
</div>
```

```css
.skeleton-loader {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.skeleton-line {
    height: 1rem;
    background-color: var(--stone-200);
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
}

.skeleton-title { height: 1.5rem; width: 60%; }
.skeleton-subtitle { height: 1rem; width: 40%; }
.skeleton-short { width: 80%; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

#### Progress Indicators
```html
<div class="progress-container">
    <div class="progress-bar">
        <div class="progress-fill" 
             style="width: 75%"
             role="progressbar"
             aria-valuenow="75"
             aria-valuemin="0"
             aria-valuemax="100"></div>
    </div>
    <div class="progress-steps">
        <span class="step completed">Upload</span>
        <span class="step completed">Process</span>
        <span class="step active">Generate</span>
        <span class="step">Complete</span>
    </div>
</div>
```

### 🎨 **Form Components**

#### Custom File Upload
```html
<div class="file-upload-wrapper">
    <input type="file" 
           id="file-input"
           class="file-input-hidden"
           accept="audio/*"
           multiple>
    
    <label for="file-input" class="file-upload-label">
        <div class="upload-content">
            <svg class="upload-icon"><!-- Upload icon --></svg>
            <span class="upload-text">Choose files or drag here</span>
            <span class="upload-hint">Supports MP3, WAV, M4A files</span>
        </div>
    </label>
    
    <div class="file-list" id="selected-files">
        <!-- Selected files appear here -->
    </div>
</div>
```

#### Form Validation
```javascript
class FormValidator {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.errors = new Map();
        this.setupValidation();
    }
    
    setupValidation() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Real-time validation
        const inputs = this.form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }
    
    validateField(field) {
        const value = field.value.trim();
        const fieldName = field.name;
        let isValid = true;
        let errorMessage = '';
        
        // Required field validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }
        
        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }
        
        // File size validation
        if (field.type === 'file' && field.files.length > 0) {
            const maxSize = 50 * 1024 * 1024; // 50MB
            Array.from(field.files).forEach(file => {
                if (file.size > maxSize) {
                    isValid = false;
                    errorMessage = 'File size must be less than 50MB';
                }
            });
        }
        
        this.displayFieldValidation(field, isValid, errorMessage);
        return isValid;
    }
    
    displayFieldValidation(field, isValid, errorMessage) {
        const errorElement = document.getElementById(`${field.name}-error`);
        
        if (isValid) {
            field.classList.remove('error');
            field.classList.add('valid');
            if (errorElement) errorElement.textContent = '';
        } else {
            field.classList.remove('valid');
            field.classList.add('error');
            if (errorElement) errorElement.textContent = errorMessage;
        }
    }
}
```

### 🔔 **Notification System**

#### Toast Notifications
```javascript
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = new Map();
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.setAttribute('aria-live', 'polite');
        document.body.appendChild(container);
        return container;
    }
    
    show(message, type = 'info', duration = 5000) {
        const id = Date.now().toString();
        const notification = this.createNotification(id, message, type);
        
        this.container.appendChild(notification);
        this.notifications.set(id, notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
        
        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(id), duration);
        }
        
        return id;
    }
    
    createNotification(id, message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.setAttribute('data-id', id);
        notification.setAttribute('role', 'alert');
        
        notification.innerHTML = `
            <div class="notification-content">
                <svg class="notification-icon">${this.getIcon(type)}</svg>
                <span class="notification-message">${message}</span>
                <button class="notification-close" 
                        onclick="notifications.dismiss('${id}')"
                        aria-label="Close notification">
                    <svg class="icon"><!-- Close icon --></svg>
                </button>
            </div>
        `;
        
        return notification;
    }
    
    dismiss(id) {
        const notification = this.notifications.get(id);
        if (notification) {
            notification.classList.add('hide');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications.delete(id);
            }, 300);
        }
    }
}

// Global notification instance
const notifications = new NotificationManager();
```

## 📱 Responsive Design

### 🖥️ **Breakpoint System**

```css
/* Mobile First Approach */
:root {
    --breakpoint-sm: 640px;      /* Small devices */
    --breakpoint-md: 768px;      /* Medium devices */
    --breakpoint-lg: 1024px;     /* Large devices */
    --breakpoint-xl: 1280px;     /* Extra large devices */
    --breakpoint-2xl: 1536px;    /* 2X Large devices */
}

/* Layout Grid */
.container {
    width: 100%;
    padding-left: 1rem;
    padding-right: 1rem;
    margin-left: auto;
    margin-right: auto;
}

@media (min-width: 640px) {
    .container { max-width: 640px; }
}

@media (min-width: 768px) {
    .container { max-width: 768px; }
}

@media (min-width: 1024px) {
    .container { max-width: 1024px; }
}

@media (min-width: 1280px) {
    .container { max-width: 1280px; }
}
```

### 📲 **Mobile Optimizations**

#### Touch-Friendly Interactions
```css
/* Minimum touch target sizes */
.button, .tap-target {
    min-height: 44px;
    min-width: 44px;
    padding: 0.75rem 1rem;
}

/* Touch feedback */
.button:active {
    transform: translateY(1px);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Prevent zoom on input focus */
input[type="text"],
input[type="email"],
input[type="password"],
textarea {
    font-size: 16px; /* Prevents zoom on iOS */
}

/* Optimized for thumb navigation */
.mobile-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    background: var(--parchment);
    border-top: 1px solid var(--stone-200);
}
```

#### Progressive Web App Features
```javascript
// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

// Install Prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install button
    const installButton = document.getElementById('install-button');
    installButton.style.display = 'block';
    
    installButton.addEventListener('click', () => {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            }
            deferredPrompt = null;
        });
    });
});
```

## ♿ Accessibility Features

### 🎯 **WCAG 2.1 AA Compliance**

#### Semantic HTML Structure
```html
<main role="main" aria-label="Story generation interface">
    <section aria-labelledby="upload-heading">
        <h2 id="upload-heading">Audio Upload</h2>
        <div class="upload-area" 
             role="button"
             tabindex="0"
             aria-describedby="upload-instructions"
             aria-label="Upload audio file">
            
            <p id="upload-instructions">
                Upload an audio file to generate your D&D story. 
                Supported formats: MP3, WAV, M4A. Maximum size: 50MB.
            </p>
            
            <input type="file" 
                   id="audio-input"
                   accept="audio/*"
                   aria-describedby="file-requirements">
            
            <div id="file-requirements" class="sr-only">
                Audio files only. Maximum 50 megabytes.
            </div>
        </div>
    </section>
    
    <section aria-labelledby="story-heading" aria-live="polite">
        <h2 id="story-heading">Generated Story</h2>
        <div id="story-content" 
             role="article"
             aria-label="Generated D&D story content">
            <!-- Story content -->
        </div>
    </section>
</main>
```

#### Keyboard Navigation
```javascript
class KeyboardNavigation {
    constructor() {
        this.focusableElements = [
            'button',
            '[href]',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
        ];
        
        this.setupKeyboardTraps();
        this.setupNavigationHelpers();
    }
    
    setupKeyboardTraps() {
        // Modal keyboard trap
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal.active');
                if (modal) {
                    this.trapFocusInModal(e, modal);
                }
            }
            
            // Escape key handling
            if (e.key === 'Escape') {
                this.handleEscapeKey();
            }
        });
    }
    
    trapFocusInModal(event, modal) {
        const focusableElements = modal.querySelectorAll(
            this.focusableElements.join(',')
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (event.shiftKey) {
            if (document.activeElement === firstElement) {
                lastElement.focus();
                event.preventDefault();
            }
        } else {
            if (document.activeElement === lastElement) {
                firstElement.focus();
                event.preventDefault();
            }
        }
    }
    
    setupNavigationHelpers() {
        // Skip to main content link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link';
        skipLink.textContent = 'Skip to main content';
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Focus indicators
        document.addEventListener('keydown', () => {
            document.body.classList.add('keyboard-navigation');
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    }
}
```

#### Screen Reader Support
```css
/* Screen reader only text */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

/* Focus indicators for keyboard navigation */
.keyboard-navigation *:focus {
    outline: 2px solid var(--wizard-blue);
    outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --stone-200: #000000;
        --stone-700: #ffffff;
        --dragon-red: #ff0000;
        --forest-green: #00ff00;
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

## 🎨 Animation & Transitions

### ✨ **Micro-Interactions**

#### Hover Effects
```css
.button {
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.2),
        transparent
    );
    transition: left 0.5s;
}

.button:hover::before {
    left: 100%;
}

.button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

#### Loading Animations
```css
@keyframes spin {
    to { transform: rotate(360deg); }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.loading-spinner {
    animation: spin 1s linear infinite;
}

.pulse-animation {
    animation: pulse 2s ease-in-out infinite;
}

.slide-in {
    animation: slideIn 0.3s ease-out;
}
```

### 🎭 **Page Transitions**

```javascript
class PageTransitions {
    constructor() {
        this.isTransitioning = false;
        this.setupTransitions();
    }
    
    setupTransitions() {
        // Intercept navigation
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (link && !link.hasAttribute('target')) {
                e.preventDefault();
                this.navigateTo(link.href);
            }
        });
        
        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            this.navigateTo(window.location.href, false);
        });
    }
    
    async navigateTo(url, updateHistory = true) {
        if (this.isTransitioning) return;
        
        this.isTransitioning = true;
        
        // Start exit animation
        document.body.classList.add('page-transitioning');
        
        try {
            // Fetch new content
            const response = await fetch(url);
            const html = await response.text();
            
            // Wait for exit animation
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // Update content
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');
            
            document.title = newDoc.title;
            document.getElementById('main-content').innerHTML = 
                newDoc.getElementById('main-content').innerHTML;
            
            // Update history
            if (updateHistory) {
                history.pushState(null, '', url);
            }
            
            // Start enter animation
            document.body.classList.remove('page-transitioning');
            document.body.classList.add('page-entering');
            
            setTimeout(() => {
                document.body.classList.remove('page-entering');
                this.isTransitioning = false;
            }, 300);
            
        } catch (error) {
            console.error('Navigation failed:', error);
            this.isTransitioning = false;
            document.body.classList.remove('page-transitioning');
        }
    }
}
```

## 🛠️ Development Tools

### 🧪 **UI Testing**

#### Playwright UI Tests
```python
# tests/ui/test_interface.py
import pytest
from playwright.async_api import async_playwright, expect

@pytest.mark.asyncio
async def test_responsive_design():
    \"\"\"Test responsive design across different screen sizes.\"\"\"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Test desktop view
        await page.set_viewport_size({"width": 1280, "height": 720})
        await page.goto("http://localhost:8000")
        
        # Verify desktop layout
        upload_area = page.locator("[data-testid='upload-area']")
        await expect(upload_area).to_be_visible()
        
        # Test mobile view
        await page.set_viewport_size({"width": 375, "height": 667})
        
        # Verify mobile adaptations
        mobile_nav = page.locator(".mobile-nav")
        await expect(mobile_nav).to_be_visible()
        
        await browser.close()

@pytest.mark.asyncio
async def test_accessibility():
    \"\"\"Test accessibility features.\"\"\"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://localhost:8000")
        
        # Test keyboard navigation
        await page.keyboard.press("Tab")
        focused_element = await page.evaluate("document.activeElement.tagName")
        assert focused_element in ["BUTTON", "A", "INPUT"]
        
        # Test ARIA labels
        upload_button = page.locator("[aria-label='Upload audio file']")
        await expect(upload_button).to_be_visible()
        
        # Test skip link
        await page.keyboard.press("Tab")
        skip_link = page.locator(".skip-link:focus")
        await expect(skip_link).to_be_visible()
        
        await browser.close()
```

### 🎨 **Component Library**

#### Storybook Integration
```javascript
// .storybook/main.js
module.exports = {
    stories: ['../app/static/components/**/*.stories.@(js|jsx|ts|tsx)'],
    addons: [
        '@storybook/addon-essentials',
        '@storybook/addon-a11y',
        '@storybook/addon-viewport'
    ]
};

// app/static/components/Button.stories.js
export default {
    title: 'Components/Button',
    component: 'button',
    parameters: {
        docs: {
            description: {
                component: 'Primary action button with D&D theming'
            }
        }
    },
    argTypes: {
        variant: {
            control: { type: 'select' },
            options: ['primary', 'secondary', 'danger']
        },
        size: {
            control: { type: 'select' },
            options: ['small', 'medium', 'large']
        }
    }
};

export const Primary = {
    args: {
        variant: 'primary',
        children: 'Generate Story'
    }
};

export const Secondary = {
    args: {
        variant: 'secondary',
        children: 'Save Draft'
    }
};
```

## 📊 Performance Optimization

### ⚡ **Loading Performance**

#### Image Optimization
```html
<!-- Responsive images with lazy loading -->
<img src="/static/images/hero-small.webp"
     srcset="/static/images/hero-small.webp 400w,
             /static/images/hero-medium.webp 800w,
             /static/images/hero-large.webp 1200w"
     sizes="(max-width: 768px) 100vw,
            (max-width: 1024px) 50vw,
            25vw"
     alt="D&D Story Telling Interface"
     loading="lazy"
     decoding="async">

<!-- Critical path images -->
<link rel="preload" 
      href="/static/images/logo.webp" 
      as="image" 
      type="image/webp">
```

#### Resource Optimization
```html
<!-- Critical CSS inline -->
<style>
    /* Critical above-the-fold styles */
    body { font-family: Inter, sans-serif; }
    .hero { background: var(--parchment); }
</style>

<!-- Non-critical CSS deferred -->
<link rel="preload" 
      href="/static/css/main.css" 
      as="style" 
      onload="this.onload=null;this.rel='stylesheet'">

<!-- JavaScript modules -->
<script type="module" src="/static/js/main.js"></script>
<script nomodule src="/static/js/main.legacy.js"></script>
```

### 📈 **Runtime Performance**

#### Virtual Scrolling for Large Lists
```javascript
class VirtualScroller {
    constructor(container, items, renderItem) {
        this.container = container;
        this.items = items;
        this.renderItem = renderItem;
        this.itemHeight = 80; // Estimated item height
        this.visibleItems = Math.ceil(container.clientHeight / this.itemHeight) + 2;
        this.scrollTop = 0;
        
        this.setupScrolling();
        this.render();
    }
    
    setupScrolling() {
        this.container.addEventListener('scroll', () => {
            this.scrollTop = this.container.scrollTop;
            this.render();
        });
    }
    
    render() {
        const startIndex = Math.floor(this.scrollTop / this.itemHeight);
        const endIndex = Math.min(startIndex + this.visibleItems, this.items.length);
        
        const offsetY = startIndex * this.itemHeight;
        
        // Clear container
        this.container.innerHTML = '';
        
        // Create spacer for scrollbar
        const spacer = document.createElement('div');
        spacer.style.height = `${this.items.length * this.itemHeight}px`;
        this.container.appendChild(spacer);
        
        // Create visible items container
        const visibleContainer = document.createElement('div');
        visibleContainer.style.transform = `translateY(${offsetY}px)`;
        visibleContainer.style.position = 'absolute';
        visibleContainer.style.top = '0';
        visibleContainer.style.width = '100%';
        
        // Render visible items
        for (let i = startIndex; i < endIndex; i++) {
            const item = this.renderItem(this.items[i], i);
            visibleContainer.appendChild(item);
        }
        
        this.container.appendChild(visibleContainer);
    }
}
```

## 🔍 Browser Support

### 🌐 **Compatibility Matrix**

| Feature | Chrome | Firefox | Safari | Edge | Mobile |
|---------|--------|---------|--------|------|--------|
| WebSocket | ✅ 16+ | ✅ 11+ | ✅ 7+ | ✅ 12+ | ✅ |
| Web Audio API | ✅ 34+ | ✅ 25+ | ✅ 14.1+ | ✅ 79+ | ✅ |
| File API | ✅ 13+ | ✅ 6+ | ✅ 6+ | ✅ 10+ | ✅ |
| Service Worker | ✅ 45+ | ✅ 44+ | ✅ 11.1+ | ✅ 17+ | ✅ |
| CSS Grid | ✅ 57+ | ✅ 52+ | ✅ 10.1+ | ✅ 16+ | ✅ |

### 🔧 **Polyfills & Fallbacks**

```javascript
// Feature detection and polyfills
class FeatureSupport {
    static checkWebSocketSupport() {
        return 'WebSocket' in window;
    }
    
    static checkFileAPISupport() {
        return window.File && window.FileReader && window.FileList;
    }
    
    static checkServiceWorkerSupport() {
        return 'serviceWorker' in navigator;
    }
    
    static loadPolyfillsIfNeeded() {
        const polyfills = [];
        
        if (!this.checkWebSocketSupport()) {
            polyfills.push('/static/js/polyfills/websocket.js');
        }
        
        if (!this.checkFileAPISupport()) {
            polyfills.push('/static/js/polyfills/fileapi.js');
        }
        
        if (polyfills.length > 0) {
            return Promise.all(
                polyfills.map(url => this.loadScript(url))
            );
        }
        
        return Promise.resolve();
    }
    
    static loadScript(url) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = url;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
}

// Initialize with polyfill support
FeatureSupport.loadPolyfillsIfNeeded().then(() => {
    // Initialize application
    new App();
});
```

---

<div align="center">

**🎨 Beautiful, Accessible, and Performant UI 🎨**

*Crafted with attention to detail for the ultimate D&D storytelling experience.*

[🚀 View Live Demo](https://dndstorytelling.com) | [🎨 Component Library](https://storybook.dndstorytelling.com) | [♿ Accessibility Report](https://accessibility.dndstorytelling.com)

</div>