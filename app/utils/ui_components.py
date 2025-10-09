"""
Enhanced UI utilities for better user experience.
Includes progress indicators, error handling, accessibility features, and responsive design.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class AlertType(Enum):
    """UI alert types with semantic meaning."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ToastPosition(Enum):
    """Toast notification positions."""
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"


@dataclass
class UIAlert:
    """UI alert configuration."""
    message: str
    alert_type: AlertType
    title: Optional[str] = None
    dismissible: bool = True
    auto_dismiss: bool = False
    timeout_ms: int = 5000
    show_icon: bool = True
    actions: List[Dict[str, Any]] = None


@dataclass
class ProgressConfig:
    """Progress indicator configuration."""
    current_value: int = 0
    max_value: int = 100
    show_percentage: bool = True
    show_label: bool = True
    animated: bool = True
    color_scheme: str = "primary"
    size: str = "medium"  # small, medium, large


class UIComponentGenerator:
    """Generate enhanced UI components with accessibility and responsiveness."""

    def __init__(self):
        self.component_id_counter = 0

    def _generate_id(self, prefix: str = "component") -> str:
        """Generate unique component ID."""
        self.component_id_counter += 1
        return f"{prefix}_{self.component_id_counter}_{int(time.time())}"

    def create_progress_bar(self, config: ProgressConfig, label: str = None) -> str:
        """Create an accessible progress bar component."""
        component_id = self._generate_id("progress")
        percentage = (config.current_value / config.max_value) * 100 if config.max_value > 0 else 0

        # Determine color class based on percentage
        color_class = self._get_progress_color_class(percentage, config.color_scheme)

        # Generate label text
        if label:
            label_text = label
        elif config.show_percentage:
            label_text = f"{percentage:.1f}%"
        else:
            label_text = f"{config.current_value} / {config.max_value}"

        html = f"""
        <div class="progress-container progress-{config.size}" role="progressbar"
             aria-valuenow="{config.current_value}"
             aria-valuemin="0"
             aria-valuemax="{config.max_value}"
             aria-label="{label_text}">

            {f'<div class="progress-label" id="{component_id}_label">{label_text}</div>' if config.show_label else ''}

            <div class="progress-track">
                <div class="progress-fill {color_class} {'progress-animated' if config.animated else ''}"
                     style="width: {percentage:.1f}%"
                     aria-describedby="{component_id}_label">
                </div>
            </div>

            <div class="sr-only" aria-live="polite">
                Progress: {label_text}
            </div>
        </div>
        """

        return html.strip()

    def create_loading_spinner(self, size: str = "medium", message: str = "Loading...") -> str:
        """Create an accessible loading spinner."""
        component_id = self._generate_id("spinner")

        html = f"""
        <div class="loading-container loading-{size}" role="status" aria-live="polite">
            <div class="loading-spinner" aria-hidden="true">
                <div class="spinner-ring"></div>
                <div class="spinner-ring"></div>
                <div class="spinner-ring"></div>
            </div>
            <div class="loading-message" id="{component_id}_message">
                {message}
            </div>
            <div class="sr-only">
                Loading content, please wait...
            </div>
        </div>
        """

        return html.strip()

    def create_alert_component(self, alert: UIAlert) -> str:
        """Create an accessible alert component."""
        component_id = self._generate_id("alert")

        # Icon mapping
        icon_map = {
            AlertType.SUCCESS: "✓",
            AlertType.INFO: "ℹ",
            AlertType.WARNING: "⚠",
            AlertType.ERROR: "✕"
        }

        # ARIA role mapping
        role_map = {
            AlertType.SUCCESS: "status",
            AlertType.INFO: "status",
            AlertType.WARNING: "alert",
            AlertType.ERROR: "alert"
        }

        icon = icon_map.get(alert.alert_type, "ℹ")
        role = role_map.get(alert.alert_type, "status")

        # Generate actions HTML
        actions_html = ""
        if alert.actions:
            action_buttons = []
            for action in alert.actions:
                action_buttons.append(f"""
                    <button class="alert-action-btn"
                            onclick="{action.get('onclick', '')}"
                            type="button">
                        {action.get('label', 'Action')}
                    </button>
                """)
            actions_html = f'<div class="alert-actions">{"".join(action_buttons)}</div>'

        # Auto-dismiss script
        auto_dismiss_script = ""
        if alert.auto_dismiss:
            auto_dismiss_script = f"""
            <script>
                setTimeout(function() {{
                    const alertEl = document.getElementById('{component_id}');
                    if (alertEl) {{
                        alertEl.style.opacity = '0';
                        setTimeout(() => alertEl.remove(), 300);
                    }}
                }}, {alert.timeout_ms});
            </script>
            """

        html = f"""
        <div class="alert alert-{alert.alert_type.value} {'alert-dismissible' if alert.dismissible else ''}"
             id="{component_id}"
             role="{role}"
             aria-live="{'assertive' if alert.alert_type in [AlertType.ERROR, AlertType.WARNING] else 'polite'}">

            <div class="alert-content">
                {f'<span class="alert-icon" aria-hidden="true">{icon}</span>' if alert.show_icon else ''}

                <div class="alert-text">
                    {f'<div class="alert-title">{alert.title}</div>' if alert.title else ''}
                    <div class="alert-message">{alert.message}</div>
                </div>

                {actions_html}

                {f'''<button class="alert-close" onclick="this.parentElement.parentElement.remove()"
                           type="button" aria-label="Close alert">
                        <span aria-hidden="true">&times;</span>
                     </button>''' if alert.dismissible else ''}
            </div>
        </div>
        {auto_dismiss_script}
        """

        return html.strip()

    def create_file_upload_area(
        self,
        accept_types: List[str] = None,
        max_size_mb: int = 10,
        multiple: bool = False
    ) -> str:
        """Create an enhanced file upload area with drag-and-drop."""
        component_id = self._generate_id("upload")
        accept_attr = ",".join(accept_types) if accept_types else "*/*"

        html = f"""
        <div class="file-upload-container" id="{component_id}">
            <div class="file-upload-area"
                 ondragover="handleDragOver(event)"
                 ondragleave="handleDragLeave(event)"
                 ondrop="handleFileDrop(event, '{component_id}')">

                <input type="file"
                       id="{component_id}_input"
                       class="file-input sr-only"
                       accept="{accept_attr}"
                       {'multiple' if multiple else ''}
                       onchange="handleFileSelect(event, '{component_id}')">

                <div class="upload-content">
                    <div class="upload-icon" aria-hidden="true">📁</div>
                    <div class="upload-text">
                        <p><strong>Click to upload</strong> or drag and drop</p>
                        <p class="upload-hint">
                            {f"Accepted: {', '.join(accept_types)}" if accept_types else "All file types accepted"}
                            (Max: {max_size_mb}MB)
                        </p>
                    </div>
                    <button type="button"
                            class="upload-button"
                            onclick="document.getElementById('{component_id}_input').click()">
                        Choose File{'s' if multiple else ''}
                    </button>
                </div>
            </div>

            <div class="upload-progress" id="{component_id}_progress" style="display: none;">
                <div class="progress-bar">
                    <div class="progress-fill" id="{component_id}_progress_fill"></div>
                </div>
                <div class="progress-text" id="{component_id}_progress_text">Uploading...</div>
            </div>

            <div class="upload-results" id="{component_id}_results"></div>
        </div>

        <script>
            function handleDragOver(event) {{
                event.preventDefault();
                event.currentTarget.classList.add('drag-over');
            }}

            function handleDragLeave(event) {{
                event.currentTarget.classList.remove('drag-over');
            }}

            function handleFileDrop(event, containerId) {{
                event.preventDefault();
                event.currentTarget.classList.remove('drag-over');

                const files = event.dataTransfer.files;
                processFiles(files, containerId);
            }}

            function handleFileSelect(event, containerId) {{
                const files = event.target.files;
                processFiles(files, containerId);
            }}

            function processFiles(files, containerId) {{
                const results = document.getElementById(containerId + '_results');
                results.innerHTML = '';

                Array.from(files).forEach(file => {{
                    const fileInfo = document.createElement('div');
                    fileInfo.className = 'file-info';
                    fileInfo.innerHTML = `
                        <span class="file-name">${{file.name}}</span>
                        <span class="file-size">${{formatFileSize(file.size)}}</span>
                        <span class="file-status">Ready to upload</span>
                    `;
                    results.appendChild(fileInfo);
                }});
            }}

            function formatFileSize(bytes) {{
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }}
        </script>
        """

        return html.strip()

    def create_toast_notification(
        self,
        message: str,
        toast_type: AlertType = AlertType.INFO,
        position: ToastPosition = ToastPosition.TOP_RIGHT,
        auto_dismiss: bool = True,
        duration_ms: int = 4000
    ) -> str:
        """Create a toast notification."""
        component_id = self._generate_id("toast")

        icon_map = {
            AlertType.SUCCESS: "✓",
            AlertType.INFO: "ℹ",
            AlertType.WARNING: "⚠",
            AlertType.ERROR: "✕"
        }

        icon = icon_map.get(toast_type, "ℹ")

        html = f"""
        <div class="toast toast-{toast_type.value} toast-{position.value}"
             id="{component_id}"
             role="status"
             aria-live="polite">
            <div class="toast-content">
                <span class="toast-icon" aria-hidden="true">{icon}</span>
                <span class="toast-message">{message}</span>
                <button class="toast-close"
                        onclick="removeToast('{component_id}')"
                        aria-label="Close notification">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
        </div>

        <script>
            // Add toast to container
            let toastContainer = document.getElementById('toast-container-{position.value}');
            if (!toastContainer) {{
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container-{position.value}';
                toastContainer.className = 'toast-container toast-container-{position.value}';
                document.body.appendChild(toastContainer);
            }}

            const toastElement = document.getElementById('{component_id}');
            toastContainer.appendChild(toastElement);

            // Auto dismiss
            {f"setTimeout(() => removeToast('{component_id}'), {duration_ms});" if auto_dismiss else ""}

            function removeToast(toastId) {{
                const toast = document.getElementById(toastId);
                if (toast) {{
                    toast.style.opacity = '0';
                    toast.style.transform = 'translateX(100%)';
                    setTimeout(() => toast.remove(), 300);
                }}
            }}
        </script>
        """

        return html.strip()

    def create_modal_dialog(
        self,
        title: str,
        content: str,
        modal_id: str = None,
        size: str = "medium",
        closable: bool = True,
        backdrop_dismiss: bool = True
    ) -> str:
        """Create an accessible modal dialog."""
        if not modal_id:
            modal_id = self._generate_id("modal")

        html = f"""
        <div class="modal-backdrop"
             id="{modal_id}_backdrop"
             {'onclick="closeModal(\'' + modal_id + '\')"' if backdrop_dismiss else ''}
             style="display: none;">

            <div class="modal modal-{size}"
                 id="{modal_id}"
                 role="dialog"
                 aria-labelledby="{modal_id}_title"
                 aria-modal="true"
                 onclick="event.stopPropagation()">

                <div class="modal-header">
                    <h2 class="modal-title" id="{modal_id}_title">{title}</h2>
                    {f'''<button class="modal-close"
                               onclick="closeModal('{modal_id}')"
                               aria-label="Close dialog">
                            <span aria-hidden="true">&times;</span>
                         </button>''' if closable else ''}
                </div>

                <div class="modal-body">
                    {content}
                </div>

                <div class="modal-footer" id="{modal_id}_footer">
                    <!-- Footer content can be added via JavaScript -->
                </div>
            </div>
        </div>

        <script>
            function openModal(modalId) {{
                const backdrop = document.getElementById(modalId + '_backdrop');
                const modal = document.getElementById(modalId);

                if (backdrop && modal) {{
                    backdrop.style.display = 'flex';
                    backdrop.offsetHeight; // Force reflow
                    backdrop.classList.add('modal-show');

                    // Focus management
                    const firstFocusable = modal.querySelector('button, input, select, textarea, [tabindex="0"]');
                    if (firstFocusable) firstFocusable.focus();

                    // Trap focus within modal
                    document.addEventListener('keydown', handleModalKeydown);
                }}
            }}

            function closeModal(modalId) {{
                const backdrop = document.getElementById(modalId + '_backdrop');

                if (backdrop) {{
                    backdrop.classList.remove('modal-show');
                    setTimeout(() => {{
                        backdrop.style.display = 'none';
                    }}, 200);

                    // Remove focus trap
                    document.removeEventListener('keydown', handleModalKeydown);
                }}
            }}

            function handleModalKeydown(event) {{
                if (event.key === 'Escape') {{
                    const openModal = document.querySelector('.modal-backdrop.modal-show .modal');
                    if (openModal) {{
                        closeModal(openModal.id);
                    }}
                }}
            }}
        </script>
        """

        return html.strip()

    def create_status_badge(
        self,
        status: str,
        text: str = None,
        size: str = "medium"
    ) -> str:
        """Create a status badge component."""
        if not text:
            text = status.replace('_', ' ').title()

        # Status color mapping
        status_colors = {
            'success': 'green',
            'completed': 'green',
            'active': 'blue',
            'pending': 'yellow',
            'warning': 'orange',
            'error': 'red',
            'failed': 'red',
            'cancelled': 'gray',
            'inactive': 'gray'
        }

        color = status_colors.get(status.lower(), 'gray')

        html = f"""
        <span class="status-badge status-{color} status-{size}"
              role="status"
              aria-label="Status: {text}">
            <span class="status-indicator" aria-hidden="true"></span>
            {text}
        </span>
        """

        return html.strip()

    def _get_progress_color_class(self, percentage: float, scheme: str) -> str:
        """Get progress bar color class based on percentage and scheme."""
        if scheme == "status":
            if percentage < 25:
                return "progress-danger"
            elif percentage < 75:
                return "progress-warning"
            else:
                return "progress-success"
        else:
            return f"progress-{scheme}"


