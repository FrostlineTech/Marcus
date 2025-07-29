import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Try to get triggers from Speech cog if loaded, else fallback to these enhanced triggers
        speech_cog = bot.get_cog("Speech")
        if speech_cog and hasattr(speech_cog, "triggers"):
            self.speech_triggers = speech_cog.triggers
        else:
            self.speech_triggers = [
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

        # Martus game commands info
        self.game_commands = {
            "rps": "Play Rock Paper Scissors with Marcus! Usage: !rps rock|paper|scissors"
        }

    @commands.command(name="help", help="Display a list of available commands and Marcus triggers.")
    async def help_command(self, ctx):
        prefix = self.bot.command_prefix
        embed = discord.Embed(
            title="Marcus Bot Help",
            description="Here are the available commands and Marcus the Worm triggers:",
            color=discord.Color.blue()
        )

        # Add all commands except hidden ones
        for command in self.bot.commands:
            if command.hidden:
                continue
            name = f"{prefix}{command.name}"
            help_text = command.help or "No description provided."
            embed.add_field(name=name, value=help_text, inline=False)

        # Add Marcus triggers
        if self.speech_triggers:
            triggers_str = ", ".join(f"`{trigger}`" for trigger in self.speech_triggers)
            embed.add_field(
                name="Marcus the Worm Triggers",
                value=triggers_str,
                inline=False
            )

        # Add Martus game commands
        game_cmds_str = "\n".join(f"`{prefix}{cmd}`: {desc}" for cmd, desc in self.game_commands.items())
        embed.add_field(
            name="Martus Game Commands",
            value=game_cmds_str,
            inline=False
        )

        embed.set_footer(text="Powered by Frostline Entertainment / Frostlinesolutions.com")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
