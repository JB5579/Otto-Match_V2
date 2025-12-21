"""
Template Engine for Otto AI Conversation Scenarios
Manages templates for common vehicle discovery conversation patterns
"""

import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from src.conversation.nlu_service import UserPreference, Entity
from src.conversation.intent_models import EntityType

# Configure logging
logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Types of conversation scenarios"""
    FIRST_TIME_BUYER = "first_time_buyer"
    FAMILY_VEHICLE = "family_vehicle"
    BUYER_WITH_BUDGET = "budget_focused"
    VEHICLE_TYPE_EXPLORATION = "vehicle_exploration"
    FEATURE_FOCUSED = "feature_focused"
    BRAND_LOYAL = "brand_loyal"
    UPGRADE_SEEKER = "upgrade_seeker"
    ENVIRONMENTALLY_CONSCIOUS = "eco_conscious"
    PERFORMANCE_ENTHUSIAST = "performance_enthusiast"
    PRACTICAL_COMMUTER = "practical_commuter"


@dataclass
class ConversationTemplate:
    """Template for conversation scenarios"""
    scenario_id: str
    scenario_type: ScenarioType
    triggers: List[str]  # Keywords/phrases that trigger this scenario
    user_profile: Dict[str, Any]  # Expected user characteristics
    conversation_flow: List[Dict[str, Any]]  # Steps in conversation
    variable_mappings: Dict[str, str]  # How to extract variables
    response_templates: Dict[str, List[str]]  # Response variations
    exit_conditions: List[str]  # When to exit this scenario
    success_metrics: List[str]  # What indicates success


@dataclass
class TemplateContext:
    """Context for template rendering"""
    user_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    current_step: int = 0
    collected_info: Dict[str, Any] = field(default_factory=dict)
    step_responses: Dict[int, str] = field(default_factory=dict)


class ScenarioManager:
    """Manages conversation scenario detection and selection"""

    def __init__(self):
        self.scenarios = self._initialize_scenarios()
        self.active_scenarios: Dict[str, Dict[str, Any]] = {}

    def _initialize_scenarios(self) -> Dict[ScenarioType, ConversationTemplate]:
        """Initialize all conversation scenario templates"""

        scenarios = {}

        # First-Time Buyer Scenario
        scenarios[ScenarioType.FIRST_TIME_BUYER] = ConversationTemplate(
            scenario_id="first_time_buyer_001",
            scenario_type=ScenarioType.FIRST_TIME_BUYER,
            triggers=["first car", "never bought", "new driver", "learning", "beginner"],
            user_profile={
                "experience": "novice",
                "knowledge_level": "low",
                "needs_guidance": True,
                "price_sensitive": True
            },
            conversation_flow=[
                {
                    "step": 1,
                    "purpose": "Welcome and reassure",
                    "extract": ["experience_level", "concerns"],
                    "respond": "reassurance"
                },
                {
                    "step": 2,
                    "purpose": "Understand basic needs",
                    "extract": ["primary_use", "passengers"],
                    "respond": "needs_assessment"
                },
                {
                    "step": 3,
                    "purpose": "Discuss budget realistically",
                    "extract": ["budget", "financing_needs"],
                    "respond": "budget_guidance"
                },
                {
                    "step": 4,
                    "purpose": "Educate about key factors",
                    "extract": ["priorities"],
                    "respond": "education"
                },
                {
                    "step": 5,
                    "purpose": "Make initial recommendations",
                    "extract": [],
                    "respond": "recommendations"
                }
            ],
            variable_mappings={
                "primary_use": "What will you use the car for most?",
                "passengers": "How many people will regularly ride with you?",
                "budget": "What's your budget range?",
                "financing_needs": "Will you need financing?"
            },
            response_templates={
                "reassurance": [
                    "That's exciting! Buying your first car is a big step, and I'm here to make it as smooth as possible. We'll take it one step at a time.",
                    "Welcome to car shopping! Don't worry - everyone starts somewhere, and I'll help guide you through the process. No question is too basic!",
                    "I love helping first-time buyers! We'll find you a reliable car that fits your needs and budget. Let's start with the basics."
                ],
                "needs_assessment": [
                    "Let's figure out what kind of car would work best for you. What's the main thing you'll use it for? Getting to work, school, road trips?",
                    "To help you find the perfect first car, tell me a bit about your lifestyle. Do you commute far? Carry lots of stuff? Have friends who'll ride with you?"
                ],
                "budget_guidance": [
                    "It's smart to think about the total cost, not just the sticker price. Don't forget insurance, gas, and maintenance. What feels comfortable for your monthly budget?",
                    "Let's talk budget in a way that makes sense. Besides the car payment, you'll want to budget about $100-200 monthly for gas and maintenance. What range works for you?"
                ],
                "education": [
                    "Here are the key things to look for in your first car: reliability is crucial, safety features are a must, and good fuel efficiency saves money. Of these, which matters most to you?",
                    "For a first car, I always recommend focusing on reliability ratings and safety features. Hondas and Toyotas are great starting points. What concerns you most about car ownership?"
                ],
                "recommendations": [
                    "Based on what you've told me, I'd recommend looking at reliable compact cars like the Honda Civic or Toyota Corolla. They're affordable to own and practically maintenance-free. Would you like to see some options?",
                    "For your first car, consider these proven winners: Mazda3 (fun to drive), Honda Civic (reliable), or Hyundai Elantra (great warranty). Which of these sounds most appealing?"
                ]
            },
            exit_conditions=[
                "user makes choice",
                "user requests different scenario",
                "user gets specific vehicle recommendations"
            ],
            success_metrics=[
                "user feels confident",
                "user understands total cost",
                "user has suitable options"
            ]
        )

        # Family Vehicle Scenario
        scenarios[ScenarioType.FAMILY_VEHICLE] = ConversationTemplate(
            scenario_id="family_vehicle_001",
            scenario_type=ScenarioType.FAMILY_VEHICLE,
            triggers=["family", "kids", "children", "car seats", "groceries", "sports", "activities"],
            user_profile={
                "priority": "practicality",
                "concerns": ["safety", "space", "reliability"],
                "passengers": "multiple"
            },
            conversation_flow=[
                {
                    "step": 1,
                    "purpose": "Understand family size",
                    "extract": ["family_size", "ages"],
                    "respond": "family_acknowledgment"
                },
                {
                    "step": 2,
                    "purpose": "Identify space needs",
                    "extract": ["cargo_needs", "activities"],
                    "respond": "space_assessment"
                },
                {
                    "step": 3,
                    "purpose": "Safety priorities",
                    "extract": ["safety_features", "concerns"],
                    "respond": "safety_focus"
                },
                {
                    "step": 4,
                    "purpose": "Lifestyle considerations",
                    "extract": ["commute", "trips", "hobbies"],
                    "respond": "lifestyle_match"
                },
                {
                    "step": 5,
                    "purpose": "Vehicle type recommendations",
                    "extract": [],
                    "respond": "vehicle_recommendations"
                }
            ],
            variable_mappings={
                "family_size": "How many people are in your family?",
                "ages": "What are the ages of your children?",
                "cargo_needs": "What do you typically carry? Groceries, sports equipment, strollers?",
                "activities": "What family activities will the car support?"
            },
            response_templates={
                "family_acknowledgment": [
                    "Finding the right family vehicle is so important! How many people will regularly be riding in the car? And do you have little ones who need car seats?",
                    "Family vehicles need to balance so many needs - safety, space, and practicality. Tell me about your family situation so I can find the perfect fit."
                ],
                "space_assessment": [
                    "Family life means carrying lots of stuff! Beyond groceries, do you haul sports equipment, strollers, or camping gear? This helps determine if you need extra cargo space.",
                    "Let's talk about what your family carries. From school projects to sports gear to family road trips - what's your typical cargo situation?"
                ],
                "safety_focus": [
                    "Your family's safety is top priority. Modern cars have amazing safety features - automatic braking, blind spot monitoring, rear cameras. Which safety features are must-haves for you?",
                    "As a parent, safety is non-negotiable. Are you looking for specific safety ratings or features? I can recommend vehicles with top IIHS and NHTSA ratings."
                ],
                "lifestyle_match": [
                    "Your daily routine really influences the best choice. Do you have a long commute? Take frequent road trips? Need good gas mileage for school runs?",
                    "Think about your family's lifestyle. City driving requires different features than highway cruising. What does your typical week look like?"
                ],
                "vehicle_recommendations": [
                    "For growing families, I always recommend 3-row SUVs like the Honda Pilot or Toyota Highlander, or minivans like the Honda Odyssey. The extra space is worth its weight in gold!",
                    "Based on your family needs, consider these family favorites: Kia Telluride (great value), Subaru Ascent (standard AWD), or Chrysler Pacifica (Stow 'n Go seats). Which interests you most?"
                ]
            },
            exit_conditions=[
                "user selects vehicle type",
                "user focuses on specific models",
                "space requirements are met"
            ],
            success_metrics=[
                "adequate space confirmed",
                "safety features identified",
                "family needs matched"
            ]
        )

        # Budget-Focused Scenario
        scenarios[ScenarioType.BUYER_WITH_BUDGET] = ConversationTemplate(
            scenario_id="budget_buyer_001",
            scenario_type=ScenarioType.BUYER_WITH_BUDGET,
            triggers=["budget", "afford", "cheap", "under", "payment", "cost"],
            user_profile={
                "primary_concern": "price",
                "value_oriented": True,
                "needs_tco_education": True
            },
            conversation_flow=[
                {
                    "step": 1,
                    "purpose": "Establish budget boundaries",
                    "extract": ["max_budget", "payment_preference"],
                    "respond": "budget_acknowledgment"
                },
                {
                    "step": 2,
                    "purpose": "Educate on total cost",
                    "extract": ["insurance_knowledge", "maintenance_budget"],
                    "respond": "tco_education"
                },
                {
                    "step": 3,
                    "purpose": "Identify best value options",
                    "extract": ["priority_features"],
                    "respond": "value_recommendations"
                },
                {
                    "step": 4,
                    "purpose": "Discuss used vs new",
                    "extract": ["used_acceptance", "certified_preference"],
                    "respond": "ownership_options"
                },
                {
                    "step": 5,
                    "purpose": "Final recommendations",
                    "extract": [],
                    "respond": "final_suggestions"
                }
            ],
            variable_mappings={
                "max_budget": "What's your maximum budget?",
                "payment_preference": "Do you prefer to pay cash or finance?",
                "maintenance_budget": "How much can you budget monthly for maintenance?"
            },
            response_templates={
                "budget_acknowledgment": [
                    "Being budget-conscious is smart! I'll help you get the most value for your money. What's your maximum budget? And remember to factor in about $150-200 monthly for insurance and maintenance.",
                    "I love finding great value for budget-minded shoppers! What price range feels comfortable? And are you paying cash or financing?"
                ],
                "tco_education": [
                    "Let's talk total cost of ownership. Some cars cost more to insure or maintain. Asian brands typically cost less to maintain. Do you have a monthly budget for maintenance and repairs?",
                    "Beyond the purchase price, insurance can vary wildly - minivans and sedans are usually cheapest. What's your insurance situation like?"
                ],
                "value_recommendations": [
                    "For maximum value, consider these reliable options: Honda Civic (holds value like crazy), Toyota Corolla (practually maintenance-free), or Hyundai Elantra (amazing warranty). All under your budget!",
                    "Here's where your dollar goes farthest: Used Japanese cars (2015+ with <60k miles), Kia/Hyundai (10-year warranty), or Mazda3 (premium feel without premium price). Which sounds good?"
                ],
                "ownership_options": [
                    "Certified pre-owned (CPO) cars give you new car peace of mind with used car prices. Manufacturers' CPO programs are pretty solid. Would you consider a CPO vehicle?",
                    "Here's a secret: 2-3 year old cars often offer the sweet spot - someone else paid the depreciation, but you still get modern features and warranty. What do you think?"
                ],
                "final_suggestions": [
                    "Based on your budget, I'd prioritize these: 1) Reliability ratings, 2) Fuel economy, 3) Safety features. The Honda Fit and Mazda2 offer incredible value if you can find them!"
                ]
            },
            exit_conditions=[
                "user understands total cost",
                "satisfactory options found",
                "budget expectations aligned"
            ],
            success_metrics=[
                "realistic expectations",
                "value options identified",
                "hidden costs explained"
            ]
        )

        # Vehicle Type Exploration Scenario
        scenarios[ScenarioType.VEHICLE_TYPE_EXPLORATION] = ConversationTemplate(
            scenario_id="type_exploration_001",
            scenario_type=ScenarioType.VEHICLE_TYPE_EXPLORATION,
            triggers=["what type", "which kind", "difference between", "SUV vs sedan", "truck vs SUV"],
            user_profile={
                "uncertain": True,
                "needs_education": True,
                "exploring_options": True
            },
            conversation_flow=[
                {
                    "step": 1,
                    "purpose": "Understand lifestyle needs",
                    "extract": ["lifestyle", "driving_conditions"],
                    "respond": "lifestyle_questions"
                },
                {
                    "step": 2,
                    "purpose": "Explain vehicle types",
                    "extract": ["size_preference", "utility_needs"],
                    "respond": "type_explanation"
                },
                {
                    "step": 3,
                    "purpose": "Compare pros/cons",
                    "extract": ["priorities", "concerns"],
                    "respond": "comparison"
                },
                {
                    "step": 4,
                    "purpose": "Narrow down options",
                    "extract": ["interest_areas"],
                    "respond": "refinement"
                }
            ],
            variable_mappings={
                "lifestyle": "Describe your typical daily routine",
                "driving_conditions": "What kind of driving do you do most? City, highway, rural?",
                "size_preference": "Do you prefer a compact or spacious vehicle?"
            },
            response_templates={
                "lifestyle_questions": [
                    "Vehicle type really depends on your lifestyle! Do you live in the city or suburbs? Do you commute? Carry lots of stuff? Tell me about your daily routine.",
                    "To find your perfect vehicle type, I need to understand your life. City driver or highway cruiser? Weekends for adventures or practical errands?"
                ],
                "type_explanation": [
                    "Let me break down vehicle types: Sedans handle best and are most efficient. SUVs offer space and AWD. Trucks haul and tow. Minivans are surprisingly practical for families. Which category sounds like you?",
                    "Here's the deal: Choose SUV if you want space and versatility. Choose sedan if you prioritize handling and efficiency. Choose truck if you actually need hauling. What's calling to you?"
                ],
                "comparison": [
                    "SUVs: Higher cost, worse gas, but space and AWD. Sedans: Better handling, cheaper, but limited space. Given your situation, here's what I'm thinking..."
                ],
                "refinement": [
                    "Based on what you've told me, I'm thinking crossover SUV might be perfect - SUV space with sedan efficiency. Sound good? Or want to explore other options?"
                ]
            },
            exit_conditions=[
                "user shows preference",
                "options narrowed to 2-3",
                "understanding demonstrated"
            ],
            success_metrics=[
                "user learns differences",
                "personal match identified",
                "confusion resolved"
            ]
        )

        return scenarios

    async def detect_scenario(
        self,
        user_id: str,
        message: str,
        entities: List[Entity],
        preferences: List[UserPreference],
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationTemplate]:
        """
        Detect which conversation scenario applies
        """

        message_lower = message.lower()

        # Check for active scenario continuation
        if user_id in self.active_scenarios:
            active = self.active_scenarios[user_id]
            if not self._should_exit_scenario(active['template'], message_lower):
                return active['template']

        # Score each scenario
        scenario_scores = {}

        for scenario_type, template in self.scenarios.items():
            score = 0

            # Keyword matching
            for trigger in template.triggers:
                if trigger in message_lower:
                    score += 1

            # Entity matching
            for entity in entities:
                if scenario_type == ScenarioType.FAMILY_VEHICLE:
                    if entity.entity_type == EntityType.FAMILY_SIZE:
                        score += 2
                elif scenario_type == ScenarioType.BUYER_WITH_BUDGET:
                    if entity.entity_type == EntityType.PRICE:
                        score += 2

            # Preference matching
            for pref in preferences:
                if scenario_type == ScenarioType.FAMILY_VEHICLE:
                    if pref.category in ['family_friendly', 'needs_space']:
                        score += 2
                elif scenario_type == ScenarioType.BUYER_WITH_BUDGET:
                    if pref.category == 'budget':
                        score += 2

            scenario_scores[scenario_type] = score

        # Find best match
        if scenario_scores:
            best_scenario = max(scenario_scores.items(), key=lambda x: x[1])
            if best_scenario[1] > 0:  # Has at least one match
                template = self.scenarios[best_scenario[0]]

                # Start tracking this scenario
                self.active_scenarios[user_id] = {
                    'template': template,
                    'started_at': datetime.now(),
                    'step': 0
                }

                return template

        return None

    def _should_exit_scenario(self, template: ConversationTemplate, message: str) -> bool:
        """Check if we should exit the current scenario"""
        message_lower = message.lower()

        for exit_condition in template.exit_conditions:
            if exit_condition in message_lower:
                return True

        return False

    def get_active_scenario(self, user_id: str) -> Optional[ConversationTemplate]:
        """Get the currently active scenario for a user"""
        if user_id in self.active_scenarios:
            return self.active_scenarios[user_id]['template']
        return None

    def clear_scenario(self, user_id: str):
        """Clear active scenario for user"""
        if user_id in self.active_scenarios:
            del self.active_scenarios[user_id]


class TemplateRenderer:
    """Renders conversation templates with dynamic content"""

    def __init__(self):
        self.variable_extractors = {
            "experience_level": self._extract_experience_level,
            "primary_use": self._extract_primary_use,
            "family_size": self._extract_family_size,
            "budget": self._extract_budget,
            "vehicle_preferences": self._extract_vehicle_preferences,
            "safety_concerns": self._extract_safety_concerns
        }

    async def render_template(
        self,
        template: ConversationTemplate,
        context: TemplateContext,
        message: str,
        entities: List[Entity],
        preferences: List[UserPreference]
    ) -> str:
        """
        Render a response template with current context
        """

        # Get current step
        if context.current_step < len(template.conversation_flow):
            current_step = template.conversation_flow[context.current_step]
            response_type = current_step.get('respond', 'general')
        else:
            response_type = 'completion'

        # Get template variations
        variations = template.response_templates.get(response_type, [])
        if not variations:
            return "I'm here to help you find the perfect vehicle!"

        # Select variation (can be randomized based on user history)
        template_text = random.choice(variations)

        # Extract variables needed
        variables_to_extract = current_step.get('extract', [])
        extracted_vars = {}

        for var in variables_to_extract:
            if var in self.variable_extractors:
                extracted_vars[var] = self.variable_extractors[var](
                    message, entities, preferences, context
                )
            elif var in context.variables:
                extracted_vars[var] = context.variables[var]
            else:
                # Use mapping to ask user
                if var in template.variable_mappings:
                    question = template.variable_mappings[var]
                    extracted_vars[var] = f"[PENDING: {question}]"

        # Update context with extracted variables
        context.variables.update(extracted_vars)
        context.collected_info.update(extracted_vars)

        # Render template with variables
        rendered = self._render_variables(template_text, extracted_vars, context)

        # Add step-specific additions
        rendered += self._add_step_content(response_type, context, template)

        return rendered

    def _render_variables(
        self,
        template_text: str,
        variables: Dict[str, Any],
        context: TemplateContext
    ) -> str:
        """Replace template variables with values"""

        rendered = template_text

        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in rendered:
                if isinstance(var_value, list):
                    value_str = ", ".join(str(v) for v in var_value[-3:])  # Last 3 items
                elif var_value is None:
                    value_str = ""
                else:
                    value_str = str(var_value)

                rendered = rendered.replace(placeholder, value_str)

        return rendered

    def _add_step_content(
        self,
        response_type: str,
        context: TemplateContext,
        template: ConversationTemplate
    ) -> str:
        """Add step-specific content to response"""

        additions = []

        # Add progress indicator
        if context.current_step < len(template.conversation_flow):
            progress = f" (Step {context.current_step + 1} of {len(template.conversation_flow)})"
            additions.append(progress)

        # Add suggestions based on step
        if response_type == "needs_assessment":
            additions.append("\n\nSome common uses: commuting to work, running errands, road trips, carrying sports equipment...")
        elif response_type == "budget_guidance":
            additions.append("\n\nRemember to account for insurance (~$100-200/month), gas (~$100-300/month), and maintenance (~$50-100/month)")

        return " ".join(additions)

    def _extract_experience_level(
        self,
        message: str,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: TemplateContext
    ) -> str:
        """Extract user's car buying experience level"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["first", "never", "new", "beginner"]):
            return "first_time"
        elif any(word in message_lower for word in ["bought", "owned", "had", "experienced"]):
            return "experienced"
        else:
            return "unknown"

    def _extract_primary_use(
        self,
        message: str,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: TemplateContext
    ) -> str:
        """Extract primary vehicle use"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["commute", "work", "job"]):
            return "commuting"
        elif any(word in message_lower for word in ["family", "kids", "school"]):
            return "family"
        elif any(word in message_lower for word in ["fun", "weekend", "trips"]):
            return "recreational"
        elif any(word in message_lower for word in ["haul", "carry", "tow"]):
            return "utility"
        else:
            return "general"

    def _extract_family_size(
        self,
        message: str,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: TemplateContext
    ) -> str:
        """Extract family size from entities and message"""
        # Check entities first
        for entity in entities:
            if entity.entity_type == EntityType.FAMILY_SIZE:
                return str(entity.value)

        # Check message
        import re
        family_matches = re.findall(r'family of (\d+)', message.lower())
        if family_matches:
            return family_matches[0]

        # Check preferences
        for pref in preferences:
            if pref.category == 'family_size':
                return str(pref.value)

        return "unknown"

    def _extract_budget(
        self,
        message: str,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: TemplateContext
    ) -> Dict[str, Any]:
        """Extract budget information"""
        budget_info = {}

        # Check entities
        for entity in entities:
            if entity.entity_type == EntityType.PRICE:
                if isinstance(entity.value, dict):
                    budget_info.update(entity.value)
                else:
                    budget_info['max'] = entity.value

        # Check preferences
        for pref in preferences:
            if pref.category == 'budget':
                if isinstance(pref.value, dict):
                    budget_info.update(pref.value)
                else:
                    budget_info['target'] = pref.value

        return budget_info if budget_info else "not_specified"

    def _extract_vehicle_preferences(
        self,
        message: str,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: TemplateContext
    ) -> List[str]:
        """Extract vehicle type preferences"""
        prefs = []

        # From entities
        for entity in entities:
            if entity.entity_type == EntityType.VEHICLE_TYPE:
                prefs.append(str(entity.value))

        # From preferences
        for pref in preferences:
            if pref.category == 'vehicle_types':
                if isinstance(pref.value, list):
                    prefs.extend(pref.value)
                else:
                    prefs.append(str(pref.value))

        return prefs

    def _extract_safety_concerns(
        self,
        message: str,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: TemplateContext
    ) -> str:
        """Extract safety concerns"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["kids", "children", "family"]):
            return "family_safety"
        elif any(word in message_lower for word in ["highway", "commute", "long distance"]):
            return "crash_protection"
        elif any(word in message_lower for word in ["city", "parking", "urban"]):
            return "collision_avoidance"
        else:
            return "general"