class AccessibilityHelper:
    """Helper for accessibility features and ARIA attributes."""

    @staticmethod
    def create_skip_links(links: List[Dict[str, str]]) -> str:
        """Create skip navigation links for keyboard users."""
        skip_links = []
        for link in links:
            skip_links.append(
                f'<a href="{link["href"]}" class="skip-link">{link["text"]}</a>'
            )

        html = f"""
        <div class="skip-links">
            {"".join(skip_links)}
        </div>
        """

        return html.strip()

    @staticmethod
    def create_screen_reader_text(text: str) -> str:
        """Create text visible only to screen readers."""
        return f'<span class="sr-only">{text}</span>'

    @staticmethod
    def create_live_region(region_id: str, level: str = "polite") -> str:
        """Create an ARIA live region for dynamic content updates."""
        return f'<div id="{region_id}" aria-live="{level}" aria-atomic="true" class="sr-only"></div>'

    @staticmethod
    def announce_to_screen_reader(message: str, region_id: str = "announce") -> str:
        """Generate JavaScript to announce message to screen readers."""
        return f"""
        <script>
            (function() {{
                let region = document.getElementById('{region_id}');
                if (!region) {{
                    region = document.createElement('div');
                    region.id = '{region_id}';
                    region.setAttribute('aria-live', 'polite');
                    region.setAttribute('aria-atomic', 'true');
                    region.className = 'sr-only';
                    document.body.appendChild(region);
                }}
                region.textContent = '{message}';
                setTimeout(() => region.textContent = '', 1000);
            }})();
        </script>
        """


# Global UI component generator
ui_generator = UIComponentGenerator()
accessibility = AccessibilityHelper()