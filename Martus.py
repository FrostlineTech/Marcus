import random
import discord
from discord.ext import commands

class Martus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.choices = ["rock", "paper", "scissors"]

    @commands.command(name="rps", help="Play Rock Paper Scissors with Marcus! Usage: !rps rock|paper|scissors")
    async def rps(self, ctx, user_choice: str):
        user_choice = user_choice.lower()
        if user_choice not in self.choices:
            await ctx.send(f"Invalid choice! Please choose one of: {', '.join(self.choices)}")
            return

        marcus_choice = random.choice(self.choices)

        # Determine outcome
        result = self.determine_winner(user_choice, marcus_choice)

        # Build embed message
        embed = discord.Embed(title="Rock Paper Scissors - Marcus vs You", color=discord.Color.green())
        embed.add_field(name="Your choice", value=user_choice.capitalize(), inline=True)
        embed.add_field(name="Marcus's choice", value=marcus_choice.capitalize(), inline=True)

        if result == "win":
            embed.description = "You win! Marcus admits defeat. 🏆"
        elif result == "lose":
            embed.description = "You lose! Marcus says: 'Waste of time I must find Jimbo James.'"
            embed.color = discord.Color.red()
        else:  # draw
            embed.description = "It's a draw! Try again."

        embed.set_footer(text="Powered by Frostline Entertainment / Frostlinesolutions.com")

        await ctx.send(embed=embed)

    def determine_winner(self, user, marcus):
        # Returns "win", "lose", or "draw"
        if user == marcus:
            return "draw"
        if (
            (user == "rock" and marcus == "scissors") or
            (user == "paper" and marcus == "rock") or
            (user == "scissors" and marcus == "paper")
        ):
            return "win"
        return "lose"

async def setup(bot):
    await bot.add_cog(Martus(bot))