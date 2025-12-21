"""
Preference Conflict Detector for Otto.AI
Identifies and resolves contradictory user preferences with intelligent questioning
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Type hints to avoid circular imports
GroqClient = Any
PreferenceEngine = Any
PreferenceCategory = Any
UserPreference = Any


class ConflictSeverity(Enum):
    """Severity levels for preference conflicts"""
    LOW = "low"           # Complementary preferences
    MEDIUM = "medium"     # Some tension, can be balanced
    HIGH = "high"         # Direct contradiction
    CRITICAL = "critical" # Mutually exclusive


class ConflictType(Enum):
    """Types of preference conflicts"""
    PERFORMANCE_VS_EFFICIENCY = "performance_vs_efficiency"
    BUDGET_VS_FEATURES = "budget_vs_features"
    SIZE_VS_EFFICIENCY = "size_vs_efficiency"
    POWER_VS_EMISSIONS = "power_vs_emissions"
    LUXURY_VS_PRACTICALITY = "luxury_vs_practicality"
    TECHNOLOGY_VS_SIMPLICITY = "technology_vs_simplicity"
    STYLE_VS_FUNCTION = "style_vs_function"


@dataclass
class PreferenceConflict:
    """Represents a detected conflict between preferences"""
    id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    preferences: List[UserPreference]
    description: str
    explanation: str
    resolution_strategies: List[str]
    recommended_questions: List[str]
    technological_solutions: List[str]


@dataclass
class ConflictResolution:
    """Represents a resolution strategy for a conflict"""
    strategy_id: str
    name: str
    description: str
    trade_offs: Dict[str, float]  # Preference vs adjustment
    compatible_technologies: List[str]
    questions_to_ask: List[str]


class PreferenceConflictDetector:
    """Detects and resolves conflicts in user preferences"""

    def __init__(
        self,
        groq_client: GroqClient,
        preference_engine: PreferenceEngine
    ):
        self.groq_client = groq_client
        self.preference_engine = preference_engine
        self.initialized = False

        # Conflict detection rules
        self.conflict_rules = self._initialize_conflict_rules()

        # Resolution strategies
        self.resolution_strategies = self._initialize_resolution_strategies()

        # Technology explanations
        self.technology_explanations = self._initialize_technology_explanations()

    async def initialize(self) -> bool:
        """Initialize the conflict detector"""
        try:
            if not self.groq_client.initialized:
                logger.error("Groq client not initialized")
                return False

            if not self.preference_engine.initialized:
                logger.error("Preference engine not initialized")
                return False

            self.initialized = True
            logger.info("Preference conflict detector initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize conflict detector: {e}")
            return False

    def _initialize_conflict_rules(self) -> Dict[ConflictType, Dict]:
        """Initialize rules for detecting conflicts"""
        return {
            ConflictType.PERFORMANCE_VS_EFFICIENCY: {
                "conflicting_pairs": [
                    (PreferenceCategory.PERFORMANCE, PreferenceCategory.ENVIRONMENT),
                    (PreferenceCategory.PERFORMANCE, PreferenceCategory.BUDGET)
                ],
                "indicators": ["fast", "powerful", "sport", "performance",
                             "efficient", "economical", "mileage", "mpg"],
                "thresholds": {"performance_score": 0.7, "efficiency_score": 0.7}
            },
            ConflictType.BUDGET_VS_FEATURES: {
                "conflicting_pairs": [
                    (PreferenceCategory.BUDGET, PreferenceCategory.FEATURE),
                    (PreferenceCategory.BUDGET, PreferenceCategory.TECHNOLOGY),
                    (PreferenceCategory.BUDGET, PreferenceCategory.SAFETY)
                ],
                "indicators": ["budget", "affordable", "cheap", "expensive",
                             "premium", "luxury", "fully loaded", "all features"],
                "thresholds": {"budget_constraint": 0.8, "feature_expectation": 0.8}
            },
            ConflictType.SIZE_VS_EFFICIENCY: {
                "conflicting_pairs": [
                    (PreferenceCategory.FAMILY_SIZE, PreferenceCategory.ENVIRONMENT),
                    (PreferenceCategory.VEHICLE_TYPE, PreferenceCategory.ENVIRONMENT)
                ],
                "indicators": ["large", "spacious", "suv", "truck", "minivan",
                             "small", "compact", "efficient", "hybrid", "electric"],
                "thresholds": {"size_preference": 0.7, "efficiency_preference": 0.7}
            },
            ConflictType.POWER_VS_EMISSIONS: {
                "conflicting_pairs": [
                    (PreferenceCategory.PERFORMANCE, PreferenceCategory.ENVIRONMENT)
                ],
                "indicators": ["v8", "turbo", "horsepower", "torque",
                             "emissions", "green", "eco", "hybrid", "electric"],
                "thresholds": {"power_desire": 0.7, "emission_concern": 0.7}
            },
            ConflictType.LUXURY_VS_PRACTICALITY: {
                "conflicting_pairs": [
                    (PreferenceCategory.STYLE, PreferenceCategory.BUDGET),
                    (PreferenceCategory.BRAND, PreferenceCategory.FEATURE)
                ],
                "indicators": ["luxury", "premium", "brand name", "status",
                             "practical", "functional", "utility", "value"],
                "thresholds": {"luxury_desire": 0.7, "practicality_need": 0.7}
            },
            ConflictType.TECHNOLOGY_VS_SIMPLICITY: {
                "conflicting_pairs": [
                    (PreferenceCategory.TECHNOLOGY, PreferenceCategory.FEATURE),
                    (PreferenceCategory.TECHNOLOGY, PreferenceCategory.STYLE)
                ],
                "indicators": ["technology", "features", "screens", "connected",
                             "simple", "basic", "minimal", "analog"],
                "thresholds": {"tech_preference": 0.7, "simplicity_preference": 0.7}
            }
        }

    def _initialize_resolution_strategies(self) -> Dict[ConflictType, List[ConflictResolution]]:
        """Initialize resolution strategies for different conflicts"""
        return {
            ConflictType.PERFORMANCE_VS_EFFICIENCY: [
                ConflictResolution(
                    strategy_id="hybrid_balance",
                    name="Hybrid Technology",
                    description="Hybrid vehicles offer both performance and efficiency through electric-assist power",
                    trade_offs={"performance": -0.1, "efficiency": 0.8},
                    compatible_technologies=["Hybrid", "Mild Hybrid", "Plug-in Hybrid"],
                    questions_to_ask=[
                        "Would you be open to a hybrid that uses both gas and electric power?",
                        "How important is instant acceleration versus overall efficiency?",
                        "Would you consider a performance-oriented hybrid?"
                    ]
                ),
                ConflictResolution(
                    strategy_id="turbo_efficiency",
                    name="Modern Turbo Engines",
                    description="Small turbocharged engines provide good performance while maintaining efficiency",
                    trade_offs={"performance": 0.3, "efficiency": 0.4},
                    compatible_technologies=["Turbocharged", "EcoBoost", "Turbo Hybrid"],
                    questions_to_ask=[
                        "Have you considered modern turbocharged engines?",
                        "Would you prefer immediate torque or top-end power?",
                        "How do you feel about smaller displacement engines with turbos?"
                    ]
                ),
                ConflictResolution(
                    strategy_id="priority_choice",
                    name="Priority Clarification",
                    description="Help user choose which aspect is more important",
                    trade_offs={"performance": 0.0, "efficiency": 0.0},
                    compatible_technologies=["User Choice Dependent"],
                    questions_to_ask=[
                        "If you had to choose, which matters more: acceleration or fuel savings?",
                        "Would you prefer better highway performance or city efficiency?",
                        "What's your monthly fuel budget versus performance needs?"
                    ]
                )
            ],
            ConflictType.BUDGET_VS_FEATURES: [
                ConflictResolution(
                    strategy_id="value_packages",
                    name="Value-Oriented Packages",
                    description="Find vehicles with essential features at reasonable prices",
                    trade_offs={"budget": 0.7, "features": 0.5},
                    compatible_technologies=["Value Packages", "Certified Pre-Owned", "Late-Model Used"],
                    questions_to_ask=[
                        "Which features are must-haves versus nice-to-haves?",
                        "Would you consider certified pre-owned for more features?",
                        "What's more important: newer vehicle or more features?"
                    ]
                ),
                ConflictResolution(
                    strategy_id="prioritization",
                    name="Feature Prioritization",
                    description="Identify and prioritize the most important features",
                    trade_offs={"budget": 0.5, "features": 0.7},
                    compatible_technologies=["Selective Features", "Base Model Plus Options"],
                    questions_to_ask=[
                        "Can you rank your top 3 must-have features?",
                        "Which safety features are non-negotiable?",
                        "Would you prefer to add features later or get them now?"
                    ]
                )
            ],
            ConflictType.SIZE_VS_EFFICIENCY: [
                ConflictResolution(
                    strategy_id="efficient_larges",
                    name="Efficient Large Vehicles",
                    description="Modern large vehicles with efficient powertrains",
                    trade_offs={"size": 0.9, "efficiency": 0.3},
                    compatible_technologies=["Hybrid SUV", "Diesel", "Turbocharged"],
                    questions_to_ask=[
                        "Would you consider a hybrid SUV for better efficiency?",
                        "How important is cargo space versus fuel economy?",
                        "Have you looked at modern crossover vehicles?"
                    ]
                ),
                ConflictResolution(
                    strategy_id="smart_compact",
                    name="Smart Compact Design",
                    description="Compact vehicles with intelligent space utilization",
                    trade_offs={"size": 0.5, "efficiency": 0.9},
                    compatible_technologies=["Compact SUV", "Wagon", "Flexible Seating"],
                    questions_to_ask=[
                        "Would flexible interior layouts help with space needs?",
                        "How often do you need maximum cargo space?",
                        "Would sliding seats or fold-flat seats be helpful?"
                    ]
                )
            ]
        }

    def _initialize_technology_explanations(self) -> Dict[str, str]:
        """Initialize explanations for different technologies"""
        return {
            "Hybrid": "Combines gasoline engine with electric motor for improved efficiency. The electric motor assists during acceleration, improving both performance and fuel economy.",
            "Plug-in Hybrid": "Similar to regular hybrid but with larger battery that can be charged. Offers 20-50 miles of electric-only range, perfect for daily commuting.",
            "Turbocharged": "Uses exhaust pressure to force more air into the engine, increasing power without significantly increasing fuel consumption. Modern turbos provide immediate torque.",
            "Mild Hybrid": "48-volt electric system that assists the engine but cannot drive the vehicle on electricity alone. Improves start/stop smoothness and adds slight electric boost.",
            "Diesel": "Compression ignition engine with high torque output. Excellent for towing and highway fuel economy, though less common in passenger vehicles now.",
            "EV": "Pure electric vehicle with zero emissions. Instant acceleration and low maintenance, though charging time and range are considerations.",
            "CVT": "Continuously Variable Transmission keeps engine at optimal RPM for efficiency. Smooth acceleration but different feel than traditional automatic.",
            "Start-Stop": "Automatically shuts off engine when stopped to save fuel. Modern systems are smooth and seamless.",
            "Cylinder Deactivation": "Shuts down unused cylinders at cruising speeds to save fuel. Automatically reactivates when power is needed."
        }

    async def detect_conflicts(
        self,
        preferences: List[UserPreference],
        context: Optional[Dict[str, Any]] = None
    ) -> List[PreferenceConflict]:
        """
        Detect conflicts between user preferences
        """
        if not self.initialized:
            logger.error("Conflict detector not initialized")
            return []

        conflicts = []

        try:
            # Check each conflict type
            for conflict_type, rules in self.conflict_rules.items():
                detected = await self._detect_conflict_type(
                    conflict_type, rules, preferences, context
                )
                conflicts.extend(detected)

            # Sort by severity
            conflicts.sort(key=lambda c: self._severity_order(c.severity), reverse=True)

            logger.info(f"Detected {len(conflicts)} preference conflicts")
            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
            return []

    async def _detect_conflict_type(
        self,
        conflict_type: ConflictType,
        rules: Dict,
        preferences: List[UserPreference],
        context: Optional[Dict[str, Any]]
    ) -> List[PreferenceConflict]:
        """Detect conflicts of a specific type"""
        conflicts = []

        # Group preferences by category
        prefs_by_category = {}
        for pref in preferences:
            if pref.category not in prefs_by_category:
                prefs_by_category[pref.category] = []
            prefs_by_category[pref.category].append(pref)

        # Check conflicting pairs
        for cat1, cat2 in rules["conflicting_pairs"]:
            if cat1 in prefs_by_category and cat2 in prefs_by_category:
                for pref1 in prefs_by_category[cat1]:
                    for pref2 in prefs_by_category[cat2]:
                        # Check threshold values
                        if self._exceeds_thresholds(pref1, pref2, rules["thresholds"]):
                            severity = await self._calculate_severity(pref1, pref2, rules)

                            conflict = PreferenceConflict(
                                id=f"{conflict_type.value}_{len(conflicts)}_{datetime.now().strftime('%H%M%S')}",
                                conflict_type=conflict_type,
                                severity=severity,
                                preferences=[pref1, pref2],
                                description=self._generate_conflict_description(pref1, pref2, conflict_type),
                                explanation=await self._generate_conflict_explanation(pref1, pref2, conflict_type),
                                resolution_strategies=[r.name for r in self.resolution_strategies.get(conflict_type, [])],
                                recommended_questions=await self._generate_conflict_questions(pref1, pref2, conflict_type),
                                technological_solutions=await self._suggest_technological_solutions(pref1, pref2, conflict_type)
                            )
                            conflicts.append(conflict)

        return conflicts

    def _exceeds_thresholds(
        self,
        pref1: UserPreference,
        pref2: UserPreference,
        thresholds: Dict[str, float]
    ) -> bool:
        """Check if preferences exceed conflict thresholds"""
        # This would need to be adapted to actual UserPreference structure
        # Assuming preferences have confidence scores
        conf1 = getattr(pref1, 'confidence', 0.5)
        conf2 = getattr(pref2, 'confidence', 0.5)

        # Check against thresholds based on category
        for key, threshold in thresholds.items():
            if "performance" in key.lower() and pref1.category == PreferenceCategory.PERFORMANCE:
                if conf1 > threshold:
                    return True
            if "efficiency" in key.lower() and pref2.category == PreferenceCategory.ENVIRONMENT:
                if conf2 > threshold:
                    return True
            # Add more category checks as needed

        return False

    async def _calculate_severity(
        self,
        pref1: UserPreference,
        pref2: UserPreference,
        rules: Dict
    ) -> ConflictSeverity:
        """Calculate the severity of a conflict"""
        # Get confidence scores
        conf1 = getattr(pref1, 'confidence', 0.5)
        conf2 = getattr(pref2, 'confidence', 0.5)

        # Check for direct contradiction indicators
        text1 = getattr(pref1, 'value', '').lower()
        text2 = getattr(pref2, 'value', '').lower()

        # Look for direct opposites
        opposites = [
            ("fast", "slow"), ("powerful", "efficient"), ("large", "small"),
            ("expensive", "affordable"), ("luxury", "basic"), ("sport", "economy")
        ]

        for opp1, opp2 in opposites:
            if (opp1 in text1 and opp2 in text2) or (opp2 in text1 and opp1 in text2):
                return ConflictSeverity.CRITICAL

        # Calculate based on confidence scores
        avg_confidence = (conf1 + conf2) / 2

        if avg_confidence > 0.85:
            return ConflictSeverity.HIGH
        elif avg_confidence > 0.7:
            return ConflictSeverity.MEDIUM
        elif avg_confidence > 0.5:
            return ConflictSeverity.LOW
        else:
            return ConflictSeverity.LOW

    def _generate_conflict_description(
        self,
        pref1: UserPreference,
        pref2: UserPreference,
        conflict_type: ConflictType
    ) -> str:
        """Generate a human-readable description of the conflict"""
        category_map = {
            PreferenceCategory.PERFORMANCE: "performance requirements",
            PreferenceCategory.ENVIRONMENT: "efficiency/environmental concerns",
            PreferenceCategory.BUDGET: "budget constraints",
            PreferenceCategory.FEATURE: "feature expectations",
            PreferenceCategory.FAMILY_SIZE: "space requirements",
            PreferenceCategory.VEHICLE_TYPE: "vehicle type preference"
        }

        desc1 = category_map.get(pref1.category, "preference")
        desc2 = category_map.get(pref2.category, "preference")

        conflict_names = {
            ConflictType.PERFORMANCE_VS_EFFICIENCY: "Performance vs Efficiency Conflict",
            ConflictType.BUDGET_VS_FEATURES: "Budget vs Features Conflict",
            ConflictType.SIZE_VS_EFFICIENCY: "Size vs Efficiency Conflict",
            ConflictType.POWER_VS_EMISSIONS: "Power vs Emissions Conflict",
            ConflictType.LUXURY_VS_PRACTICALITY: "Luxury vs Practicality Conflict",
            ConflictType.TECHNOLOGY_VS_SIMPLICITY: "Technology vs Simplicity Conflict"
        }

        return f"{conflict_names.get(conflict_type, 'Preference Conflict')}: " \
               f"Your {desc1} may conflict with your {desc2}"

    async def _generate_conflict_explanation(
        self,
        pref1: UserPreference,
        pref2: UserPreference,
        conflict_type: ConflictType
    ) -> str:
        """Generate an explanation of why this is a conflict and how to resolve it"""

        explanations = {
            ConflictType.PERFORMANCE_VS_EFFICIENCY:
                "Performance-focused vehicles typically prioritize power and acceleration, "
                "which often comes at the cost of fuel efficiency. However, modern technologies "
                "like hybrid systems and turbocharging can provide a good balance of both.",

            ConflictType.BUDGET_VS_FEATURES:
                "High-end features and luxury options increase vehicle cost significantly. "
                "However, many manufacturers offer well-equipped vehicles at reasonable prices, "
                "and certified pre-owned options can provide premium features at lower costs.",

            ConflictType.SIZE_VS_EFFICIENCY:
                "Larger vehicles typically have lower fuel efficiency due to weight and aerodynamics. "
                "Modern hybrid and diesel options in larger vehicles have significantly improved efficiency, "
                "while some compact vehicles offer surprisingly spacious interiors.",

            ConflictType.POWER_VS_EMISSIONS:
                "High-performance engines often produce more emissions, while eco-friendly vehicles "
                "prioritize low emissions over power. Electric performance vehicles and efficient "
                "turbocharged engines can provide both power and lower emissions.",

            ConflictType.LUXURY_VS_PRACTICALITY:
                "Luxury vehicles focus on premium materials and advanced features, which can impact "
                "practicality through higher costs and complex systems. Many mainstream brands now "
                "offer premium features with better practicality and value.",

            ConflictType.TECHNOLOGY_VS_SIMPLICITY:
                "Advanced technology features can be complex and may require learning curves, "
                "while simple interfaces are intuitive but may lack modern conveniences. "
                "Many vehicles now offer customizable technology levels."
        }

        base_explanation = explanations.get(conflict_type, "This preference combination presents a challenge that requires careful consideration of trade-offs.")

        # Add specific context based on actual preferences
        pref1_val = getattr(pref1, 'value', str(pref1.category))
        pref2_val = getattr(pref2, 'value', str(pref2.category))

        return f"{base_explanation} You've indicated interest in {pref1_val} while also wanting {pref2_val}."

    async def _generate_conflict_questions(
        self,
        pref1: UserPreference,
        pref2: UserPreference,
        conflict_type: ConflictType
    ) -> List[str]:
        """Generate questions to help resolve the conflict"""

        # Get questions from resolution strategies
        questions = []
        strategies = self.resolution_strategies.get(conflict_type, [])

        for strategy in strategies[:2]:  # Take first 2 strategies
            questions.extend(strategy.questions_to_ask[:2])  # Take first 2 questions from each

        # Add general clarification questions
        general_questions = [
            "If you had to prioritize, which of these is more important to you?",
            "Are there specific scenarios where one preference matters more than the other?",
            "Would you be open to a compromise solution that balances both aspects?"
        ]

        questions.extend(general_questions[:1])  # Add one general question

        return questions[:4]  # Return max 4 questions

    async def _suggest_technological_solutions(
        self,
        pref1: UserPreference,
        pref2: UserPreference,
        conflict_type: ConflictType
    ) -> List[str]:
        """Suggest technological solutions that can resolve the conflict"""

        solutions = []
        strategies = self.resolution_strategies.get(conflict_type, [])

        # Collect technologies from strategies
        for strategy in strategies:
            if strategy.compatible_technologies:
                solutions.extend(strategy.compatible_technologies[:2])

        # Remove duplicates
        unique_solutions = list(set(solutions))

        return unique_solutions[:5]  # Return max 5 solutions

    def _severity_order(self, severity: ConflictSeverity) -> int:
        """Return numeric value for sorting by severity"""
        order = {
            ConflictSeverity.CRITICAL: 4,
            ConflictSeverity.HIGH: 3,
            ConflictSeverity.MEDIUM: 2,
            ConflictSeverity.LOW: 1
        }
        return order.get(severity, 0)

    async def get_explanation_for_technology(self, technology: str) -> str:
        """Get explanation for a specific technology"""
        return self.technology_explanations.get(technology,
            f"{technology} is a technology that can help balance competing preferences. "
            "Please ask for more specific information about this feature.")

    async def generate_resolution_summary(
        self,
        conflict: PreferenceConflict,
        selected_resolution: str
    ) -> str:
        """Generate a summary of how the conflict will be resolved"""

        summary = f"To address the {conflict.conflict_type.value.replace('_', ' ')} "
        summary += f"between your preference for {conflict.preferences[0].category.value} "
        summary += f"and {conflict.preferences[1].category.value}, "

        if selected_resolution in self.technology_explanations:
            summary += f"I recommend considering {selected_resolution}. "
            summary += self.technology_explanations[selected_resolution]
        else:
            summary += f"we'll focus on {selected_resolution}. "
            summary += "This approach will help balance both of your important preferences."

        return summary