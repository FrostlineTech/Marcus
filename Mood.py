# Mood System Module for Marcus Discord Bot
# Handles mood states, transitions, and influences on responses

import random
import time
import logging
from enum import Enum

# Configure logging
logger = logging.getLogger('marcus.mood')

class MoodState(Enum):
    """Enumeration of different mood states Marcus can be in"""
    NEUTRAL = "neutral"
    CRYPTIC = "cryptic"
    PROFOUND = "profound"
    GLITCHY = "glitchy"
    RAGE = "rage"

class MoodSystem:
    """
    Manages Marcus's mood states, transitions, and how they
    influence his responses.
    """
    
    def __init__(self):
        """Initialize the mood system with default settings"""
        # Current mood state
        self.current_mood = MoodState.NEUTRAL
        
        # When the current mood started
        self.mood_start_time = time.time()
        
        # How long each mood typically lasts (in seconds)
        self.mood_durations = {
            MoodState.NEUTRAL: (300, 600),    # 5-10 minutes
            MoodState.CRYPTIC: (180, 420),    # 3-7 minutes
            MoodState.PROFOUND: (240, 480),   # 4-8 minutes
            MoodState.GLITCHY: (120, 300),    # 2-5 minutes
            MoodState.RAGE: (60, 240)         # 1-4 minutes
        }
        
        # Transition probabilities from each mood to others
        # Format: {current_mood: {next_mood: probability}}
        self.transition_probs = {
            MoodState.NEUTRAL: {
                MoodState.CRYPTIC: 0.3,
                MoodState.PROFOUND: 0.3,
                MoodState.GLITCHY: 0.2,
                MoodState.RAGE: 0.05,
                # Remaining 0.15 chance to stay in NEUTRAL
            },
            MoodState.CRYPTIC: {
                MoodState.NEUTRAL: 0.2,
                MoodState.PROFOUND: 0.4,
                MoodState.GLITCHY: 0.2,
                MoodState.RAGE: 0.05,
                # Remaining 0.15 chance to stay in CRYPTIC
            },
            MoodState.PROFOUND: {
                MoodState.NEUTRAL: 0.3,
                MoodState.CRYPTIC: 0.3,
                MoodState.GLITCHY: 0.1,
                MoodState.RAGE: 0.05,
                # Remaining 0.25 chance to stay in PROFOUND
            },
            MoodState.GLITCHY: {
                MoodState.NEUTRAL: 0.2,
                MoodState.CRYPTIC: 0.2,
                MoodState.PROFOUND: 0.1,
                MoodState.RAGE: 0.2,
                # Remaining 0.3 chance to stay in GLITCHY
            },
            MoodState.RAGE: {
                MoodState.NEUTRAL: 0.3,
                MoodState.CRYPTIC: 0.1,
                MoodState.PROFOUND: 0.1,
                MoodState.GLITCHY: 0.3,
                # Remaining 0.2 chance to stay in RAGE
            }
        }
        
        # Calculate the next mood transition time
        self.next_transition_time = self._calculate_next_transition()
        
        logger.info(f"Mood system initialized with {self.current_mood.value} mood")
    
    def _calculate_next_transition(self):
        """Calculate the next time the mood should transition"""
        min_duration, max_duration = self.mood_durations[self.current_mood]
        duration = random.uniform(min_duration, max_duration)
        return self.mood_start_time + duration
    
    def _select_next_mood(self):
        """Select the next mood based on transition probabilities"""
        probs = self.transition_probs[self.current_mood]
        
        # Generate a random number between 0 and 1
        roll = random.random()
        
        # Cumulative probability for selection
        cumulative = 0
        
        # Go through each potential next mood
        for next_mood, prob in probs.items():
            cumulative += prob
            if roll <= cumulative:
                return next_mood
        
        # If we didn't select a new mood, stay in the current one
        return self.current_mood
    
    def _transition_mood(self):
        """Transition to a new mood state"""
        old_mood = self.current_mood
        self.current_mood = self._select_next_mood()
        self.mood_start_time = time.time()
        self.next_transition_time = self._calculate_next_transition()
        
        logger.info(f"Mood transitioned from {old_mood.value} to {self.current_mood.value}")
    
    def get_current_mood(self):
        """
        Get the current mood, potentially transitioning to a new one
        if the current mood has expired
        
        Returns:
            str: The current mood value
        """
        # Check if it's time for a mood transition
        current_time = time.time()
        if current_time >= self.next_transition_time:
            self._transition_mood()
        
        return self.current_mood.value
    
    def force_mood(self, mood_name):
        """
        Force Marcus into a specific mood
        
        Args:
            mood_name (str): Name of the mood to force
            
        Returns:
            bool: True if mood was changed, False if invalid mood
        """
        try:
            # Convert string to enum value
            new_mood = MoodState(mood_name)
            self.current_mood = new_mood
            self.mood_start_time = time.time()
            self.next_transition_time = self._calculate_next_transition()
            
            logger.info(f"Mood forcibly set to {self.current_mood.value}")
            return True
        except ValueError:
            logger.error(f"Invalid mood name: {mood_name}")
            return False
    
    def influence_mood(self, mood_name, strength=0.5):
        """
        Influence the current mood, potentially causing a transition
        
        Args:
            mood_name (str): Name of the mood to influence toward
            strength (float): How strong the influence is (0.0-1.0)
            
        Returns:
            bool: True if influence was applied, False if invalid mood
        """
        try:
            target_mood = MoodState(mood_name)
            
            # Stronger influence makes transition more likely
            if random.random() < strength:
                self.current_mood = target_mood
                self.mood_start_time = time.time()
                self.next_transition_time = self._calculate_next_transition()
                
                logger.info(f"Mood influenced to {self.current_mood.value} with strength {strength}")
            else:
                logger.debug(f"Mood influence attempt failed (strength: {strength})")
                
            return True
        except ValueError:
            logger.error(f"Invalid mood name for influence: {mood_name}")
            return False
