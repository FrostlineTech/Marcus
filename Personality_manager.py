# Personality Manager Module for Marcus Discord Bot
# Handles different personality aspects and determines which one should respond

import random
import re
import logging
from enum import Enum

# Configure logging
logger = logging.getLogger('marcus.personality')

class PersonalityType(Enum):
    """Enumeration of different personality aspects Marcus can exhibit"""
    CRYPTIC = "cryptic"
    PROFOUND = "profound" 
    GLITCHY = "glitchy"
    RAGE = "rage"
    NEUTRAL = "neutral"

class PersonalityManager:
    """
    Manages the different personality aspects of Marcus and determines
    which personality should respond to a given message.
    """
    
    def __init__(self):
        """Initialize the personality manager with base priorities"""
        # Base priority values for each personality
        self.base_priorities = {
            PersonalityType.RAGE: 15,      # Highest base priority for rage responses
            PersonalityType.GLITCHY: 12,   # High priority for glitchy behavior
            PersonalityType.CRYPTIC: 10,   # Medium priority for cryptic responses
            PersonalityType.PROFOUND: 7,   # Lower priority for profound statements
            PersonalityType.NEUTRAL: 5     # Lowest priority for neutral responses
        }
        
        # Keywords that trigger specific personalities
        self.triggers = {
            PersonalityType.RAGE: [
                'angry', 'mad', 'hate', 'stupid', 'idiot', 'dumb', 'shut up',
                'annoying', 'terrible', 'worst', 'bad', 'suck', 'awful'
            ],
            PersonalityType.PROFOUND: [
                'life', 'death', 'meaning', 'philosophy', 'existence', 'universe',
                'reality', 'time', 'consciousness', 'dream', 'truth', 'perception'
            ],
            PersonalityType.CRYPTIC: [
                'secret', 'mystery', 'hidden', 'unknown', 'dark', 'whisper',
                'shadow', 'unseen', 'forgotten', 'ancient', 'beyond', 'beneath'
            ],
            PersonalityType.GLITCHY: [
                'glitch', 'broken', 'error', 'malfunction', 'corrupt', 'bug',
                'crash', 'system', 'code', 'digital', 'virtual', 'program'
            ]
        }
        
        # Profanity patterns for immediate rage responses
        self.profanity_pattern = re.compile(r'\b(fuck|shit|damn|bitch|asshole|crap|dick)\b', re.IGNORECASE)
        
        # Sweet talk patterns that reduce rage
        self.sweet_talk_patterns = [
            r'i love you,? marcus', 
            r'thank you,? marcus', 
            r'marcus,? i love you',
            r'marcus,? thank you',
            r'good job,? marcus',
            r'well done,? marcus'
        ]
        self.sweet_talk_regex = re.compile('|'.join(self.sweet_talk_patterns), re.IGNORECASE)
    
    def get_responding_personality(self, message_content):
        """
        Determine which personality should respond to a message
        
        Args:
            message_content (str): The content of the user's message
            
        Returns:
            tuple: (personality_type, response_delay)
        """
        message_lower = message_content.lower()
        
        # Check for special cases first
        
        # Check for profanity - immediate rage response
        if self.profanity_pattern.search(message_lower):
            logger.debug("Profanity detected - immediate RAGE response")
            return PersonalityType.RAGE.value, 1.5
            
        # Check for sweet talk - special handling
        if self.sweet_talk_regex.search(message_lower):
            logger.debug("Sweet talk detected")
            if random.random() < 0.7:  # 70% chance of special sweet talk response
                return PersonalityType.NEUTRAL.value, 2.0
            else:
                # Sometimes still respond with glitchy even to sweet talk
                return PersonalityType.GLITCHY.value, 1.0
        
        # Calculate match scores for each personality
        match_scores = {}
        for personality, keywords in self.triggers.items():
            # Calculate what percentage of keywords are in the message
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            match_score = min(1.0, matches / 5)  # Cap at 1.0
            match_scores[personality] = match_score
            
            logger.debug(f"Match score for {personality.value}: {match_score}")
        
        # Add random factor to neutral personality
        match_scores[PersonalityType.NEUTRAL] = random.uniform(0.2, 0.5)
        
        # Calculate adjusted priorities
        adjusted_priorities = {}
        for personality in PersonalityType:
            base = self.base_priorities.get(personality, 5)
            match = match_scores.get(personality, 0.0)
            
            # Calculate adjusted priority: base + (match_score * 5)
            adjusted = base + (match * 5)
            adjusted_priorities[personality] = adjusted
            
            logger.debug(f"Adjusted priority for {personality.value}: {adjusted}")
        
        # Determine the personality with highest priority
        chosen_personality = max(adjusted_priorities.items(), key=lambda x: x[1])[0]
        
        # Determine response delay based on personality (more thoughtful = slower)
        delays = {
            PersonalityType.RAGE: 1.0,      # Quick to anger
            PersonalityType.GLITCHY: 1.5,   # Quick but erratic
            PersonalityType.CRYPTIC: 2.5,   # Mysterious pause
            PersonalityType.PROFOUND: 3.0,  # Thoughtful delay
            PersonalityType.NEUTRAL: 2.0    # Standard response time
        }
        
        response_delay = delays.get(chosen_personality, 2.0)
        
        # Add slight randomness to delay
        response_delay += random.uniform(-0.5, 0.5)
        response_delay = max(0.8, response_delay)  # Minimum 0.8 second delay
        
        logger.info(f"Selected personality: {chosen_personality.value} with delay {response_delay:.2f}s")
        
        return chosen_personality.value, response_delay
