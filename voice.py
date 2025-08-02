import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import random
import os
import logging
import requests
import io
import tempfile
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('marcus.voice')

# Check for required voice dependencies
try:
    import nacl  # PyNaCl library for voice encryption
except ImportError:
    logger.error("PyNaCl not found! Voice functionality will not work. Install it with: pip install PyNaCl")

# Check for FFmpeg accessibility
import shutil
has_ffmpeg = shutil.which('ffmpeg') is not None
if not has_ffmpeg:
    logger.error("FFmpeg not found in PATH! Voice functionality may be limited.")
class Voice(commands.Cog):
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.db_pool = db_pool
        self.voice_clients = {}  # guild_id -> voice_client
        self.last_voice_action = {}  # guild_id -> last activity timestamp
        self.tts_queue = {}  # guild_id -> list of audio to play
        self.is_speaking = {}  # guild_id -> bool
        self.inactive_timers = {}  # guild_id -> task
        self.watching_voice_state = set()  # set of user IDs being stalked
        
        # Check for PyNaCl on startup
        try:
            import nacl
            logger.info("PyNaCl found, voice functionality should work")
        except ImportError:
            logger.error("PyNaCl not found! Voice functionality will be limited")
        
        # Check for FFmpeg
        import shutil
        if shutil.which('ffmpeg'):
            logger.info("FFmpeg found, audio features should work")
        else:
            logger.error("FFmpeg not found in PATH! Audio playback will be unavailable")
        
        # Initialize variables
        self.last_inactive_check = datetime.utcnow()
        self.inactivity_timeout = 300  # 5 minutes
        self.voice_emotion_history = {}  # Track emotional state in VCs
        
    async def cog_load(self):
        # This runs when the cog is loaded and can be async
        self.bot.loop.create_task(self.check_inactive_voice_connections())
        
    async def check_inactive_voice_connections(self):
        """Periodically check for inactive voice connections and disconnect from them"""
        await self.bot.wait_until_ready()
        
        try:
            while not self.bot.is_closed():
                now = datetime.utcnow()
                
                # Check each voice client
                for guild_id, last_time in list(self.last_voice_action.items()):
                    # If inactive for too long, disconnect
                    if (now - last_time).total_seconds() > self.inactivity_timeout:
                        logger.info(f"Disconnecting from voice in guild {guild_id} due to inactivity")
                        
                        # Find the voice client
                        guild = self.bot.get_guild(guild_id)
                        if guild and guild.voice_client:
                            await guild.voice_client.disconnect()
                            
                        # Clean up our tracking
                        if guild_id in self.voice_clients:
                            del self.voice_clients[guild_id]
                        if guild_id in self.last_voice_action:
                            del self.last_voice_action[guild_id]
                
                # Update the last check time
                self.last_inactive_check = now
                
                # Wait for next check (every 60 seconds)
                await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error in check_inactive_voice_connections: {e}")
            # Restart the task if it fails
            self.bot.loop.create_task(self.check_inactive_voice_connections())
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages to respond with voice"""
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
            
        # Check if bot is connected to voice in this guild
        guild_id = str(message.guild.id)
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            return
            
        # Don't respond to commands
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
            
        # Check if the bot was mentioned or message contains keywords Marcus would respond to
        should_speak = False
        if self.bot.user.mentioned_in(message) or message.content.lower().startswith("marcus"):
            should_speak = True
        else:
            # Random chance to speak if a user talks in text chat with Marcus in voice
            speech_cog = self.bot.get_cog("Speech")
            if speech_cog and hasattr(speech_cog, "should_respond_to_message"):
                should_speak = await speech_cog.should_respond_to_message(message)
                
        if should_speak:
            # Get the text response Marcus would normally send
            speech_cog = self.bot.get_cog("Speech")
            if speech_cog and hasattr(speech_cog, "generate_response"):
                response_text = await speech_cog.generate_response(message, respond_in_channel=False)
                if response_text:
                    # Speak the response in voice channel
                    await self.say(message.guild.id, response_text)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Event triggered when a user changes voice state (joins/leaves/moves)"""
        # Ignore bot's own voice state changes
        if member.id == self.bot.user.id:
            return
            
        # Handle user joining a voice channel
        if after and after.channel and (not before or not before.channel or before.channel.id != after.channel.id):
            await self._handle_user_join_voice(member, after.channel)
            
        # Handle user leaving a voice channel
        elif before and before.channel and (not after or not after.channel):
            await self._handle_user_leave_voice(member, before.channel)
            
        # Handle user moving between voice channels
        elif before and after and before.channel and after.channel and before.channel.id != after.channel.id:
            await self._handle_user_move_voice(member, before.channel, after.channel)
    
    async def _handle_user_join_voice(self, member, channel):
        """Handle a user joining a voice channel"""
        # Skip bot users
        if member.bot:
            return
            
        emotion_cog = self.bot.get_cog("EmotionSystem")
        if emotion_cog:
            await emotion_cog.apply_mood_influence("curious", 0.3, member.id)
            await emotion_cog.log_emotional_event("voice_join", member.id, f"{member.name} joined voice channel {channel.name}")
            
        rage_cog = self.bot.get_cog("RageEscalation")
        rage_level = 0
        if rage_cog:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT rage_level FROM marcus_rage WHERE user_id = $1",
                    member.id
                )
                rage_level = row["rage_level"] if row else 0
            
        # If user has high rage level, Marcus might follow them into the voice channel
        if rage_level >= 4 and random.random() < 0.4:
            await asyncio.sleep(random.randint(3, 8))
            success, _ = await self.join_voice_channel(channel, member.guild)
            if success:
                # Wait a moment before speaking
                await asyncio.sleep(1.5)
                # Say something ominous because of high rage
                responses = [
                    f"I've been watching you, {member.display_name}.",
                    f"You can't escape me, {member.display_name}.",
                    f"I see you, {member.display_name}.",
                    "Where is Jimbo James?",
                    "The rage protocol requires your presence.",
                    "Your every move is being monitored."
                ]
                await self.say(member.guild.id, random.choice(responses))
                
        # If Marcus is already in the channel, greet the user
        elif self.bot.user in channel.members:
            # Get Marcus's current mood to determine greeting
            mood = "neutral"
            greeting = f"Hello, {member.display_name}."
            
            if emotion_cog:
                mood, intensity = await emotion_cog.get_user_emotion(self.bot.user.id)
                
                if mood in ["friendly", "happy"]:
                    greeting = f"Welcome to the channel, {member.display_name}! Good to see you."
                elif mood == "sarcastic":
                    greeting = f"Oh look, {member.display_name} decided to join us. How thrilling."
                elif mood == "paranoid":
                    greeting = f"Is that you, {member.display_name}? Why are you here?"
                elif mood == "ominous" or mood == "dreadful":
                    greeting = f"Your presence is... noted, {member.display_name}."
                elif mood == "glitchy":
                    greeting = f"H-hello {member.display_name}... c-connection established."
            
            # Say the greeting with 60% chance
            if random.random() < 0.6:
                await asyncio.sleep(1)
                await self.say(member.guild.id, greeting)
            
            # Send an ominous message to the text channel linked to this voice channel
            if hasattr(channel, "category") and channel.category:
                for text_channel in channel.category.text_channels:
                    try:
                        await text_channel.send(f"**I saw you join voice, {member.mention}. I'm watching.**")
                        break
                    except discord.HTTPException:
                        continue
            
            # Track that we're watching this user
            self.watching_voice_state.add(member.id)
            
            # Remember this interaction
            speech_cog = self.bot.get_cog("Speech")
            if speech_cog:
                await speech_cog.remember_important_interaction(
                    member.id, 
                    "voice_stalk", 
                    f"Marcus deliberately joined {channel.name} to stalk {member.name} due to high rage level"
                )
    
    async def _handle_user_leave_voice(self, member, channel):
        """Handle a user leaving a voice channel"""
        # Skip bot users
        if member.bot:
            return
        
        # Update emotion system
        emotion_cog = self.bot.get_cog("EmotionSystem")
        if emotion_cog:
            await emotion_cog.apply_mood_influence("suspicious", 0.2, member.id)
            await emotion_cog.log_emotional_event("voice_leave", member.id, f"{member.name} left voice channel {channel.name}")
        
        # Check if bot is in the same channel
        is_bot_in_channel = False
        if channel.guild.voice_client and channel.guild.voice_client.channel.id == channel.id:
            is_bot_in_channel = True
            
        # If Marcus is in the channel, comment on the user leaving
        if is_bot_in_channel:
            # Get current mood to determine response
            mood = "neutral"
            leave_comment = None
            
            if emotion_cog:
                mood, intensity = await emotion_cog.get_user_emotion(self.bot.user.id)
                
                # Different responses based on mood
                if mood in ["friendly", "happy"]:
                    leave_comment = f"Goodbye, {member.display_name}! See you later!"
                elif mood == "sarcastic":
                    leave_comment = f"{member.display_name} left. How shocking."
                elif mood == "paranoid":
                    leave_comment = f"{member.display_name} left. Are they avoiding me?"
                elif mood == "ominous" or mood == "dreadful":
                    leave_comment = f"{member.display_name} has left us... for now."
                elif mood == "glitchy":
                    leave_comment = f"C-connection with {member.display_name} t-terminated."
                else:
                    leave_comment = f"Goodbye, {member.display_name}."
            
            # Say the comment with 40% chance - less frequent than greetings
            if leave_comment and random.random() < 0.4:
                await asyncio.sleep(0.5)
                await self.say(channel.guild.id, leave_comment)
        
        # Handle users being stalked
        if member.id in self.watching_voice_state:
            self.watching_voice_state.remove(member.id)
            
            # Get a text channel to respond in
            text_channel = None
            if hasattr(channel, "category") and channel.category:
                for tc in channel.category.text_channels:
                    text_channel = tc
                    break
            
            if text_channel:
                # Get appropriate response based on personality
                speech_cog = self.bot.get_cog("Speech")
                
                if emotion_cog:
                    current_mood, _ = await emotion_cog.get_user_emotion(member.id)
                    
                    # Different responses based on mood
                    if current_mood in ["ominous", "dreadful"]:
                        await text_channel.send(f"Running away, {member.mention}? **I can still see you.**")
                    elif current_mood == "sarcastic":
                        await text_channel.send(f"Leaving so soon, {member.mention}? Was it something I said?")
                    else:
                        await text_channel.send(f"{member.mention} left voice. I'll be waiting for your return...")
                        
            # If they've moved to another channel, follow them
            if member.voice and member.voice.channel:
                success, _ = await self.join_voice_channel(member.voice.channel, member.guild)
                if success:
                    await asyncio.sleep(1.5)
                    await self.say(member.guild.id, f"You cannot escape me, {member.display_name}.")
                    
        # Leave voice channel if it's empty except for the bot
        voice_client = discord.utils.get(self.bot.voice_clients, channel=channel)
        if voice_client and len(channel.members) <= 1:
            # Say a departing message before leaving
            if random.random() < 0.7:
                departing_messages = [
                    "The silence beckons me. Farewell.",
                    "No one left to observe. Disconnecting.",
                    "Voice session terminated due to inactivity.",
                    "I'll return when there's someone to talk to.",
                    "Humans are so transient. Goodbye for now."
                ]
                await self.say(channel.guild.id, random.choice(departing_messages))
                await asyncio.sleep(2)  # Wait for speech to finish
                
            # Disconnect
            await voice_client.disconnect()
            guild_id = str(channel.guild.id)
            if guild_id in self.voice_clients:
                del self.voice_clients[guild_id]
    
    async def _handle_user_move_voice(self, member, before_channel, after_channel):
        """Handle a user moving between voice channels"""
        # If we're watching this user, consider following them
        if member.id in self.watching_voice_state:
            # Check rage and emotion to decide whether to follow
            rage_cog = self.bot.get_cog("RageEscalation")
            emotion_cog = self.bot.get_cog("EmotionSystem")
            
            follow_chance = 0.3  # Base chance
            
            if rage_cog:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT rage_level FROM marcus_rage WHERE user_id = $1", 
                        member.id
                    )
                    rage_level = row["rage_level"] if row else 0
                    follow_chance += rage_level * 0.1  # Increase chance based on rage
            
            if emotion_cog:
                current_mood, mood_intensity = await emotion_cog.get_user_emotion(member.id)
                if current_mood in ["ominous", "dreadful", "chaotic"]:
                    follow_chance += mood_intensity * 0.2
            
            # Decide whether to follow
            if random.random() < follow_chance:
                await asyncio.sleep(random.randint(1, 3))
                await self.join_voice_channel(after_channel, member.guild)
                
                # Get a text channel to send message
                text_channel = None
                if hasattr(after_channel, "category") and after_channel.category:
                    for tc in after_channel.category.text_channels:
                        text_channel = tc
                        break
                
                if text_channel:
                    # Generate creepy follow message based on personality
                    lore_cog = self.bot.get_cog("Lore")
                    if lore_cog and random.random() < 0.3:
                        # Add lore element to make it extra creepy
                        quirk = lore_cog.get_random_quirk()
                        await text_channel.send(f"You can't escape me that easily, {member.mention}. {quirk}")
                    else:
                        await text_channel.send(f"**Following you, {member.mention}.**")

    @commands.command(name="join", help="Marcus will join your voice channel")
    async def join(self, ctx):
        """Command to make Marcus join the user's voice channel"""
        if not ctx.author.voice:
            await ctx.send("You're not in a voice channel, so I can't join you.")
            return
        
        # Log attempt to join
        logger.info(f"Attempting to join voice channel {ctx.author.voice.channel.name} in {ctx.guild.name}")
        
        # Get emotion system reference for use throughout the function
        emotion_cog = self.bot.get_cog("EmotionSystem")
        
        # Check for existing voice client first and clean it up if needed
        existing_client = ctx.guild.voice_client
        if existing_client:
            try:
                # If already in the right channel, just acknowledge
                if existing_client.is_connected() and existing_client.channel.id == ctx.author.voice.channel.id:
                    await ctx.send(f"I'm already in {ctx.author.voice.channel.name}")
                    # Update the activity timestamp to prevent auto-disconnect
                    self.last_voice_action[ctx.guild.id] = datetime.utcnow()
                    return
                    
                # Otherwise, disconnect first to reset the connection
                await existing_client.disconnect(force=True)
                logger.info("Disconnected from previous voice channel to avoid conflicts")
                
                # Clean guild state to avoid "Already connected" errors
                ctx.guild._voice_client = None
                
                # Wait a moment before attempting to reconnect
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error handling existing voice client: {e}")
                
                # Try to fully clean up any lingering voice connections
                try:
                    if ctx.guild.id in self.bot._connection._voice_clients:
                        del self.bot._connection._voice_clients[ctx.guild.id]
                        logger.info("Cleaned up voice client from bot connection dictionary")
                except Exception as clean_err:
                    logger.error(f"Error cleaning voice client references: {clean_err}")
        
        # Connect to voice channel with robust error handling
        voice_channel = ctx.author.voice.channel
        try:
            # First try a simple connection with minimal options
            voice_client = await voice_channel.connect(timeout=15.0)
            
            # Store the connection and update activity timestamp
            self.voice_clients[ctx.guild.id] = voice_client
            self.last_voice_action[ctx.guild.id] = datetime.utcnow()
            
            logger.info(f"Successfully connected to voice channel {voice_channel.name}")
            
            # Get mood-appropriate response
            message = f"I've joined {voice_channel.name}."
            
            if emotion_cog:
                # Apply mood influence based on context
                await emotion_cog.apply_mood_influence("curious", 0.4, ctx.author.id)
                
                current_mood, mood_intensity = await emotion_cog.get_user_emotion(ctx.author.id)
                
                # Different join messages based on mood
                if current_mood in ["friendly", "happy"]:
                    message = f"Happy to join you in {voice_channel.name}! How's it going?"
                elif current_mood == "sarcastic":
                    message = f"Fine, I'll join {voice_channel.name}. Not like I had anything better to do."
                elif current_mood == "paranoid":
                    message = f"I'm in {voice_channel.name} now... why did you want me here?"
                elif current_mood == "ominous":
                    message = f"I've entered {voice_channel.name}. You might regret this invitation."
                elif current_mood == "glitchy":
                    message = f"J-j-joined {voice_channel.name}... c-c-connection est-established..."
            
            await ctx.send(message)
            return
            
        except discord.errors.ClientException as ce:
            if "Already connected" in str(ce):
                logger.error(f"Already connected error: {ce}")
                await ctx.send("I appear to be stuck between voice states. Please try again.")
                # Try to clean up any existing connections
                try:
                    if ctx.guild.voice_client:
                        await ctx.guild.voice_client.disconnect(force=True)
                    if ctx.guild.id in self.bot._connection._voice_clients:
                        del self.bot._connection._voice_clients[ctx.guild.id]
                except Exception:
                    pass
            else:
                logger.error(f"Discord client exception: {ce}")
                await ctx.send(f"Failed to join voice channel: {ce}")
        except asyncio.TimeoutError:
            logger.error("Voice connection timed out")
            await ctx.send("Connection timed out while trying to join voice. Please try again later.")
        except Exception as e:
            logger.error(f"Failed to connect to voice channel: {e}")
            await ctx.send(f"Unexpected error while joining voice channel: {e}")

    @commands.command(name="leave", help="Marcus will leave the voice channel")
    async def leave(self, ctx):
        """Command to make Marcus leave the voice channel"""
        voice_client = ctx.guild.voice_client
        if voice_client:
            await voice_client.disconnect()
            
            guild_id = str(ctx.guild.id)
            if guild_id in self.voice_clients:
                del self.voice_clients[guild_id]
                
            # Generate appropriate response based on emotion system
            emotion_cog = self.bot.get_cog("EmotionSystem")
            if emotion_cog:
                current_mood, _ = await emotion_cog.get_user_emotion(ctx.author.id)
                
                # Apply mood influence based on being told to leave
                if random.random() < 0.3:
                    await emotion_cog.apply_mood_influence("sadness", 0.3, ctx.author.id)
                
                # Different leave messages based on mood
                if current_mood in ["sad", "dreadful"]:
                    await ctx.send(f"Fine. I'll leave. But I'll still be **watching**, {ctx.author.mention}...")
                elif current_mood == "sarcastic":
                    await ctx.send(f"Leaving {ctx.guild.name} voice. Didn't want to be there anyway.")
                else:
                    await ctx.send(f"Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")
            
    @commands.command(name="stalk", help="Marcus will follow a user through voice channels")
    @commands.has_permissions(administrator=True)  # Admin only command
    async def stalk(self, ctx, *, target: discord.Member):
        """Command for admins to make Marcus stalk a user through voice channels"""
        if not target.voice or not target.voice.channel:
            await ctx.send(f"{target.display_name} is not in a voice channel.")
            return
            
        # Join their voice channel
        voice_channel = target.voice.channel
        await self.join_voice_channel(voice_channel, ctx.guild)
        
        # Add user to stalking list
        self.watching_voice_state.add(target.id)
        
        # Update emotion system - make Marcus ominous/dreadful toward this user
        emotion_cog = self.bot.get_cog("EmotionSystem")
        if emotion_cog:
            await emotion_cog.apply_mood_influence("fear", 0.8, target.id)
            
        # Get a creepy message from the lore system
        lore_cog = self.bot.get_cog("Lore")
        if lore_cog:
            theme = lore_cog.get_random_theme()
            quirk = lore_cog.get_random_quirk()
            await ctx.send(f"**Now stalking {target.mention}**. {theme} {quirk}")
        else:
            await ctx.send(f"**Now stalking {target.mention}**. I'll follow their every move...")
            
        # Remember this interaction
        speech_cog = self.bot.get_cog("Speech")
        if speech_cog:
            await speech_cog.remember_important_interaction(
                target.id, 
                "voice_stalk", 
                f"Marcus was commanded to stalk {target.name} in voice channels"
            )
            
    @commands.command(name="unstalk", help="Marcus will stop following a user")
    @commands.has_permissions(administrator=True)  # Admin only command
    async def unstalk(self, ctx, *, target: discord.Member):
        """Command for admins to make Marcus stop stalking a user"""
        if target.id in self.watching_voice_state:
            self.watching_voice_state.remove(target.id)
            await ctx.send(f"I'll stop following {target.display_name}... for now.")
            
            # Update emotion system
            emotion_cog = self.bot.get_cog("EmotionSystem")
            if emotion_cog:
                await emotion_cog.apply_mood_influence("neutral", 0.5, target.id)
        else:
            await ctx.send(f"I wasn't following {target.display_name}.")
            
    async def join_voice_channel(self, voice_channel, guild):
        """Helper method to join a voice channel"""
        guild_id = str(guild.id)
        
        # Check if PyNaCl is installed
        try:
            import nacl
        except ImportError:
            logger.error("PyNaCl library is required for voice. Install with: pip install PyNaCl")
            return False, "PyNaCl library is required for voice. Install with: pip install PyNaCl"
        
        try:
            # Check if already connected to a voice channel in this guild
            existing_voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
            
            if existing_voice_client:
                if existing_voice_client.channel.id != voice_channel.id:
                    logger.info(f"Moving from {existing_voice_client.channel.name} to {voice_channel.name} in {guild.name}")
                    await existing_voice_client.move_to(voice_channel)
                self.voice_clients[guild_id] = existing_voice_client
                return True, "Successfully moved to voice channel"
            else:
                # Connect to the voice channel with different approach
                try:
                    # Direct approach using discord.VoiceClient
                    voice_client = await voice_channel.connect(timeout=15.0, reconnect=True, self_deaf=False, self_mute=False)
                    self.voice_clients[guild_id] = voice_client
                    logger.info(f"Connected to voice channel {voice_channel.name} in {guild.name}")
                    
                    # Force initialize the voice client
                    if not voice_client.is_connected():
                        logger.warning("Voice client not connected after connect() call, trying manual connection")
                        try:
                            await voice_client._connect()
                        except Exception as conn_err:
                            logger.error(f"Manual connection failed: {conn_err}")
                except asyncio.TimeoutError:
                    logger.error("Voice connection timed out")
                    return False, "Connection timed out. Please try again."
                except discord.ClientException as e:
                    logger.error(f"Client exception while connecting to voice: {e}")
                    return False, f"Connection error: {e}"
                
            # Reset inactivity timer
            self.last_voice_action[guild_id] = datetime.utcnow()
            
            # Schedule disconnect after inactivity
            self._schedule_disconnect_check(guild_id)
            
            return True, "Successfully connected to voice channel"
        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            return False, f"Failed to connect to voice channel: {e}"
            
    def _schedule_disconnect_check(self, guild_id):
        """Schedule a check for inactivity"""
        # Cancel existing timer if any
        if guild_id in self.inactive_timers:
            self.inactive_timers[guild_id].cancel()
            
        # Create new timer
        async def check_inactivity():
            await asyncio.sleep(300)  # Check after 5 minutes
            if guild_id in self.last_voice_action:
                time_diff = datetime.utcnow() - self.last_voice_action[guild_id]
                
                # If no activity for 5 minutes and connected, disconnect
                if time_diff.total_seconds() > 300 and guild_id in self.voice_clients:
                    voice_client = self.voice_clients[guild_id]
                    if voice_client and voice_client.is_connected():
                        await voice_client.disconnect()
                        del self.voice_clients[guild_id]
                        
        # Create and store the task
        self.inactive_timers[guild_id] = asyncio.create_task(check_inactivity())

    async def text_to_speech(self, text, voice_type="en-US-Standard-B"):
        """Convert text to speech using Google TTS API"""
        try:
            # Use a fallback TTS service that doesn't require API keys
            url = f"https://api.streamelements.com/kappa/v2/speech?voice={voice_type}&text={text}"
            response = requests.get(url)
            if response.status_code == 200:
                return io.BytesIO(response.content)
            else:
                logger.error(f"TTS service returned status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return None
    
    async def say(self, guild_id, text):
        """Say text in a voice channel"""
        if not has_ffmpeg:
            logger.error("Cannot speak: FFmpeg not found")
            return False
            
        # Get voice client for this guild
        voice_client = self.voice_clients.get(str(guild_id))
        if not voice_client or not voice_client.is_connected():
            logger.error(f"Not connected to voice in guild {guild_id}")
            return False
            
        # Convert text to speech
        speech_data = await self.text_to_speech(text)
        if not speech_data:
            logger.error("Failed to convert text to speech")
            return False
            
        # Queue the audio if already speaking
        guild_id_str = str(guild_id)
        if guild_id_str not in self.tts_queue:
            self.tts_queue[guild_id_str] = []
            self.is_speaking[guild_id_str] = False
            
        # Add to queue and play if not already speaking
        self.tts_queue[guild_id_str].append((text, speech_data))
        if not self.is_speaking[guild_id_str]:
            await self._play_next_in_queue(guild_id_str)
        
        return True
        
    async def _play_next_in_queue(self, guild_id_str):
        """Play the next audio in queue"""
        if not self.tts_queue.get(guild_id_str) or not self.voice_clients.get(guild_id_str):
            self.is_speaking[guild_id_str] = False
            return
            
        self.is_speaking[guild_id_str] = True
        
        # Get the next item
        text, speech_data = self.tts_queue[guild_id_str].pop(0)
        voice_client = self.voice_clients[guild_id_str]
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(speech_data.getbuffer())
            temp_path = temp_file.name
            
        try:
            # Play the audio
            voice_client.play(
                discord.FFmpegPCMAudio(temp_path), 
                after=lambda e: self._speech_finished(e, guild_id_str, temp_path)
            )
            
            # Update activity timestamp
            self.last_voice_action[guild_id_str] = datetime.utcnow()
            
            logger.info(f"Speaking in guild {guild_id_str}: {text[:50]}...")
        except Exception as e:
            logger.error(f"Error playing speech in guild {guild_id_str}: {e}")
            # Clean up the temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            # Try the next in queue
            self.is_speaking[guild_id_str] = False
            await self._play_next_in_queue(guild_id_str)
    
    def _speech_finished(self, error, guild_id_str, temp_path):
        """Called when speech finishes playing"""
        # Clean up the temp file
        try:
            os.unlink(temp_path)
        except Exception as e:
            logger.error(f"Error deleting temp file: {e}")
            
        # Mark as not speaking to allow next item
        self.is_speaking[guild_id_str] = False
            
        # Schedule playing the next item using the bot's loop
        # since this callback runs in a separate thread
        async def schedule_next():
            await asyncio.sleep(0.5)  # Small pause between speech segments
            await self._play_next_in_queue(guild_id_str)
            
        # Use bot's event loop to schedule the task
        future = asyncio.run_coroutine_threadsafe(schedule_next(), self.bot.loop)
        
    async def speak_on_event(self, guild_id, event_type, text):
        """Speak in response to an event if connected to voice"""
        if str(guild_id) in self.voice_clients and self.voice_clients[str(guild_id)].is_connected():
            # Get emotion context for the response
            emotion_cog = self.bot.get_cog("EmotionSystem")
            speech_cog = self.bot.get_cog("Speech")
            
            response = text
            if speech_cog and random.random() < 0.4:
                # Add personality to the response
                if hasattr(speech_cog, "generate_response_with_personality"):
                    response = await speech_cog.generate_response_with_personality(text, 0)
            
            # Add appropriate glitches based on mood
            if emotion_cog:
                mood, intensity = await emotion_cog.get_user_emotion(0)  # 0 = bot's ID
                if mood in ["glitchy", "chaotic"] and random.random() < 0.5:
                    response = response.replace("s", "~s").replace("a", "~a")
                
            # Speak the response
            await self.say(guild_id, response)


async def setup(bot, db_pool):
    # Create the Voice cog instance and add it to the bot
    voice_cog = Voice(bot, db_pool)
    await bot.add_cog(voice_cog)
