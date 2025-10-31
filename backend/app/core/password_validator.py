"""
Password Validation using Validator Pattern
Provides extensible password validation with configurable rules
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidationResult:
	"""Result of password validation."""

	is_valid: bool
	errors: List[str]

	def __bool__(self) -> bool:
		return self.is_valid

	def add_error(self, error: str) -> None:
		"""Add an error message."""
		self.errors.append(error)
		self.is_valid = False


class PasswordRule(ABC):
	"""Base class for password validation rules."""

	@abstractmethod
	def validate(self, password: str) -> Optional[str]:
		"""
		Validate password against this rule.

		Args:
		    password: Password to validate

		Returns:
		    Error message if validation fails, None if passes
		"""
		pass

	@property
	@abstractmethod
	def description(self) -> str:
		"""Human-readable description of this rule."""
		pass


class MinLengthRule(PasswordRule):
	"""Minimum password length rule."""

	def __init__(self, min_length: int = 8):
		self.min_length = min_length

	def validate(self, password: str) -> Optional[str]:
		if len(password) < self.min_length:
			return f"Password must be at least {self.min_length} characters long"
		return None

	@property
	def description(self) -> str:
		return f"At least {self.min_length} characters"


class MaxLengthRule(PasswordRule):
	"""Maximum password length rule."""

	def __init__(self, max_length: int = 128):
		self.max_length = max_length

	def validate(self, password: str) -> Optional[str]:
		if len(password) > self.max_length:
			return f"Password must be less than {self.max_length} characters long"
		return None

	@property
	def description(self) -> str:
		return f"Maximum {self.max_length} characters"


class UppercaseRule(PasswordRule):
	"""Requires at least one uppercase letter."""

	def __init__(self, count: int = 1):
		self.count = count

	def validate(self, password: str) -> Optional[str]:
		uppercase_count = sum(1 for c in password if c.isupper())
		if uppercase_count < self.count:
			return f"Password must contain at least {self.count} uppercase letter(s)"
		return None

	@property
	def description(self) -> str:
		return f"At least {self.count} uppercase letter(s)"


class LowercaseRule(PasswordRule):
	"""Requires at least one lowercase letter."""

	def __init__(self, count: int = 1):
		self.count = count

	def validate(self, password: str) -> Optional[str]:
		lowercase_count = sum(1 for c in password if c.islower())
		if lowercase_count < self.count:
			return f"Password must contain at least {self.count} lowercase letter(s)"
		return None

	@property
	def description(self) -> str:
		return f"At least {self.count} lowercase letter(s)"


class DigitRule(PasswordRule):
	"""Requires at least one digit."""

	def __init__(self, count: int = 1):
		self.count = count

	def validate(self, password: str) -> Optional[str]:
		digit_count = sum(1 for c in password if c.isdigit())
		if digit_count < self.count:
			return f"Password must contain at least {self.count} digit(s)"
		return None

	@property
	def description(self) -> str:
		return f"At least {self.count} digit(s)"


class SpecialCharRule(PasswordRule):
	"""Requires at least one special character."""

	def __init__(self, count: int = 1, special_chars: str = '!@#$%^&*(),.?":{}|<>'):
		self.count = count
		self.special_chars = special_chars

	def validate(self, password: str) -> Optional[str]:
		special_count = sum(1 for c in password if c in self.special_chars)
		if special_count < self.count:
			return f"Password must contain at least {self.count} special character(s) from {self.special_chars}"
		return None

	@property
	def description(self) -> str:
		return f"At least {self.count} special character(s)"


class NoWhitespaceRule(PasswordRule):
	"""Prohibits whitespace characters."""

	def validate(self, password: str) -> Optional[str]:
		if any(c.isspace() for c in password):
			return "Password must not contain whitespace characters"
		return None

	@property
	def description(self) -> str:
		return "No whitespace characters"


class NoCommonPasswordRule(PasswordRule):
	"""Checks against common/weak passwords."""

	def __init__(self, common_passwords: Optional[List[str]] = None):
		self.common_passwords = common_passwords or [
			"password",
			"123456",
			"password123",
			"12345678",
			"qwerty",
			"abc123",
			"monkey",
			"1234567",
			"letmein",
			"trustno1",
			"dragon",
			"baseball",
			"111111",
			"iloveyou",
			"master",
			"sunshine",
			"ashley",
			"bailey",
			"passw0rd",
			"shadow",
		]

	def validate(self, password: str) -> Optional[str]:
		if password.lower() in self.common_passwords:
			return "Password is too common. Please choose a stronger password"
		return None

	@property
	def description(self) -> str:
		return "Not a common password"


class NoUsernameRule(PasswordRule):
	"""Ensures password doesn't contain username."""

	def __init__(self, username: str):
		self.username = username.lower()

	def validate(self, password: str) -> Optional[str]:
		if self.username in password.lower():
			return "Password must not contain your username"
		return None

	@property
	def description(self) -> str:
		return "Does not contain username"


