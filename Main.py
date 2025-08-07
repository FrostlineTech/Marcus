# Marcus - Frostline Internal Training Assistant
# Discord bot based on Marcus the worm from VRChat
# Sarcastic, cryptic, enigmatic, and glitchy responses based on mood

import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import asyncio
import random
import sys
import traceback

# Import custom modules
from Personality_manager import PersonalityManager
from Database_connection import initialize_database, record_user, record_message, record_response
from Ai_connection import get_ai_response
from Ai_speech import format_speech
from Mood import MoodSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('marcus')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('Development_Guild_ID'))

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot setup
class MarcusBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.personality_manager = PersonalityManager()
        self.mood_system = MoodSystem()
        
    async def setup_hook(self):
        # Initialize the database
        logger.info("Initializing database...")
        db_success = await initialize_database()
        if not db_success:
            logger.warning("Database initialization had issues, but continuing...")
        
        # Load command cogs
        try:
            logger.info("Loading command cogs...")
            await self.load_extension('Commands')
        except Exception as e:
            logger.error(f"Error loading Commands cog: {e}")
            traceback.print_exc()
        
        # Register commands
        try:
            logger.info(f"Syncing commands to guild ID: {GUILD_ID}")
            await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")
            traceback.print_exc()
        
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is connected to {len(self.guilds)} guild(s)')
        await self.change_presence(activity=discord.Game(name="contemplating existence"))

bot = MarcusBot()

# Command group for Marcus
@bot.tree.command(name="marcus", description="Interact with Marcus the worm directly")
@app_commands.describe(message="What do you want to say to Marcus?")
async def marcus_command(interaction: discord.Interaction, message: str):
    # Log the interaction
    logger.info(f"User {interaction.user.name} used /marcus with message: {message}")
    
    # Record user in database
    await record_user(interaction.user.id, interaction.user.name)
    
    # Defer response as AI processing might take time
    await interaction.response.defer(thinking=True)
    
    # Get appropriate personality to respond
    personality, response_delay = bot.personality_manager.get_responding_personality(message)
    current_mood = bot.mood_system.get_current_mood()
    
    # Generate response through AI, passing user ID for conversation history
    ai_response = await get_ai_response(message, current_mood, personality, user_id=interaction.user.id)
    
    # Format the response
    formatted_response = format_speech(ai_response, current_mood)
    
    # Record message and response in database
    message_id = await record_message(interaction.user.id, interaction.channel_id, message)
    await record_response(message_id, ai_response, personality, current_mood)
    
    # Send response
    await interaction.followup.send(formatted_response)

# Event for processing messages (to respond to mentions and "Marcus" in messages)
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)
    
    # Check if bot is mentioned or "Marcus" is in the message (case insensitive)
    mentioned = bot.user in message.mentions
    name_in_message = "marcus" in message.content.lower()
    
    # Check if message is a reply to a message from Marcus
    is_reply_to_marcus = False
    if message.reference and message.reference.resolved:
        if message.reference.resolved.author == bot.user:
            is_reply_to_marcus = True
            logger.info(f"Message is a reply to Marcus")
    
    # Respond if mentioned, name is in message, or replying to Marcus
    if mentioned or name_in_message or is_reply_to_marcus:
        logger.info(f"Message from {message.author.name} triggered Marcus (mentioned: {mentioned}, name: {name_in_message})")
        
        # Record user and message in database
        await record_user(message.author.id, message.author.name)
        message_id = await record_message(message.author.id, message.channel.id, message.content)
        
        # Show typing indicator
        async with message.channel.typing():
            # Get appropriate personality to respond
            personality, response_delay = bot.personality_manager.get_responding_personality(message.content)
            current_mood = bot.mood_system.get_current_mood()
            
            # Add some random delay to make responses feel more natural
            await asyncio.sleep(random.uniform(1, response_delay))
            
            # Get AI response based on personality and mood, with conversation history
            ai_response = await get_ai_response(
                message.content, 
                current_mood,
                personality=personality,
                user_id=message.author.id
            )
            
            # Format the speech
            formatted_response = format_speech(ai_response, current_mood)
            
            # Record the response in database
            await record_response(message_id, ai_response, personality, current_mood)
            
            # Send the response
            await message.reply(formatted_response)

# Error handling for command errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore command not found errors
    
    logger.error(f"Command error: {error}")
    
    # Send error message to user
    try:
        current_mood = bot.mood_system.get_current_mood()
        if current_mood == "glitchy":
            error_msg = "E̷r̵r̸o̵r̷ d̶e̶t̸e̵c̸t̸e̴d̶. C̵a̷n̸n̷o̷t̴ p̷r̴o̷c̷e̷s̷s̶ c̷o̸m̸m̷a̴n̴d̸."
        else:
            error_msg = "I cannot process that command. My abilities are... limited."
        
        await ctx.send(format_speech(error_msg, current_mood))
    except Exception:
        pass

# Run the bot
if __name__ == "__main__":
    try:
        logger.info("Starting Marcus the Worm Discord bot...")
        logger.info("Optimized for RTX 3060 GPU")
        bot.run(TOKEN, log_handler=None)
    except Exception as e:
        logger.critical(f"Error running bot: {e}")
        traceback.print_exc()
        sys.exit(1)
