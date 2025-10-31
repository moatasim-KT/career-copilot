"""
Unit Tests for Password Validator
Tests the extensible password validation system
"""

import pytest
from app.core.password_validator import (
	DigitRule,
	MinLengthRule,
	NoCommonPasswordRule,
	NoUsernameRule,
	NoWhitespaceRule,
	PasswordValidator,
	SpecialCharRule,
	UppercaseRule,
	get_basic_validator,
	get_strict_validator,
	get_strong_validator,
)


class TestPasswordValidation:
	"""Test password validation"""

	def test_min_length_validation(self):
		"""Test minimum length validation"""
		rule = MinLengthRule(min_length=8)
		assert rule.validate("12345678") is None  # Valid
		assert rule.validate("1234567") is not None  # Invalid

	def test_uppercase_validation(self):
		"""Test uppercase character validation"""
		rule = UppercaseRule(count=1)
		assert rule.validate("Password1") is None  # Valid
		assert rule.validate("password1") is not None  # Invalid

	def test_digit_validation(self):
		"""Test digit validation"""
		rule = DigitRule(count=1)
		assert rule.validate("Password1") is None  # Valid
		assert rule.validate("Password") is not None  # Invalid

	def test_special_char_validation(self):
		"""Test special character validation"""
		rule = SpecialCharRule(count=1)
		assert rule.validate("Password1!") is None  # Valid
		assert rule.validate("Password1") is not None  # Invalid

	def test_no_whitespace_validation(self):
		"""Test no whitespace validation"""
		rule = NoWhitespaceRule()
		assert rule.validate("Password123") is None  # Valid
		assert rule.validate("Pass word 123") is not None  # Invalid

	def test_no_common_password_validation(self):
		"""Test no common password validation"""
		rule = NoCommonPasswordRule()
		assert rule.validate("MyComplexP@ss123") is None  # Valid
		assert rule.validate("password") is not None  # Invalid

	def test_no_username_validation(self):
		"""Test no username in password validation"""
		rule = NoUsernameRule("john")
		assert rule.validate("SecureP@ss123") is None  # Valid
		assert rule.validate("john1234") is not None  # Invalid

	def test_basic_validator(self):
		"""Test basic password validator"""
		validator = get_basic_validator()
		result = validator.validate("Password123")
		assert result.is_valid
		assert len(result.errors) == 0

	def test_strong_validator(self):
		"""Test strong password validator"""
		validator = get_strong_validator()
		result = validator.validate("Password123!")
		assert result.is_valid

		result = validator.validate("password")
		assert not result.is_valid

	def test_strict_validator(self):
		"""Test strict password validator"""
		validator = get_strict_validator()
		result = validator.validate("MyVerySecureP@ssw0rd!123")
		assert result.is_valid

		result = validator.validate("Password1!")
		assert not result.is_valid  # Too short

	def test_custom_validator(self):
		"""Test custom validator with specific rules"""
		validator = PasswordValidator(
			rules=[
				MinLengthRule(10),
				UppercaseRule(2),
				DigitRule(2),
			]
		)

		result = validator.validate("MyPassword123")
		assert result.is_valid

		result = validator.validate("Password1")
		assert not result.is_valid  # Only 1 uppercase, 1 digit

	def test_username_validation(self):
		"""Test password validation with username"""
		validator = get_strong_validator()

		result = validator.validate("johndoe123!", username="johndoe")
		assert not result.is_valid  # Contains username

		result = validator.validate("SecureP@ss123!", username="johndoe")
		assert result.is_valid  # Doesn't contain username


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