class PasswordValidator:
	"""
	Configurable password validator using rule-based validation.

	Example:
	    validator = PasswordValidator()
	    result = validator.validate("MyP@ssw0rd123")
	    if not result:
	        print("Errors:", result.errors)
	"""

	def __init__(self, rules: Optional[List[PasswordRule]] = None):
		"""
		Initialize validator with rules.

		Args:
		    rules: List of validation rules. If None, uses default rules.
		"""
		self.rules = rules or self._default_rules()

	def _default_rules(self) -> List[PasswordRule]:
		"""Get default password validation rules."""
		return [
			MinLengthRule(8),
			MaxLengthRule(128),
			UppercaseRule(1),
			LowercaseRule(1),
			DigitRule(1),
			SpecialCharRule(1),
			NoWhitespaceRule(),
			NoCommonPasswordRule(),
		]

	def validate(self, password: str, username: Optional[str] = None) -> ValidationResult:
		"""
		Validate password against all rules.

		Args:
		    password: Password to validate
		    username: Optional username to check against

		Returns:
		    ValidationResult with is_valid and errors
		"""
		result = ValidationResult(is_valid=True, errors=[])

		# Add username rule if username provided
		rules = self.rules.copy()
		if username:
			rules.append(NoUsernameRule(username))

		# Validate against all rules
		for rule in rules:
			error = rule.validate(password)
			if error:
				result.add_error(error)

		return result

	def get_requirements(self) -> List[str]:
		"""Get list of password requirements (descriptions of all rules)."""
		return [rule.description for rule in self.rules]

	def add_rule(self, rule: PasswordRule) -> None:
		"""Add a custom validation rule."""
		self.rules.append(rule)

	def remove_rule(self, rule_type: type) -> None:
		"""Remove a specific type of rule."""
		self.rules = [r for r in self.rules if not isinstance(r, rule_type)]


# Pre-configured validators for different security levels


def get_basic_validator() -> PasswordValidator:
	"""Basic password validator (min 8 chars, alphanumeric)."""
	return PasswordValidator(
		rules=[
			MinLengthRule(8),
			MaxLengthRule(128),
			UppercaseRule(1),
			LowercaseRule(1),
			DigitRule(1),
		]
	)


def get_strong_validator() -> PasswordValidator:
	"""Strong password validator (default rules)."""
	return PasswordValidator()  # Uses default rules


def get_strict_validator() -> PasswordValidator:
	"""Strict password validator (more stringent requirements)."""
	return PasswordValidator(
		rules=[
			MinLengthRule(12),
			MaxLengthRule(128),
			UppercaseRule(2),
			LowercaseRule(2),
			DigitRule(2),
			SpecialCharRule(2),
			NoWhitespaceRule(),
			NoCommonPasswordRule(),
		]
	)


# Singleton instance for default usage
default_validator = PasswordValidator()
