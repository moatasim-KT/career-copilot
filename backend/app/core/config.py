import os
from typing import Any

from pydantic import SecretStr

# Bridge to the unified configuration system
from .unified_config import UnifiedSettings, get_config


class _SecretStrProxy(str):
	"""String proxy that adds get_secret_value for compatibility."""

	def get_secret_value(self) -> str:
		return str(self)


class Settings:
	"""
	Thin adapter over UnifiedSettings to preserve backward-compatible attributes.

	- Delegates unknown attributes to UnifiedSettings via __getattr__
	- Exposes commonly used properties expected by legacy code
	- Reads a few security keys directly from the environment when not present
	"""

	def __init__(self) -> None:
		self._u: UnifiedSettings = get_config()

	# -------- Core/backward-compatible properties --------
	@property
	def database_url(self) -> str:
		return self._u.database_url

	@property
	def debug(self) -> bool:
		return bool(self._u.debug)

	@property
	def environment(self) -> str:
		return self._u.environment

	@property
	def log_level(self) -> str:
		return getattr(self._u, "log_level", "INFO")

	@property
	def development_mode(self) -> bool:
		# Unified settings may not expose this flag directly; fall back to environment check.
		if hasattr(self._u, "development_mode"):
			return bool(getattr(self._u, "development_mode"))
		return self.environment.lower() == "development"

	# -------- Job board API keys (expected by scrapers/tests) --------
	@property
	def adzuna_app_id(self) -> Any:
		return getattr(self._u, "adzuna_app_id", None)

	@property
	def adzuna_app_key(self) -> Any:
		return getattr(self._u, "adzuna_app_key", None)

	@property
	def adzuna_country(self) -> str:
		return getattr(self._u, "adzuna_country", "de")  # Default to Germany for EU jobs

	@property
	def rapidapi_jsearch_key(self) -> Any:
		return getattr(self._u, "rapidapi_jsearch_key", None)

	@property
	def themuse_api_key(self) -> Any:
		return getattr(self._u, "themuse_api_key", None)

	@property
	def themuse_base_url(self) -> Any:
		return getattr(self._u, "themuse_base_url", "https://www.themuse.com/api/public")

	@property
	def firecrawl_api_key(self) -> Any:
		"""Firecrawl API key for scraping JS-heavy career pages"""
		return getattr(self._u, "firecrawl_api_key", os.getenv("FIRECRAWL_API_KEY", None))

	@property
	def FIRECRAWL_API_KEY(self) -> Any:
		"""Backward compatibility - uppercase version"""
		return self.firecrawl_api_key

	# -------- Security keys --------
	@property
	def jwt_secret_key(self) -> _SecretStrProxy:
		val = getattr(self._u, "jwt_secret_key", None)
		if isinstance(val, SecretStr):
			secret = val.get_secret_value()
		elif isinstance(val, str):
			secret = val
		else:
			secret = os.getenv("JWT_SECRET_KEY", "")

		return _SecretStrProxy(secret)

	@property
	def encryption_key(self) -> str:
		# Not part of UnifiedSettings; pull from env
		return os.getenv("ENCRYPTION_KEY", "")

	@property
	def api_key_secret(self) -> str:
		# Not part of UnifiedSettings; pull from env
		return os.getenv("API_KEY_SECRET", "")

	# -------- Scraping toggles (legacy uppercase settings) --------
	@property
	def SCRAPING_MAX_RESULTS_PER_SITE(self) -> int:
		return int(os.getenv("SCRAPING_MAX_RESULTS_PER_SITE", "25"))

	@property
	def SCRAPING_MAX_CONCURRENT(self) -> int:
		return int(os.getenv("SCRAPING_MAX_CONCURRENT", "2"))

	@property
	def SCRAPING_ENABLE_INDEED(self) -> bool:
		return os.getenv("SCRAPING_ENABLE_INDEED", "false").lower() in {"1", "true", "yes"}

	@property
	def SCRAPING_ENABLE_LINKEDIN(self) -> bool:
		return os.getenv("SCRAPING_ENABLE_LINKEDIN", "false").lower() in {"1", "true", "yes"}

	@property
	def SCRAPING_RATE_LIMIT_MIN(self) -> float:
		return float(os.getenv("SCRAPING_RATE_LIMIT_MIN", "1.0"))

	@property
	def SCRAPING_RATE_LIMIT_MAX(self) -> float:
		return float(os.getenv("SCRAPING_RATE_LIMIT_MAX", "3.0"))

	# -------- Generic delegation --------
	def __getattr__(self, name: str) -> Any:
		# Delegate to the unified settings for any other attribute
		try:
			return getattr(self._u, name)
		except AttributeError as e:
			raise AttributeError(f"Settings object has no attribute '{name}'") from e


_settings: Settings | None = None


def get_settings() -> Settings:
	"""Return a singleton Settings adapter instance."""
	global _settings
	if _settings is None:
		_settings = Settings()
	return _settings


# Backward compatibility: some modules import `settings` directly
settings = get_settings()
