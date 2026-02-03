"""
Conversation Configuration for Otto.AI
Manages all configuration settings for the conversational AI system
"""

import os
from typing import Dict, Any, Optional, Callable
from pydantic_settings import BaseSettings
from pydantic import Field
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ConversationConfig(BaseSettings):
    """Configuration settings for conversation services"""

    # Zep Cloud Configuration
    zep_api_key: Optional[str] = Field(
        default=None,
        env="ZEP_API_KEY",
        description="Zep Cloud API key for temporal memory"
    )
    zep_base_url: Optional[str] = Field(
        default="https://api.getzep.com",
        env="ZEP_BASE_URL",
        description="Zep Cloud base URL"
    )

    # Groq API Configuration
    groq_api_key: Optional[str] = Field(
        default=None,
        env="GROQ_API_KEY",
        description="Groq API key for AI model access"
    )
    openrouter_api_key: Optional[str] = Field(
        default=None,
        env="OPENROUTER_API_KEY",
        description="OpenRouter API key (alternative to Groq)"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        env="OPENROUTER_BASE_URL",
        description="OpenRouter API base URL"
    )
    groq_model: str = Field(
        default="groq/llama-3.1-8b-instruct:free",
        env="GROQ_MODEL",
        description="Groq model to use for responses"
    )

    # Hot-reload Configuration
    enable_hot_reload: bool = Field(
        default=False,
        env="ENABLE_HOT_RELOAD",
        description="Enable configuration hot-reload from file"
    )
    config_file_path: Optional[str] = Field(
        default=None,
        env="CONFIG_FILE_PATH",
        description="Path to configuration file for hot-reload"
    )
    hot_reload_check_interval: int = Field(
        default=30,
        env="HOT_RELOAD_CHECK_INTERVAL",
        description="Check interval in seconds for config file changes"
    )

    # WebSocket Configuration
    websocket_max_connections: int = Field(
        default=1000,
        env="WEBSOCKET_MAX_CONNECTIONS",
        description="Maximum concurrent WebSocket connections"
    )
    websocket_max_per_user: int = Field(
        default=5,
        env="WEBSOCKET_MAX_PER_USER",
        description="Maximum connections per user"
    )
    websocket_timeout: int = Field(
        default=300,
        env="WEBSOCKET_TIMEOUT",
        description="WebSocket connection timeout in seconds"
    )
    websocket_heartbeat_interval: int = Field(
        default=30,
        env="WEBSOCKET_HEARTBEAT_INTERVAL",
        description="WebSocket heartbeat interval in seconds"
    )

    # Performance Configuration
    response_timeout_ms: float = Field(
        default=2000.0,
        env="RESPONSE_TIMEOUT_MS",
        description="Maximum response time in milliseconds"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        env="CACHE_TTL_SECONDS",
        description="Cache TTL for conversation data"
    )
    max_concurrent_requests: int = Field(
        default=50,
        env="MAX_CONCURRENT_REQUESTS",
        description="Maximum concurrent requests per user"
    )

    # Conversation Behavior
    max_message_history: int = Field(
        default=50,
        env="MAX_MESSAGE_HISTORY",
        description="Maximum messages to keep in conversation history"
    )
    max_working_memory: int = Field(
        default=10,
        env="MAX_WORKING_MEMORY",
        description="Maximum messages in working memory"
    )
    context_similarity_threshold: float = Field(
        default=0.7,
        env="CONTEXT_SIMILARITY_THRESHOLD",
        description="Threshold for context similarity matching"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level for conversation services"
    )
    log_requests: bool = Field(
        default=False,
        env="LOG_REQUESTS",
        description="Whether to log all conversation requests"
    )
    log_performance: bool = Field(
        default=True,
        env="LOG_PERFORMANCE",
        description="Whether to log performance metrics"
    )

    # Security Configuration
    rate_limit_enabled: bool = Field(
        default=True,
        env="RATE_LIMIT_ENABLED",
        description="Enable rate limiting for conversations"
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        env="RATE_LIMIT_RPM",
        description="Rate limit requests per minute per user"
    )
    enable_message_filtering: bool = Field(
        default=True,
        env="ENABLE_MESSAGE_FILTERING",
        description="Enable profanity and content filtering"
    )

    # Integration Configuration
    semantic_search_api_url: Optional[str] = Field(
        default=None,
        env="SEMANTIC_SEARCH_API_URL",
        description="URL for semantic search API integration"
    )
    vehicle_data_api_url: Optional[str] = Field(
        default=None,
        env="VEHICLE_DATA_API_URL",
        description="URL for vehicle data API integration"
    )

    # Development/Testing Configuration
    mock_ai_responses: bool = Field(
        default=False,
        env="MOCK_AI_RESPONSES",
        description="Use mock AI responses for testing"
    )
    enable_debug_mode: bool = Field(
        default=False,
        env="ENABLE_DEBUG_MODE",
        description="Enable debug mode with additional logging"
    )

    # Pydantic v2 model config
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields from environment (like supabase_url, etc.)
    }

    def __init__(self, **data):
        super().__init__(**data)
        self._last_modified = None
        self._reload_task = None
        self._reload_callbacks = []

    @classmethod
    def load(cls) -> "ConversationConfig":
        """Load configuration from environment"""
        try:
            config = cls()

            # Log configuration status
            logger.info("Conversation configuration loaded:")
            logger.info(f"  Zep Cloud: {'configured' if config.zep_api_key else 'not configured'}")
            logger.info(f"  Groq/OpenRouter: {'configured' if config.groq_api_key or config.openrouter_api_key else 'not configured'}")
            logger.info(f"  Model: {config.groq_model}")
            logger.info(f"  Response timeout: {config.response_timeout_ms}ms")

            return config

        except Exception as e:
            logger.error(f"Failed to load conversation configuration: {e}")
            raise

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        warnings = []

        # Check required configurations
        if not self.zep_api_key:
            warnings.append("Zep Cloud API key not configured - temporal memory will be disabled")

        if not self.groq_api_key and not self.openrouter_api_key:
            issues.append("No AI API key configured - either GROQ_API_KEY or OPENROUTER_API_KEY is required")

        # Check performance settings
        if self.response_timeout_ms < 500:
            warnings.append("Response timeout is very low (< 500ms) - may cause failures")

        if self.max_concurrent_requests > 100:
            warnings.append("High concurrent request limit may impact performance")

        # Check WebSocket settings
        if self.websocket_max_per_user > 10:
            warnings.append("High per-user connection limit may be abused")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

    def get_zep_config(self) -> Dict[str, Any]:
        """Get Zep Cloud configuration"""
        return {
            'api_key': self.zep_api_key,
            'base_url': self.zep_base_url,
            'initialized': bool(self.zep_api_key)
        }

    def get_groq_config(self) -> Dict[str, Any]:
        """Get Groq/OpenRouter configuration"""
        # Prefer OpenRouter if available, otherwise use Groq
        if self.openrouter_api_key:
            return {
                'api_key': self.openrouter_api_key,
                'base_url': self.openrouter_base_url,
                'model': "anthropic/claude-3.5-sonnet",  # Default OpenRouter model
                'provider': 'openrouter'
            }
        elif self.groq_api_key:
            return {
                'api_key': self.groq_api_key,
                'base_url': None,
                'model': self.groq_model,
                'provider': 'groq'
            }
        else:
            return {
                'initialized': False
            }

    def get_websocket_config(self) -> Dict[str, Any]:
        """Get WebSocket configuration"""
        return {
            'max_connections': self.websocket_max_connections,
            'max_per_user': self.websocket_max_per_user,
            'timeout': self.websocket_timeout,
            'heartbeat_interval': self.websocket_heartbeat_interval
        }

    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return {
            'response_timeout_ms': self.response_timeout_ms,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'max_concurrent_requests': self.max_concurrent_requests,
            'max_message_history': self.max_message_history,
            'max_working_memory': self.max_working_memory
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': self.log_level,
            'log_requests': self.log_requests,
            'log_performance': self.log_performance,
            'enable_debug': self.enable_debug_mode
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'zep': self.get_zep_config(),
            'groq': self.get_groq_config(),
            'websocket': self.get_websocket_config(),
            'performance': self.get_performance_config(),
            'logging': self.get_logging_config(),
            'validation': self.validate_configuration(),
            'hot_reload': {
                'enabled': self.enable_hot_reload,
                'config_file': self.config_file_path,
                'check_interval': self.hot_reload_check_interval
            }
        }

    async def start_hot_reload(self):
        """Start hot-reload monitoring if enabled"""
        if not self.enable_hot_reload or not self.config_file_path:
            logger.info("Hot-reload disabled or no config file specified")
            return

        config_path = Path(self.config_file_path)
        if not config_path.exists():
            logger.warning(f"Config file not found: {self.config_file_path}")
            return

        # Record initial modification time
        self._last_modified = config_path.stat().st_mtime

        # Start monitoring task
        self._reload_task = asyncio.create_task(self._monitor_config_file())
        logger.info(f"Started hot-reload monitoring for {self.config_file_path}")

    async def stop_hot_reload(self):
        """Stop hot-reload monitoring"""
        if self._reload_task:
            self._reload_task.cancel()
            try:
                await self._reload_task
            except asyncio.CancelledError:
                pass
            self._reload_task = None
            logger.info("Stopped hot-reload monitoring")

    async def _monitor_config_file(self):
        """Monitor configuration file for changes"""
        config_path = Path(self.config_file_path)

        while True:
            try:
                await asyncio.sleep(self.hot_reload_check_interval)

                if not config_path.exists():
                    logger.warning(f"Config file disappeared: {self.config_file_path}")
                    continue

                current_modified = config_path.stat().st_mtime
                if current_modified != self._last_modified:
                    logger.info(f"Configuration file changed: {self.config_file_path}")
                    await self._reload_config()
                    self._last_modified = current_modified

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring config file: {e}")

    async def _reload_config(self):
        """Reload configuration from file and environment"""
        try:
            # Save current state for comparison
            old_config = self.to_dict()

            # Reload from environment
            new_config = ConversationConfig.load()

            # Compare and log changes
            changes = self._compare_configs(old_config, new_config.to_dict())
            if changes:
                logger.info("Configuration reloaded with changes:")
                for section, items in changes.items():
                    logger.info(f"  {section}:")
                    for key, change in items.items():
                        logger.info(f"    {key}: {change['old']} -> {change['new']}")

                # Update this instance
                self._update_from_config(new_config)

                # Notify callbacks
                for callback in self._reload_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(self, changes)
                        else:
                            callback(self, changes)
                    except Exception as e:
                        logger.error(f"Error in reload callback: {e}")
            else:
                logger.info("Configuration reloaded with no changes")

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")

    def _compare_configs(self, old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two configuration dictionaries and return changes"""
        changes = {}

        for section in old:
            if section not in new:
                continue

            old_section = old[section]
            new_section = new[section]

            if isinstance(old_section, dict) and isinstance(new_section, dict):
                section_changes = {}
                for key in old_section:
                    if key in new_section and old_section[key] != new_section[key]:
                        section_changes[key] = {
                            'old': old_section[key],
                            'new': new_section[key]
                        }

                if section_changes:
                    changes[section] = section_changes

        return changes

    def _update_from_config(self, new_config: "ConversationConfig"):
        """Update this instance from another config"""
        for field_name, field_value in new_config.__dict__.items():
            if not field_name.startswith('_'):
                setattr(self, field_name, field_value)

    def add_reload_callback(self, callback: Callable[["ConversationConfig", Dict[str, Any]], None]):
        """Add a callback to be called when configuration is reloaded"""
        self._reload_callbacks.append(callback)

    def remove_reload_callback(self, callback: Callable[["ConversationConfig", Dict[str, Any]], None]):
        """Remove a reload callback"""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)

    def save_to_file(self, file_path: Optional[str] = None):
        """Save current configuration to file"""
        if not file_path:
            file_path = self.config_file_path

        if not file_path:
            raise ValueError("No file path specified")

        # Convert to JSON-serializable dict
        config_dict = self.to_dict()

        # Remove sensitive data
        if 'zep' in config_dict and 'api_key' in config_dict['zep']:
            config_dict['zep']['api_key'] = "***REDACTED***"
        if 'groq' in config_dict and 'api_key' in config_dict['groq']:
            config_dict['groq']['api_key'] = "***REDACTED***"

        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

        logger.info(f"Configuration saved to {file_path}")


# Global configuration instance
conversation_config: Optional[ConversationConfig] = None


def get_conversation_config() -> ConversationConfig:
    """Get global conversation configuration"""
    global conversation_config

    if conversation_config is None:
        conversation_config = ConversationConfig.load()

        # Start hot-reload if enabled
        if conversation_config.enable_hot_reload:
            # Note: This needs to be awaited in an async context
            # For now, we'll log a message
            logger.info("Configuration hot-reload enabled - call await start_config_hot_reload() to activate")

    return conversation_config


async def start_config_hot_reload():
    """Start configuration hot-reload monitoring"""
    config = get_conversation_config()
    await config.start_hot_reload()


async def stop_config_hot_reload():
    """Stop configuration hot-reload monitoring"""
    config = get_conversation_config()
    await config.stop_hot_reload()


def validate_conversation_config() -> bool:
    """Validate conversation configuration"""
    config = get_conversation_config()
    validation = config.validate_configuration()

    if not validation['valid']:
        logger.error("Configuration validation failed:")
        for issue in validation['issues']:
            logger.error(f"  - {issue}")
        return False

    if validation['warnings']:
        logger.warning("Configuration warnings:")
        for warning in validation['warnings']:
            logger.warning(f"  - {warning}")

    return True


# Configuration helper functions
def is_zep_available() -> bool:
    """Check if Zep Cloud is configured"""
    config = get_conversation_config()
    return bool(config.zep_api_key)


def is_ai_available() -> bool:
    """Check if AI service is configured"""
    config = get_conversation_config()
    return bool(config.groq_api_key or config.openrouter_api_key)


def get_active_ai_provider() -> str:
    """Get the active AI provider"""
    config = get_conversation_config()
    groq_config = config.get_groq_config()
    return groq_config.get('provider', 'none')


# Environment validation
def validate_environment() -> Dict[str, bool]:
    """Validate required environment variables"""
    return {
        'ZEP_API_KEY': bool(os.getenv('ZEP_API_KEY')),
        'GROQ_API_KEY': bool(os.getenv('GROQ_API_KEY')),
        'OPENROUTER_API_KEY': bool(os.getenv('OPENROUTER_API_KEY')),
        'SUPABASE_URL': bool(os.getenv('SUPABASE_URL')),
        'SUPABASE_ANON_KEY': bool(os.getenv('SUPABASE_ANON_KEY'))
    }