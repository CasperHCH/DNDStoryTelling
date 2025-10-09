"""
Enhanced user authentication and session management.
Includes secure session handling, role-based access, and audit logging.
"""

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt

from app.utils.monitoring import performance_metrics, alert_manager
from app.utils.security import RateLimiter


class UserRole:
    """User role definitions with hierarchical permissions."""

    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    MODERATOR = "moderator"
    ADMIN = "admin"

    # Permission hierarchy
    ROLE_HIERARCHY = {
        GUEST: 0,
        USER: 1,
        PREMIUM: 2,
        MODERATOR: 3,
        ADMIN: 4
    }

    # Role permissions
    PERMISSIONS = {
        GUEST: {"read_public_content"},
        USER: {"read_public_content", "create_stories", "save_stories", "export_stories"},
        PREMIUM: {
            "read_public_content", "create_stories", "save_stories", "export_stories",
            "advanced_generation", "priority_processing", "api_access"
        },
        MODERATOR: {
            "read_public_content", "create_stories", "save_stories", "export_stories",
            "advanced_generation", "priority_processing", "api_access",
            "moderate_content", "view_user_activity", "manage_user_stories"
        },
        ADMIN: {
            "read_public_content", "create_stories", "save_stories", "export_stories",
            "advanced_generation", "priority_processing", "api_access",
            "moderate_content", "view_user_activity", "manage_user_stories",
            "manage_users", "system_admin", "view_metrics", "manage_settings"
        }
    }

    @classmethod
    def has_permission(cls, user_role: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        return permission in cls.PERMISSIONS.get(user_role, set())

    @classmethod
    def can_access_role(cls, user_role: str, required_role: str) -> bool:
        """Check if user role meets minimum required role."""
        user_level = cls.ROLE_HIERARCHY.get(user_role, -1)
        required_level = cls.ROLE_HIERARCHY.get(required_role, 999)
        return user_level >= required_level


class SessionData:
    """Secure session data container."""

    def __init__(self, user_id: str, username: str, role: str = UserRole.USER):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.username = username
        self.role = role
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.ip_address = None
        self.user_agent = None
        self.is_active = True
        self.metadata = {}
        self.activity_log = []

    def update_access(self, ip_address: str = None, user_agent: str = None):
        """Update session access information."""
        self.last_accessed = datetime.now()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent

        self.activity_log.append({
            'timestamp': self.last_accessed.isoformat(),
            'ip_address': ip_address,
            'user_agent': user_agent
        })

        # Keep only recent activity
        if len(self.activity_log) > 50:
            self.activity_log = self.activity_log[-50:]

    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if session is expired."""
        if not self.is_active:
            return True

        age = datetime.now() - self.last_accessed
        return age.total_seconds() > (max_age_hours * 3600)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'ip_address': self.ip_address,
            'is_active': self.is_active,
            'metadata': self.metadata
        }


class AuthenticationManager:
    """Secure authentication and session management."""

    def __init__(self, secret_key: str, session_timeout_hours: int = 24):
        self.secret_key = secret_key
        self.session_timeout_hours = session_timeout_hours
        self.active_sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        self.failed_attempts: Dict[str, List[float]] = {}
        self.rate_limiter = RateLimiter()
        self.audit_log = []

        # JWT settings
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def hash_password(self, password: str) -> str:
        """Hash a password securely."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Optional[SessionData]:
        """Authenticate a user and create session."""

        # Rate limiting check
        if not self.rate_limiter.is_allowed(ip_address or "unknown", max_requests=5, window_seconds=300):
            await alert_manager.trigger_alert(
                "rate_limit_exceeded",
                "warning",
                f"Authentication rate limit exceeded for IP: {ip_address}",
                {"ip_address": ip_address, "username": username}
            )
            return None

        # Check for recent failed attempts
        if self._has_recent_failures(username, max_attempts=3, window_minutes=15):
            await alert_manager.trigger_alert(
                "brute_force_detected",
                "warning",
                f"Multiple failed login attempts for user: {username}",
                {"username": username, "ip_address": ip_address}
            )
            return None

        try:
            # TODO: Replace with actual user lookup from database
            user_data = await self._lookup_user(username)

            if user_data and self.verify_password(password, user_data['password_hash']):
                # Authentication successful
                session = SessionData(
                    user_id=user_data['user_id'],
                    username=username,
                    role=user_data.get('role', UserRole.USER)
                )
                session.update_access(ip_address, user_agent)

                # Store session
                self.active_sessions[session.session_id] = session

                # Track user sessions
                if session.user_id not in self.user_sessions:
                    self.user_sessions[session.user_id] = set()
                self.user_sessions[session.user_id].add(session.session_id)

                # Clear failed attempts
                if username in self.failed_attempts:
                    del self.failed_attempts[username]

                # Log successful authentication
                await self._log_auth_event("login_success", username, ip_address, user_agent)

                performance_metrics.record_function_call("authentication_success", 1)
                return session
            else:
                # Authentication failed
                self._record_failed_attempt(username)
                await self._log_auth_event("login_failed", username, ip_address, user_agent)
                performance_metrics.record_function_call("authentication_failed", 1)
                return None

        except Exception as e:
            await alert_manager.trigger_alert(
                "authentication_error",
                "error",
                f"Authentication system error: {e}",
                {"username": username, "ip_address": ip_address}
            )
            return None

    def create_access_token(self, session: SessionData) -> str:
        """Create a JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode = {
            "sub": session.user_id,
            "username": session.username,
            "role": session.role,
            "session_id": session.session_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        return jwt.encode(to_encode, self.secret_key, algorithm=self.jwt_algorithm)

    def create_refresh_token(self, session: SessionData) -> str:
        """Create a JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode = {
            "sub": session.user_id,
            "session_id": session.session_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        return jwt.encode(to_encode, self.secret_key, algorithm=self.jwt_algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError:
            return None

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get an active session."""
        session = self.active_sessions.get(session_id)

        if session and not session.is_expired(self.session_timeout_hours):
            return session
        elif session:
            # Session expired, remove it
            self.invalidate_session(session_id)

        return None

    def refresh_session(
        self,
        session_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Optional[SessionData]:
        """Refresh an existing session."""
        session = self.get_session(session_id)

        if session:
            session.update_access(ip_address, user_agent)
            performance_metrics.record_function_call("session_refresh", 1)
            return session

        return None

    async def invalidate_session(self, session_id: str):
        """Invalidate a specific session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.is_active = False

            # Remove from active sessions
            del self.active_sessions[session_id]

            # Remove from user sessions
            if session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].discard(session_id)
                if not self.user_sessions[session.user_id]:
                    del self.user_sessions[session.user_id]

            await self._log_auth_event("logout", session.username)
            performance_metrics.record_function_call("session_invalidated", 1)

    async def invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user."""
        if user_id in self.user_sessions:
            session_ids = list(self.user_sessions[user_id])
            for session_id in session_ids:
                await self.invalidate_session(session_id)

    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = datetime.now()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if session.is_expired(self.session_timeout_hours):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            asyncio.create_task(self.invalidate_session(session_id))

        performance_metrics.record_function_call("sessions_cleaned", len(expired_sessions))
        return len(expired_sessions)

    def check_permission(self, session: SessionData, permission: str) -> bool:
        """Check if user has specific permission."""
        return UserRole.has_permission(session.role, permission)

    def require_role(self, session: SessionData, required_role: str) -> bool:
        """Check if user meets minimum role requirement."""
        return UserRole.can_access_role(session.role, required_role)

    async def change_user_role(self, user_id: str, new_role: str, admin_user_id: str):
        """Change user role (admin function)."""
        if new_role not in UserRole.ROLE_HIERARCHY:
            raise ValueError(f"Invalid role: {new_role}")

        # TODO: Update role in database

        # Update active sessions
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                if session_id in self.active_sessions:
                    self.active_sessions[session_id].role = new_role

        await self._log_auth_event(
            "role_changed",
            f"user_{user_id}",
            metadata={
                "new_role": new_role,
                "changed_by": admin_user_id
            }
        )

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        active_count = len(self.active_sessions)
        user_count = len(self.user_sessions)

        role_distribution = {}
        for session in self.active_sessions.values():
            role = session.role
            role_distribution[role] = role_distribution.get(role, 0) + 1

        return {
            'active_sessions': active_count,
            'active_users': user_count,
            'role_distribution': role_distribution,
            'session_timeout_hours': self.session_timeout_hours
        }

    def _has_recent_failures(self, username: str, max_attempts: int = 3, window_minutes: int = 15) -> bool:
        """Check for recent failed login attempts."""
        if username not in self.failed_attempts:
            return False

        cutoff_time = time.time() - (window_minutes * 60)
        recent_attempts = [
            attempt for attempt in self.failed_attempts[username]
            if attempt > cutoff_time
        ]

        self.failed_attempts[username] = recent_attempts
        return len(recent_attempts) >= max_attempts

    def _record_failed_attempt(self, username: str):
        """Record a failed login attempt."""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []

        self.failed_attempts[username].append(time.time())

        # Keep only recent attempts
        cutoff_time = time.time() - (60 * 60)  # 1 hour
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username]
            if attempt > cutoff_time
        ]

    async def _lookup_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Lookup user in database (placeholder implementation)."""
        # TODO: Replace with actual database lookup

        # Mock user data for testing
        mock_users = {
            "admin": {
                "user_id": "admin_001",
                "username": "admin",
                "password_hash": self.hash_password("admin_password"),
                "role": UserRole.ADMIN
            },
            "user": {
                "user_id": "user_001",
                "username": "user",
                "password_hash": self.hash_password("user_password"),
                "role": UserRole.USER
            }
        }

        return mock_users.get(username)

    async def _log_auth_event(
        self,
        event_type: str,
        username: str,
        ip_address: str = None,
        user_agent: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Log authentication events for audit purposes."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'metadata': metadata or {}
        }

        self.audit_log.append(log_entry)

        # Keep only recent logs
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]  # Keep last 5000 entries


class PermissionDecorator:
    """Decorator for checking permissions on routes."""

    def __init__(self, auth_manager: AuthenticationManager):
        self.auth_manager = auth_manager

    def require_permission(self, permission: str):
        """Decorator to require specific permission."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract session from request context
                # This would be integrated with FastAPI dependency injection
                session = kwargs.get('current_user')

                if not session or not self.auth_manager.check_permission(session, permission):
                    raise HTTPException(status_code=403, detail="Insufficient permissions")

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def require_role(self, role: str):
        """Decorator to require minimum role."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                session = kwargs.get('current_user')

                if not session or not self.auth_manager.require_role(session, role):
                    raise HTTPException(status_code=403, detail="Insufficient role")

                return await func(*args, **kwargs)
            return wrapper
        return decorator


# Global authentication manager (would be configured with actual secret key)
auth_manager = AuthenticationManager(
    secret_key="your-secret-key-here-change-in-production",
    session_timeout_hours=24
)

# Permission decorator instance
permission_decorator = PermissionDecorator(auth_manager)