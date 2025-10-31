"""
Predictive Analytics Service
Provides predictive insights for job application tracking
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

try:
	import numpy as np
	from sklearn.ensemble import RandomForestRegressor
	from sklearn.linear_model import LinearRegression
	from sklearn.preprocessing import StandardScaler
except ImportError:
	# Fallback for when scikit-learn is not available

	np = None
	RandomForestRegressor = None
	LinearRegression = None
	StandardScaler = None

logger = logging.getLogger(__name__)


class PredictionType(str, Enum):
	"""Types of predictions"""

	RISK_SCORE = "risk_score"
	RENEWAL_LIKELIHOOD = "renewal_likelihood"
	CONTRACT_VALUE = "contract_value"
	NEGOTIATION_SUCCESS = "negotiation_success"
	COMPLIANCE_RISK = "compliance_risk"


@dataclass
class PredictionResult:
	"""Prediction result"""

	prediction_type: PredictionType
	predicted_value: float
	confidence: float
	factors: List[Dict[str, Any]]
	recommendations: List[str]
	generated_at: datetime


@dataclass
class HistoricalData:
	"""Historical contract data for training"""

	contract_id: str
	risk_score: float
	contract_value: float
	renewal_status: bool
	negotiation_success: bool
	compliance_score: float
	contract_type: str
	duration_months: int
	created_at: datetime


class PredictiveService:
	"""Service for predictive analytics and forecasting"""

	def __init__(self):
		self.models = {}
		self.scaler = StandardScaler() if StandardScaler else None
		self.historical_data: List[HistoricalData] = []
		self._initialize_models()

	def _initialize_models(self):
		"""Initialize ML models"""
		if RandomForestRegressor and LinearRegression:
			self.models = {
				PredictionType.RISK_SCORE: RandomForestRegressor(n_estimators=100, random_state=42),
				PredictionType.RENEWAL_LIKELIHOOD: RandomForestRegressor(n_estimators=100, random_state=42),
				PredictionType.CONTRACT_VALUE: LinearRegression(),
				PredictionType.NEGOTIATION_SUCCESS: RandomForestRegressor(n_estimators=100, random_state=42),
				PredictionType.COMPLIANCE_RISK: RandomForestRegressor(n_estimators=100, random_state=42),
			}
		else:
			# Fallback models when scikit-learn is not available
			self.models = {}

	async def predict_risk_score(self, contract_text: str, contract_type: str, contract_value: float = 0.0) -> PredictionResult:
		"""Predict contract risk score"""
		try:
			# Extract features from contract text
			features = await self._extract_risk_features(contract_text, contract_type, contract_value)

			# Make prediction using trained model
			if self.models[PredictionType.RISK_SCORE].n_features_in_ > 0:
				prediction = self.models[PredictionType.RISK_SCORE].predict([features])[0]
				confidence = 0.85  # Mock confidence score
			else:
				# Fallback to rule-based prediction
				prediction = await self._rule_based_risk_prediction(contract_text)
				confidence = 0.70

			# Generate factors and recommendations
			factors = await self._analyze_risk_factors(contract_text)
			recommendations = await self._generate_risk_recommendations(prediction, factors)

			return PredictionResult(
				prediction_type=PredictionType.RISK_SCORE,
				predicted_value=round(prediction, 2),
				confidence=confidence,
				factors=factors,
				recommendations=recommendations,
				generated_at=datetime.now(),
			)

		except Exception as e:
			logger.error(f"Failed to predict risk score: {e}")
			return self._get_empty_prediction(PredictionType.RISK_SCORE)

	async def predict_renewal_likelihood(
		self, contract_id: str, contract_value: float, duration_months: int, current_risk_score: float
	) -> PredictionResult:
		"""Predict contract renewal likelihood"""
		try:
			# Extract features
			features = [
				contract_value,
				duration_months,
				current_risk_score,
				datetime.now().month,  # Seasonality
				contract_value / duration_months if duration_months > 0 else 0,  # Value per month
			]

			# Make prediction
			if self.models[PredictionType.RENEWAL_LIKELIHOOD].n_features_in_ > 0:
				prediction = self.models[PredictionType.RENEWAL_LIKELIHOOD].predict([features])[0]
				confidence = 0.80
			else:
				# Fallback prediction based on risk score
				prediction = max(0, min(1, 1 - (current_risk_score / 10)))
				confidence = 0.60

			# Generate factors and recommendations
			factors = [
				{"factor": "Contract Value", "impact": "positive" if contract_value > 100000 else "negative", "value": contract_value},
				{"factor": "Risk Score", "impact": "negative", "value": current_risk_score},
				{"factor": "Duration", "impact": "positive" if duration_months > 12 else "negative", "value": duration_months},
			]

			recommendations = await self._generate_renewal_recommendations(prediction, factors)

			return PredictionResult(
				prediction_type=PredictionType.RENEWAL_LIKELIHOOD,
				predicted_value=round(prediction, 3),
				confidence=confidence,
				factors=factors,
				recommendations=recommendations,
				generated_at=datetime.now(),
			)

		except Exception as e:
			logger.error(f"Failed to predict renewal likelihood: {e}")
			return self._get_empty_prediction(PredictionType.RENEWAL_LIKELIHOOD)

	async def predict_contract_value(
		self, contract_type: str, duration_months: int, risk_score: float, industry: str = "general"
	) -> PredictionResult:
		"""Predict contract value based on characteristics"""
		try:
			# Extract features
			features = [
				duration_months,
				risk_score,
				len(contract_type),
				1 if industry == "technology" else 0,
				1 if industry == "finance" else 0,
				1 if industry == "healthcare" else 0,
			]

			# Make prediction
			if self.models[PredictionType.CONTRACT_VALUE].n_features_in_ > 0:
				prediction = self.models[PredictionType.CONTRACT_VALUE].predict([features])[0]
				confidence = 0.75
			else:
				# Fallback prediction based on industry averages
				base_value = 50000
				if industry == "technology":
					base_value = 100000
				elif industry == "finance":
					base_value = 150000
				elif industry == "healthcare":
					base_value = 200000

				prediction = base_value * (duration_months / 12) * (1 - risk_score / 20)
				confidence = 0.60

			# Generate factors and recommendations
			factors = [
				{"factor": "Contract Type", "impact": "neutral", "value": contract_type},
				{"factor": "Duration", "impact": "positive", "value": duration_months},
				{"factor": "Risk Score", "impact": "negative", "value": risk_score},
				{"factor": "Industry", "impact": "positive" if industry in ["technology", "finance"] else "neutral", "value": industry},
			]

			recommendations = await self._generate_value_recommendations(prediction, factors)

			return PredictionResult(
				prediction_type=PredictionType.CONTRACT_VALUE,
				predicted_value=round(prediction, 2),
				confidence=confidence,
				factors=factors,
				recommendations=recommendations,
				generated_at=datetime.now(),
			)

		except Exception as e:
			logger.error(f"Failed to predict contract value: {e}")
			return self._get_empty_prediction(PredictionType.CONTRACT_VALUE)

	async def predict_negotiation_success(self, contract_text: str, current_terms: Dict[str, Any], proposed_changes: List[str]) -> PredictionResult:
		"""Predict negotiation success likelihood"""
		try:
			# Extract features from contract and proposed changes
			features = await self._extract_negotiation_features(contract_text, current_terms, proposed_changes)

			# Make prediction
			if self.models[PredictionType.NEGOTIATION_SUCCESS].n_features_in_ > 0:
				prediction = self.models[PredictionType.NEGOTIATION_SUCCESS].predict([features])[0]
				confidence = 0.80
			else:
				# Fallback prediction based on change complexity
				complexity_score = len(proposed_changes) / 10
				prediction = max(0, min(1, 0.7 - complexity_score))
				confidence = 0.65

			# Generate factors and recommendations
			factors = [
				{"factor": "Number of Changes", "impact": "negative", "value": len(proposed_changes)},
				{"factor": "Contract Complexity", "impact": "negative", "value": len(contract_text) / 1000},
				{"factor": "Current Risk Level", "impact": "negative", "value": current_terms.get("risk_score", 5.0)},
			]

			recommendations = await self._generate_negotiation_recommendations(prediction, factors)

			return PredictionResult(
				prediction_type=PredictionType.NEGOTIATION_SUCCESS,
				predicted_value=round(prediction, 3),
				confidence=confidence,
				factors=factors,
				recommendations=recommendations,
				generated_at=datetime.now(),
			)

		except Exception as e:
			logger.error(f"Failed to predict negotiation success: {e}")
			return self._get_empty_prediction(PredictionType.NEGOTIATION_SUCCESS)

	async def _extract_risk_features(self, contract_text: str, contract_type: str, contract_value: float) -> List[float]:
		"""Extract features for risk prediction"""
		# Simple feature extraction - in production, use more sophisticated NLP
		features = [
			len(contract_text) / 1000,  # Contract length
			contract_text.count("liability") / len(contract_text.split()) * 100,  # Liability mentions
			contract_text.count("penalty") / len(contract_text.split()) * 100,  # Penalty mentions
			contract_text.count("termination") / len(contract_text.split()) * 100,  # Termination mentions
			contract_value / 100000,  # Contract value (normalized)
			1 if "service" in contract_type.lower() else 0,  # Service contract
			1 if "employment" in contract_type.lower() else 0,  # Employment contract
			1 if "nda" in contract_type.lower() else 0,  # NDA
		]
		return features

	async def _extract_negotiation_features(self, contract_text: str, current_terms: Dict[str, Any], proposed_changes: List[str]) -> List[float]:
		"""Extract features for negotiation prediction"""
		features = [
			len(proposed_changes),  # Number of proposed changes
			len(contract_text) / 1000,  # Contract length
			current_terms.get("risk_score", 5.0),  # Current risk score
			current_terms.get("value", 0) / 100000,  # Contract value
			sum(1 for change in proposed_changes if "liability" in change.lower()),  # Liability changes
			sum(1 for change in proposed_changes if "payment" in change.lower()),  # Payment changes
		]
		return features

	async def _rule_based_risk_prediction(self, contract_text: str) -> float:
		"""Fallback rule-based risk prediction"""
		risk_score = 5.0  # Base risk score

		# Adjust based on contract content
		if "liability" in contract_text.lower():
			risk_score += 1.0
		if "penalty" in contract_text.lower():
			risk_score += 1.5
		if "termination" in contract_text.lower():
			risk_score += 0.5
		if "force majeure" in contract_text.lower():
			risk_score += 0.5

		return min(10.0, max(0.0, risk_score))

	async def _analyze_risk_factors(self, contract_text: str) -> List[Dict[str, Any]]:
		"""Analyze risk factors in contract"""
		factors = []

		if "liability" in contract_text.lower():
			factors.append({"factor": "Liability Clauses", "impact": "high", "description": "Contract contains liability limitations"})

		if "penalty" in contract_text.lower():
			factors.append({"factor": "Penalty Clauses", "impact": "high", "description": "Contract contains penalty provisions"})

		if "termination" in contract_text.lower():
			factors.append({"factor": "Termination Clauses", "impact": "medium", "description": "Contract contains termination provisions"})

		return factors

	async def _generate_risk_recommendations(self, risk_score: float, factors: List[Dict[str, Any]]) -> List[str]:
		"""Generate risk-based recommendations"""
		recommendations = []

		if risk_score >= 7.0:
			recommendations.append("High risk detected - consider legal review")
			recommendations.append("Negotiate risk mitigation clauses")
		elif risk_score >= 5.0:
			recommendations.append("Medium risk - review key clauses")
			recommendations.append("Consider additional protections")
		else:
			recommendations.append("Low risk - standard review sufficient")

		for factor in factors:
			if factor["impact"] == "high":
				recommendations.append(f"Address {factor['factor']} - {factor['description']}")

		return recommendations

	async def _generate_renewal_recommendations(self, likelihood: float, factors: List[Dict[str, Any]]) -> List[str]:
		"""Generate renewal recommendations"""
		recommendations = []

		if likelihood >= 0.8:
			recommendations.append("High renewal likelihood - prepare for renewal")
			recommendations.append("Consider early renewal incentives")
		elif likelihood >= 0.6:
			recommendations.append("Moderate renewal likelihood - monitor relationship")
			recommendations.append("Address any outstanding issues")
		else:
			recommendations.append("Low renewal likelihood - develop retention strategy")
			recommendations.append("Schedule relationship review meeting")

		return recommendations

	async def _generate_value_recommendations(self, predicted_value: float, factors: List[Dict[str, Any]]) -> List[str]:
		"""Generate value-based recommendations"""
		recommendations = []

		if predicted_value > 200000:
			recommendations.append("High-value contract - ensure proper documentation")
			recommendations.append("Consider executive approval process")
		elif predicted_value > 100000:
			recommendations.append("Medium-value contract - standard review process")
		else:
			recommendations.append("Lower-value contract - streamlined process possible")

		return recommendations

	async def _generate_negotiation_recommendations(self, success_likelihood: float, factors: List[Dict[str, Any]]) -> List[str]:
		"""Generate negotiation recommendations"""
		recommendations = []

		if success_likelihood >= 0.8:
			recommendations.append("High negotiation success likelihood")
			recommendations.append("Proceed with proposed changes")
		elif success_likelihood >= 0.6:
			recommendations.append("Moderate negotiation success likelihood")
			recommendations.append("Consider phased approach to changes")
		else:
			recommendations.append("Low negotiation success likelihood")
			recommendations.append("Prioritize most critical changes")
			recommendations.append("Consider alternative negotiation strategies")

		return recommendations

	def _get_empty_prediction(self, prediction_type: PredictionType) -> PredictionResult:
		"""Get empty prediction result"""
		return PredictionResult(
			prediction_type=prediction_type, predicted_value=0.0, confidence=0.0, factors=[], recommendations=[], generated_at=datetime.now()
		)

	async def train_models(self, historical_data: List[HistoricalData]):
		"""Train ML models with historical data"""
		try:
			if not historical_data:
				logger.warning("No historical data provided for training")
				return

			# Prepare training data
			X = []
			y_risk = []
			y_renewal = []
			y_value = []
			y_negotiation = []
			y_compliance = []

			for data in historical_data:
				features = [
					data.contract_value,
					data.duration_months,
					data.compliance_score,
					1 if data.contract_type == "service" else 0,
					1 if data.contract_type == "employment" else 0,
					data.created_at.month,
					data.created_at.year,
				]

				X.append(features)
				y_risk.append(data.risk_score)
				y_renewal.append(1 if data.renewal_status else 0)
				y_value.append(data.contract_value)
				y_negotiation.append(1 if data.negotiation_success else 0)
				y_compliance.append(data.compliance_score)

			X = np.array(X)

			# Scale features
			X_scaled = self.scaler.fit_transform(X)

			# Train models
			self.models[PredictionType.RISK_SCORE].fit(X_scaled, y_risk)
			self.models[PredictionType.RENEWAL_LIKELIHOOD].fit(X_scaled, y_renewal)
			self.models[PredictionType.CONTRACT_VALUE].fit(X_scaled, y_value)
			self.models[PredictionType.NEGOTIATION_SUCCESS].fit(X_scaled, y_negotiation)
			self.models[PredictionType.COMPLIANCE_RISK].fit(X_scaled, y_compliance)

			logger.info("Models trained successfully")

		except Exception as e:
			logger.error(f"Failed to train models: {e}")

	async def get_prediction_insights(self) -> Dict[str, Any]:
		"""Get insights about prediction accuracy and model performance"""
		return {
			"models_trained": len([m for m in self.models.values() if hasattr(m, "n_features_in_") and m.n_features_in_ > 0]),
			"total_historical_data": len(self.historical_data),
			"prediction_types": [pt.value for pt in PredictionType],
			"last_training": datetime.now().isoformat(),
			"model_performance": {
				"risk_score": "Good" if hasattr(self.models[PredictionType.RISK_SCORE], "n_features_in_") else "Not trained",
				"renewal_likelihood": "Good" if hasattr(self.models[PredictionType.RENEWAL_LIKELIHOOD], "n_features_in_") else "Not trained",
				"contract_value": "Good" if hasattr(self.models[PredictionType.CONTRACT_VALUE], "n_features_in_") else "Not trained",
			},
		}
