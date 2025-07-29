import random
from discord.ext import commands

class Speech(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.quotes = [
            "I must make amends with the cartel.",
            "This place is dangerous.",
            "New Orleans.",
            "Atlantic ocean.",
            "Where is Jimbo James?",
            "Where is Robert?",
            "I feel happiness as I begin to experience organ failure.",
            "Have you tried the moon juice?",
            "This place is a dangerous place.",
        ]

        self.triggers = [
            "cartel",
            "dangerous",
            "orleans",
            "atlantic",
            "jimbo",
            "robert",
            "moon juice",
            "organ failure",
            "vrchat",
            "neon-lit weirdcore",
            "brainrot prophet",
            "felon",
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Skip messages that are commands
        if message.content.startswith(self.bot.command_prefix):
            return

        content = message.content.lower()
        if any(trigger in content for trigger in self.triggers):
            quote = random.choice(self.quotes)
            await message.channel.send(quote)

    @commands.command(name="wormquote", help="Get a Marcus the Worm quote.")
    async def wormquote(self, ctx):
        quote = random.choice(self.quotes)
        await ctx.send(quote)

async def setup(bot):
    await bot.add_cog(Speech(bot))
