import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
import asyncio

class EmotionSystem(commands.Cog):
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.db_pool = db_pool
        self.base_mood = "neutral"
        self.current_mood = "neutral"
        self.mood_influences = []
        self.mood_intensity = 0  # Overall emotional intensity
        self.mood_decay_task.start()
        
        # Core emotion types
        self.emotion_types = {
            "joy": {"compatible": ["friendly", "happy", "energetic"], 
                   "incompatible": ["sad", "dreadful", "ominous"]},
            "anger": {"compatible": ["chaotic", "glitchy", "sarcastic"], 
                     "incompatible": ["friendly", "happy", "mysterious"]},
            "fear": {"compatible": ["paranoid", "ominous", "dreadful"], 
                    "incompatible": ["happy", "friendly"]},
            "sadness": {"compatible": ["existential", "sad", "mysterious"], 
                       "incompatible": ["happy", "chaotic", "energetic"]},
            "disgust": {"compatible": ["sarcastic", "glitchy"], 
                       "incompatible": ["friendly", "happy"]},
            "surprise": {"compatible": ["chaotic", "glitchy", "energetic"], 
                        "incompatible": ["sad", "dreadful"]}
        }
        
        # Personality traits that persist
        self.core_traits = {
            "cryptic": 0.8,  # Very cryptic
            "weird": 0.7,    # Quite weird
            "unstable": 0.6, # Somewhat unstable
            "curious": 0.5,  # Moderately curious
            "helpful": 0.3   # A little helpful
        }
    
    def cog_unload(self):
        self.mood_decay_task.cancel()
        
    @tasks.loop(minutes=15)
    async def mood_decay_task(self):
        """Gradually return to baseline emotional state"""
        if not self.mood_influences:
            return
            
        # Remove old influences (older than 2 hours)
        now = datetime.utcnow()
        self.mood_influences = [
            influence for influence in self.mood_influences 
            if now - influence["timestamp"] < timedelta(hours=2)
        ]
        
        # Recalculate current mood based on remaining influences
        await self.recalculate_mood()
    
    @mood_decay_task.before_loop
    async def before_mood_decay(self):
        await self.bot.wait_until_ready()
    
    async def apply_mood_influence(self, influence_type, intensity, user_id=None):
        """Apply a temporary mood shift"""
        # Cap intensity between 0.1 and 1.0
        intensity = max(0.1, min(intensity, 1.0))
        
        self.mood_influences.append({
            "type": influence_type,
            "intensity": intensity,
            "timestamp": datetime.utcnow(),
            "user_id": user_id
        })
        
        await self.recalculate_mood()
        return self.current_mood, self.mood_intensity
    
    async def recalculate_mood(self):
        """Recalculate current mood based on influences"""
        if not self.mood_influences:
            self.current_mood = self.base_mood
            self.mood_intensity = 0
            return
            
        # Calculate the strongest influence
        strongest = max(self.mood_influences, key=lambda x: x["intensity"])
        
        # Find compatible moods for this emotion
        if strongest["type"] in self.emotion_types:
            compatible_moods = self.emotion_types[strongest["type"]]["compatible"]
            self.current_mood = random.choice(compatible_moods)
        else:
            self.current_mood = self.base_mood
            
        # Calculate overall intensity (average of all active influences)
        self.mood_intensity = sum(infl["intensity"] for infl in self.mood_influences) / len(self.mood_influences)
    
    async def get_user_emotion(self, user_id):
        """Get the emotional state specifically for a user interaction"""
        # Get rage level
        rage_cog = self.bot.get_cog("RageEscalation")
        rage_level = 0
        
        if rage_cog:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT rage_level FROM marcus_rage WHERE user_id = $1", user_id
                )
                rage_level = row["rage_level"] if row else 0
        
        # User-specific influences
        user_influences = [
            infl for infl in self.mood_influences 
            if infl.get("user_id") == user_id
        ]
        
        # Default mood state
        user_mood = self.current_mood
        user_intensity = self.mood_intensity
        
        # Adjust based on rage level
        if rage_level >= 4:
            return "dreadful", 0.9  # High rage overrides other emotions
        elif rage_level >= 3:
            return "ominous", 0.7
        elif rage_level >= 2:
            return "sarcastic", 0.5
        elif user_influences:
            # Use the most recent user-specific influence
            latest = max(user_influences, key=lambda x: x["timestamp"])
            if latest["type"] in self.emotion_types:
                compatible_moods = self.emotion_types[latest["type"]]["compatible"]
                user_mood = random.choice(compatible_moods)
                user_intensity = latest["intensity"]
        
        return user_mood, user_intensity
    
    async def evolve_personality(self):
        """Slightly evolve personality traits over time"""
        for trait in self.core_traits:
            # Small random adjustment (-0.1 to +0.1)
            adjustment = (random.random() - 0.5) / 5
            self.core_traits[trait] = max(0.1, min(0.9, self.core_traits[trait] + adjustment))
        
        # Slightly shift base mood occasionally (10% chance)
        if random.random() < 0.1:
            all_moods = []
            for emotion in self.emotion_types.values():
                all_moods.extend(emotion["compatible"])
            self.base_mood = random.choice(all_moods)
        
        print(f"[EMOTION] Personality evolved: {self.core_traits}")
        print(f"[EMOTION] Base mood shifted to: {self.base_mood}")
        
    def get_personality_trait_influence(self):
        """Get a dictionary of current personality trait influence"""
        return self.core_traits
    
    async def log_emotional_event(self, event_type, user_id, content=None, intensity=0.5):
        """Log an emotional event for future reference"""
        try:
            async with self.db_pool.acquire() as conn:
                # Check if the table exists and what columns it has
                table_exists = await conn.fetchval(
                    """SELECT EXISTS (SELECT FROM information_schema.tables 
                       WHERE table_name = 'marcus_emotional_events')"""
                )
                
                if not table_exists:
                    # Create the table if it doesn't exist
                    await conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS marcus_emotional_events (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            event_type VARCHAR(50) NOT NULL,
                            description TEXT,
                            intensity FLOAT NOT NULL,
                            timestamp TIMESTAMP NOT NULL
                        )
                        """
                    )
                    print("[EMOTION] Created marcus_emotional_events table")
                
                # Insert the emotional event
                await conn.execute(
                    """
                    INSERT INTO marcus_emotional_events (user_id, event_type, description, intensity, timestamp)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    user_id, event_type, content, intensity, datetime.utcnow()
                )
        except Exception as e:
            print(f"[EMOTION] Error logging emotional event: {e}")
            # Don't raise the exception - we don't want voice functionality to break
            # because of a database issue

async def setup(bot, db_pool):
    await bot.add_cog(EmotionSystem(bot, db_pool))
