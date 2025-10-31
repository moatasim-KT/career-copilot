"""
Feedback analysis service for pattern recognition and model improvement
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from collections import defaultdict
import statistics

from app.models.feedback import JobRecommendationFeedback
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeedbackAnalysisService:
	"""Service for analyzing feedback patterns and improving recommendation algorithms"""

	def __init__(self, db: Session):
		self.db = db

	def analyze_feedback_patterns(self, days_back: int = 30) -> Dict[str, Any]:
		"""
		Analyze feedback patterns to identify areas for improvement
		"""
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)

		feedback_data = self.db.query(JobRecommendationFeedback).filter(JobRecommendationFeedback.created_at >= cutoff_date).all()

		if not feedback_data:
			return {"total_feedback": 0, "patterns": {}, "recommendations": []}

		patterns = {
			"skill_match_analysis": self._analyze_skill_match_patterns(feedback_data),
			"location_match_analysis": self._analyze_location_match_patterns(feedback_data),
			"experience_level_analysis": self._analyze_experience_level_patterns(feedback_data),
			"match_score_analysis": self._analyze_match_score_patterns(feedback_data),
			"temporal_analysis": self._analyze_temporal_patterns(feedback_data),
		}

		recommendations = self._generate_improvement_recommendations(patterns)

		return {
			"total_feedback": len(feedback_data),
			"analysis_period_days": days_back,
			"patterns": patterns,
			"recommendations": recommendations,
			"analyzed_at": datetime.now(timezone.utc).isoformat(),
		}

	def _analyze_skill_match_patterns(self, feedback_data: List[JobRecommendationFeedback]) -> Dict[str, Any]:
		"""Analyze how skill matching affects feedback quality"""
		skill_feedback = defaultdict(lambda: {"helpful": 0, "unhelpful": 0})

		for feedback in feedback_data:
			if not feedback.user_skills_at_time or not feedback.job_tech_stack:
				continue

			user_skills = set(s.lower() for s in feedback.user_skills_at_time)
			job_skills = set(s.lower() for s in feedback.job_tech_stack)

			# Calculate skill overlap
			overlap = len(user_skills.intersection(job_skills))
			total_job_skills = len(job_skills)

			if total_job_skills > 0:
				overlap_percentage = (overlap / total_job_skills) * 100

				# Categorize overlap
				if overlap_percentage >= 70:
					category = "high_overlap"
				elif overlap_percentage >= 40:
					category = "medium_overlap"
				else:
					category = "low_overlap"

				if feedback.is_helpful:
					skill_feedback[category]["helpful"] += 1
				else:
					skill_feedback[category]["unhelpful"] += 1

		# Calculate satisfaction rates
		analysis = {}
		for category, counts in skill_feedback.items():
			total = counts["helpful"] + counts["unhelpful"]
			if total > 0:
				satisfaction_rate = counts["helpful"] / total
				analysis[category] = {
					"total_feedback": total,
					"helpful_count": counts["helpful"],
					"unhelpful_count": counts["unhelpful"],
					"satisfaction_rate": satisfaction_rate,
				}

		return analysis

	def _analyze_location_match_patterns(self, feedback_data: List[JobRecommendationFeedback]) -> Dict[str, Any]:
		"""Analyze how location matching affects feedback quality"""
		location_feedback = defaultdict(lambda: {"helpful": 0, "unhelpful": 0})

		for feedback in feedback_data:
			if not feedback.user_preferred_locations or not feedback.job_location:
				continue

			user_locations = set(l.lower() for l in feedback.user_preferred_locations)
			job_location = feedback.job_location.lower()

			# Determine match type
			if "remote" in user_locations and "remote" in job_location:
				match_type = "remote_match"
			elif any(loc in job_location for loc in user_locations):
				match_type = "location_match"
			elif "remote" in user_locations:
				match_type = "remote_preferred_onsite_job"
			else:
				match_type = "no_match"

			if feedback.is_helpful:
				location_feedback[match_type]["helpful"] += 1
			else:
				location_feedback[match_type]["unhelpful"] += 1

		# Calculate satisfaction rates
		analysis = {}
		for match_type, counts in location_feedback.items():
			total = counts["helpful"] + counts["unhelpful"]
			if total > 0:
				satisfaction_rate = counts["helpful"] / total
				analysis[match_type] = {
					"total_feedback": total,
					"helpful_count": counts["helpful"],
					"unhelpful_count": counts["unhelpful"],
					"satisfaction_rate": satisfaction_rate,
				}

		return analysis

	def _analyze_experience_level_patterns(self, feedback_data: List[JobRecommendationFeedback]) -> Dict[str, Any]:
		"""Analyze how experience level matching affects feedback quality"""
		exp_feedback = defaultdict(lambda: {"helpful": 0, "unhelpful": 0})

		for feedback in feedback_data:
			if not feedback.user_experience_level:
				continue

			user_exp = feedback.user_experience_level.lower()

			# Extract experience level from job context if available
			job_context = feedback.recommendation_context or {}
			job_title = job_context.get("job_title", "").lower() if "job_title" in job_context else ""

			# Determine experience match
			if user_exp in job_title:
				match_type = "exact_match"
			elif (user_exp == "junior" and any(term in job_title for term in ["entry", "associate"])) or (
				user_exp == "senior" and any(term in job_title for term in ["lead", "principal"])
			):
				match_type = "related_match"
			else:
				match_type = "no_clear_match"

			if feedback.is_helpful:
				exp_feedback[match_type]["helpful"] += 1
			else:
				exp_feedback[match_type]["unhelpful"] += 1

		# Calculate satisfaction rates
		analysis = {}
		for match_type, counts in exp_feedback.items():
			total = counts["helpful"] + counts["unhelpful"]
			if total > 0:
				satisfaction_rate = counts["helpful"] / total
				analysis[match_type] = {
					"total_feedback": total,
					"helpful_count": counts["helpful"],
					"unhelpful_count": counts["unhelpful"],
					"satisfaction_rate": satisfaction_rate,
				}

		return analysis

	def _analyze_match_score_patterns(self, feedback_data: List[JobRecommendationFeedback]) -> Dict[str, Any]:
		"""Analyze how match scores correlate with feedback quality"""
		score_ranges = {"high": (80, 100), "medium": (50, 79), "low": (0, 49)}

		score_feedback = defaultdict(lambda: {"helpful": 0, "unhelpful": 0, "scores": []})

		for feedback in feedback_data:
			if feedback.match_score is None:
				continue

			score = feedback.match_score

			# Determine score range
			range_name = "low"
			for range_key, (min_score, max_score) in score_ranges.items():
				if min_score <= score <= max_score:
					range_name = range_key
					break

			score_feedback[range_name]["scores"].append(score)

			if feedback.is_helpful:
				score_feedback[range_name]["helpful"] += 1
			else:
				score_feedback[range_name]["unhelpful"] += 1

		# Calculate statistics
		analysis = {}
		for range_name, data in score_feedback.items():
			total = data["helpful"] + data["unhelpful"]
			if total > 0:
				satisfaction_rate = data["helpful"] / total
				avg_score = statistics.mean(data["scores"]) if data["scores"] else 0

				analysis[range_name] = {
					"total_feedback": total,
					"helpful_count": data["helpful"],
					"unhelpful_count": data["unhelpful"],
					"satisfaction_rate": satisfaction_rate,
					"average_score": avg_score,
					"score_range": score_ranges[range_name],
				}

		return analysis

	def _analyze_temporal_patterns(self, feedback_data: List[JobRecommendationFeedback]) -> Dict[str, Any]:
		"""Analyze feedback patterns over time"""
		daily_feedback = defaultdict(lambda: {"helpful": 0, "unhelpful": 0})

		for feedback in feedback_data:
			date_key = feedback.created_at.date().isoformat()

			if feedback.is_helpful:
				daily_feedback[date_key]["helpful"] += 1
			else:
				daily_feedback[date_key]["unhelpful"] += 1

		# Calculate daily satisfaction rates
		daily_analysis = {}
		for date, counts in daily_feedback.items():
			total = counts["helpful"] + counts["unhelpful"]
			if total > 0:
				satisfaction_rate = counts["helpful"] / total
				daily_analysis[date] = {
					"total_feedback": total,
					"helpful_count": counts["helpful"],
					"unhelpful_count": counts["unhelpful"],
					"satisfaction_rate": satisfaction_rate,
				}

		# Calculate overall trends
		satisfaction_rates = [data["satisfaction_rate"] for data in daily_analysis.values()]

		return {
			"daily_breakdown": daily_analysis,
			"average_daily_satisfaction": statistics.mean(satisfaction_rates) if satisfaction_rates else 0,
			"satisfaction_trend": "improving"
			if len(satisfaction_rates) > 1 and satisfaction_rates[-1] > satisfaction_rates[0]
			else "declining"
			if len(satisfaction_rates) > 1
			else "stable",
		}

	def _generate_improvement_recommendations(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Generate actionable recommendations based on pattern analysis"""
		recommendations = []

		# Skill matching recommendations
		skill_analysis = patterns.get("skill_match_analysis", {})
		if skill_analysis:
			low_overlap_data = skill_analysis.get("low_overlap", {})
			if low_overlap_data and low_overlap_data.get("satisfaction_rate", 0) < 0.5:
				recommendations.append(
					{
						"type": "algorithm_adjustment",
						"priority": "high",
						"area": "skill_matching",
						"recommendation": "Increase skill matching weight in recommendation algorithm",
						"current_weight": 50,
						"suggested_weight": 60,
						"reason": f"Low skill overlap jobs have {low_overlap_data.get('satisfaction_rate', 0):.1%} satisfaction rate",
					}
				)

		# Location matching recommendations
		location_analysis = patterns.get("location_match_analysis", {})
		if location_analysis:
			remote_mismatch = location_analysis.get("remote_preferred_onsite_job", {})
			if remote_mismatch and remote_mismatch.get("satisfaction_rate", 0) < 0.3:
				recommendations.append(
					{
						"type": "algorithm_adjustment",
						"priority": "medium",
						"area": "location_matching",
						"recommendation": "Reduce weight for non-remote jobs when user prefers remote",
						"reason": f"Remote-preferring users show {remote_mismatch.get('satisfaction_rate', 0):.1%} satisfaction with onsite jobs",
					}
				)

		# Match score recommendations
		score_analysis = patterns.get("match_score_analysis", {})
		if score_analysis:
			high_score_data = score_analysis.get("high", {})
			if high_score_data and high_score_data.get("satisfaction_rate", 0) < 0.8:
				recommendations.append(
					{
						"type": "algorithm_review",
						"priority": "high",
						"area": "scoring_accuracy",
						"recommendation": "Review scoring algorithm - high scores not correlating with satisfaction",
						"reason": f"High-scoring recommendations only have {high_score_data.get('satisfaction_rate', 0):.1%} satisfaction rate",
					}
				)

		# Temporal recommendations
		temporal_analysis = patterns.get("temporal_analysis", {})
		if temporal_analysis.get("satisfaction_trend") == "declining":
			recommendations.append(
				{
					"type": "urgent_review",
					"priority": "critical",
					"area": "overall_performance",
					"recommendation": "Immediate algorithm review needed - satisfaction declining over time",
					"reason": "User satisfaction trend is declining",
				}
			)

		return recommendations

	def get_algorithm_adjustment_suggestions(self) -> Dict[str, Any]:
		"""Get specific suggestions for algorithm weight adjustments"""
		analysis = self.analyze_feedback_patterns(days_back=30)
		patterns = analysis.get("patterns", {})

		current_weights = {"skill_matching": 50, "location_matching": 30, "experience_matching": 20}

		suggested_weights = current_weights.copy()
		adjustments = []

		# Analyze skill matching effectiveness
		skill_analysis = patterns.get("skill_match_analysis", {})
		if skill_analysis:
			high_overlap = skill_analysis.get("high_overlap", {})
			low_overlap = skill_analysis.get("low_overlap", {})

			if high_overlap and low_overlap:
				high_satisfaction = high_overlap.get("satisfaction_rate", 0)
				low_satisfaction = low_overlap.get("satisfaction_rate", 0)

				if high_satisfaction > 0.8 and low_satisfaction < 0.4:
					# Strong correlation - increase skill weight
					suggested_weights["skill_matching"] = min(60, current_weights["skill_matching"] + 10)
					adjustments.append(
						{
							"weight": "skill_matching",
							"change": +10,
							"reason": f"High skill overlap shows {high_satisfaction:.1%} satisfaction vs {low_satisfaction:.1%} for low overlap",
						}
					)

		# Analyze location matching effectiveness
		location_analysis = patterns.get("location_match_analysis", {})
		if location_analysis:
			remote_match = location_analysis.get("remote_match", {})
			no_match = location_analysis.get("no_match", {})

			if remote_match and no_match:
				remote_satisfaction = remote_match.get("satisfaction_rate", 0)
				no_match_satisfaction = no_match.get("satisfaction_rate", 0)

				if remote_satisfaction > 0.9 and no_match_satisfaction < 0.3:
					# Strong location preference - increase location weight
					suggested_weights["location_matching"] = min(40, current_weights["location_matching"] + 10)
					adjustments.append(
						{"weight": "location_matching", "change": +10, "reason": f"Location matching shows strong correlation with satisfaction"}
					)

		# Ensure weights sum to 100
		total_weight = sum(suggested_weights.values())
		if total_weight != 100:
			# Proportionally adjust to maintain 100% total
			factor = 100 / total_weight
			for key in suggested_weights:
				suggested_weights[key] = round(suggested_weights[key] * factor)

		return {
			"current_weights": current_weights,
			"suggested_weights": suggested_weights,
			"adjustments": adjustments,
			"confidence_score": self._calculate_adjustment_confidence(analysis),
			"sample_size": analysis.get("total_feedback", 0),
		}

	def _calculate_adjustment_confidence(self, analysis: Dict[str, Any]) -> float:
		"""Calculate confidence score for weight adjustments based on sample size and pattern strength"""
		total_feedback = analysis.get("total_feedback", 0)

		# Base confidence on sample size
		if total_feedback < 10:
			base_confidence = 0.1
		elif total_feedback < 50:
			base_confidence = 0.5
		elif total_feedback < 100:
			base_confidence = 0.7
		else:
			base_confidence = 0.9

		# Adjust based on pattern clarity
		patterns = analysis.get("patterns", {})
		pattern_strength = 0
		pattern_count = 0

		for pattern_type, pattern_data in patterns.items():
			if isinstance(pattern_data, dict):
				for category, data in pattern_data.items():
					if isinstance(data, dict) and "satisfaction_rate" in data:
						# Strong patterns have clear satisfaction differences
						satisfaction = data["satisfaction_rate"]
						if satisfaction > 0.8 or satisfaction < 0.2:
							pattern_strength += 1
						pattern_count += 1

		if pattern_count > 0:
			pattern_clarity = pattern_strength / pattern_count
			return min(1.0, base_confidence * (0.5 + pattern_clarity))

		return base_confidence
