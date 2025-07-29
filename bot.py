import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Constants
TEST_GUILD_ID = discord.Object(id=1394558066111942766)  # Your test server

# Intents
intents = discord.Intents.default()
intents.message_content = True

# Bot setup — disable default help_command to avoid conflicts
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

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
    await ctx.send(f"Hello {ctx.author.name}, I'm Marcus!")

# ===== Module: Help (basic fallback command) =====
@register_module("help_custom")
@bot.command(name="helpme", help="Shows available commands.")
async def help_custom(ctx):
    cmds = ", ".join([cmd.name for cmd in bot.commands])
    await ctx.send(f"Available commands: {cmds}")

# ===== SLASH COMMAND EXAMPLE (GUILD ONLY) =====
@bot.tree.command(name="hello", description="Say hello!", guild=TEST_GUILD_ID)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey {interaction.user.mention}, this is a test slash command!")

# ===== Load Cogs (all as extensions) =====
async def load_modules():
    await bot.load_extension("speech")
    await bot.load_extension("help")
    await bot.load_extension("Martus")

loaded = False

# ===== Events =====
@bot.event
async def on_ready():
    global loaded
    if loaded:
        return

    print(f"[+] Logged in as {bot.user}")
    print(f"[+] Active modules: {', '.join(modules.keys())}")
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
    bot.run(TOKEN)
