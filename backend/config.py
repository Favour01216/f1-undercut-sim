"""
Configuration module for F1 Undercut Simulation Backend

Centralizes environment variable handling and application configuration.
"""

import os
from typing import Optional, Dict, Any

class Config:
    """
    Application configuration with environment variable support.
    """
    
    # API Configuration
    OPENF1_API_URL: str = os.getenv("OPENF1_API_URL", "https://api.openf1.org/v1")
    JOLPICA_API_URL: str = os.getenv("JOLPICA_API_URL", "https://jolpica-f1-api.p.rapidapi.com")
    
    # Cache Configuration
    CACHE_DIR: str = os.getenv("CACHE_DIR", "features")
    ENRICHED_CACHE_DIR: str = os.getenv("ENRICHED_CACHE_DIR", "features/enriched")
    FASTF1_CACHE_DIR: str = os.getenv("FASTF1_CACHE_DIR", "features/fastf1_cache")
    
    # Data Enrichment Configuration
    OFFLINE_MODE: bool = os.getenv("OFFLINE", "0").lower() in ("1", "true", "yes", "on")
    ENABLE_FASTF1_ENRICHMENT: bool = os.getenv("ENABLE_FASTF1_ENRICHMENT", "1").lower() in ("1", "true", "yes", "on")
    COMPOUND_COVERAGE_THRESHOLD: float = float(os.getenv("COMPOUND_COVERAGE_THRESHOLD", "0.8"))
    
    # Performance Configuration  
    CACHE_EXPIRY_HOURS: int = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Sentry Configuration
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    SENTRY_PROFILES_SAMPLE_RATE: float = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))
    
    @classmethod
    def get_data_enrichment_config(cls) -> Dict[str, Any]:
        """
        Get data enrichment configuration for FastF1 integration.
        
        Returns:
            Dictionary with enrichment settings
        """
        return {
            "offline_mode": cls.OFFLINE_MODE,
            "enable_enrichment": cls.ENABLE_FASTF1_ENRICHMENT,
            "coverage_threshold": cls.COMPOUND_COVERAGE_THRESHOLD,
            "cache_dir": cls.ENRICHED_CACHE_DIR,
            "fastf1_cache_dir": cls.FASTF1_CACHE_DIR
        }
    
    @classmethod
    def log_configuration(cls) -> None:
        """Log current configuration settings."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=== F1 Undercut Simulation Configuration ===")
        logger.info(f"OpenF1 API URL: {cls.OPENF1_API_URL}")
        logger.info(f"Cache Directory: {cls.CACHE_DIR}")
        logger.info(f"Offline Mode: {cls.OFFLINE_MODE}")
        logger.info(f"FastF1 Enrichment: {cls.ENABLE_FASTF1_ENRICHMENT}")
        logger.info(f"Compound Coverage Threshold: {cls.COMPOUND_COVERAGE_THRESHOLD}")
        logger.info(f"Cache Expiry: {cls.CACHE_EXPIRY_HOURS} hours")
        logger.info(f"Log Level: {cls.LOG_LEVEL}")
        
        if cls.OFFLINE_MODE:
            logger.warning("🔴 OFFLINE MODE ENABLED - FastF1 integration disabled")
        elif not cls.ENABLE_FASTF1_ENRICHMENT:
            logger.warning("🟡 FastF1 enrichment disabled by configuration")
        else:
            logger.info("🟢 FastF1 compound enrichment enabled")


# Global configuration instance
config = Config()