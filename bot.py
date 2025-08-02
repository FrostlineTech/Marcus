# bot.py
# Add at the top with other imports
import discord
from discord import app_commands

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncpg  # Import asyncpg for PostgreSQL

# Load .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Constants
TEST_GUILD_ID = discord.Object(id=1394558066111942766) #Client Server given guild id for instant progagation of comamnds
TEST_GUILD_ID_2 = discord.Object(id=1283291824232075345)  #Developer server given guild id for instant progagation of comamnds for testing

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # Required for voice channel events

# Bot setup — disable default help_command to avoid conflicts
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Global variable to hold the DB pool
db_pool = None

# Modular command system
modules = {}

def register_module(name):
    def wrapper(func):
        modules[name] = func
        return func
    return wrapper

# ===== Module: Ping =====
@register_module("ping")
@bot.command(name="ping", help="Checks the bot's latency.")
async def ping(ctx):
    await ctx.send("Pong!")

# ===== Module: Greet =====
@register_module("greet")
@bot.command(name="greet", help="Greets the user.")
async def greet(ctx):
    await ctx.send(f"Hello Robert.. Have you had your moon juice?")

# ===== Module: Help (basic fallback command) =====
@register_module("help_custom")
@bot.command(name="helpme", help="Shows available commands.")
async def help_custom(ctx):
    cmds = ", ".join([cmd.name for cmd in bot.commands])
    await ctx.send(f"Available commands: {cmds}")

# ===== DB test command =====
@bot.command(name="dbtest", help="Tests the database connection.")
async def dbtest(ctx):
    global db_pool
    if db_pool is None:
        await ctx.send("Database connection is not initialized.")
        return
    try:
        async with db_pool.acquire() as connection:
            # Example query: fetch current time from DB
            result = await connection.fetchval("SELECT NOW()")
            await ctx.send(f"Database time is: {result}")
    except Exception as e:
        await ctx.send(f"Database error: {e}")


# ===== SLASH COMMANDS (GUILD ONLY) =====
@bot.tree.command(name="hello", description="Say hello!", guild=TEST_GUILD_ID)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey {interaction.user.mention}, this is a test slash command!")

# /addcontext slash command (guild only)
@bot.tree.command(name="addcontext", description="Add a message to Marcus's global context pool.", guild=TEST_GUILD_ID)
async def addcontext(interaction: discord.Interaction, message: str):
    """Slash command to add a message to Marcus's global context pool."""
    # Wait for cogs to be loaded
    speech_cog = bot.get_cog("Speech")
    if not speech_cog:
        await interaction.response.send_message("Speech module not loaded. Please try again later.", ephemeral=True)
        return
    await speech_cog.add_global_context(  # type: ignore[attr-defined]
        username=str(interaction.user),
        user_id=str(interaction.user.id),
        guild_id=str(interaction.guild.id) if interaction.guild else "DM",
        guild_name=interaction.guild.name if interaction.guild else "DM",
        message=message.strip()
    )
    await interaction.response.send_message(f"Added to Marcus's global context! Thank you, {interaction.user.mention}.", ephemeral=True)


# ===== Load Cogs (all as extensions) =====
async def load_modules():
    # Add ragelevel slash command (guild-specific if others are guild-specific)
    @app_commands.command(name="ragelevel", description="Check your current rage level with Marcus.")
    async def ragelevel_slash(interaction: discord.Interaction):
        global db_pool
        user_id = interaction.user.id
        if db_pool is None:
            await interaction.response.send_message("Database connection is not initialized.", ephemeral=True)
            return
        async with db_pool.acquire() as conn:
            print(f"[RAGE] Reading rage_level for user_id={user_id} (/ragelevel slash command)")
            row = await conn.fetchrow(
                "SELECT rage_level FROM marcus_rage WHERE user_id = $1", user_id
            )
            level = row["rage_level"] if row else 0
        await interaction.response.send_message(f"Your current Marcus rage level is: {level}", ephemeral=True)

    # Register with the same guild as other slash commands
    try:
        bot.tree.add_command(ragelevel_slash, guild=TEST_GUILD_ID)
    except Exception as e:
        print(f"[RAGE] Failed to add /ragelevel slash command: {e}")
    # Speech cog now requires db_pool, so we load it manually after db_pool is created
    import speech
    await speech.setup(bot, db_pool)
    await bot.load_extension("help")
    await bot.load_extension("Martus")
    # Load rage_escalation cog with db_pool
    import rage_escalation
    await rage_escalation.setup(bot, db_pool)
    
    # Load emotion system cog if exists
    try:
        import emotions
        await emotions.setup(bot, db_pool)
        print("[+] Loaded EmotionSystem cog.")
    except ImportError as e:
        print(f"[!] Failed to load EmotionSystem cog: {e}")
        
    # Load voice cog for voice channel functionality
    try:
        import voice
        await voice.setup(bot, db_pool)
        print("[+] Loaded Voice cog.")
    except ImportError as e:
        print(f"[!] Failed to load Voice cog: {e}")

loaded = False

# ===== Events =====
@bot.event
async def on_ready():
    global loaded, db_pool
    if loaded:
        return

    print(f"[+] Logged in as {bot.user}")
    print(f"[+] Active modules: {', '.join(modules.keys())}")


    # Create a connection pool for PostgreSQL

    # Check required environment variables
    if not all([DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT]):
        print("[!] One or more required database environment variables are missing.")
        return
    try:
        db_pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=int(DB_PORT) if DB_PORT is not None else 5432,
            min_size=1,
            max_size=5,
        )
        print("[+] Database connection pool created.")
    except Exception as e:
        print(f"[!] Failed to connect to the database: {e}")
        return

    await load_modules()
    loaded = True

    # Sync slash commands to test guild
    try:
        synced = await bot.tree.sync(guild=TEST_GUILD_ID)
        print(f"[+] Synced {len(synced)} slash command(s) to test server.")
    except Exception as e:
        print(f"[!] Failed to sync slash commands: {e}")

# ===== Run Bot =====
if __name__ == "__main__":
    if not TOKEN:
        print("[!] DISCORD_TOKEN environment variable is missing.")
    else:
        bot.run(TOKEN)
