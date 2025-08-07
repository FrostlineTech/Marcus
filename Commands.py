# Commands Module for Marcus Discord Bot
# Handles all slash commands and command registration

import discord
from discord import app_commands
from discord.ext import commands
import logging
import random
import asyncio

from Ai_connection import get_ai_response
from Ai_speech import format_speech
from Database_connection import update_rage_level, get_rage_level, record_user, record_message, record_response
from Mood import MoodState

# Configure logging
logger = logging.getLogger('marcus.commands')

class CommandsCog(commands.Cog):
    """Commands for interacting with Marcus the Worm"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="quote", description="Get a random Marcus quote")
    async def quote_command(self, interaction: discord.Interaction):
        """Generate a random Marcus quote"""
        logger.info(f"User {interaction.user.name} used /quote")
        
        # Record the user in the database
        await record_user(interaction.user.id, interaction.user.name)
        
        # Generate a random quote prompt
        quote_prompts = [
            "Share your wisdom about existence",
            "What do you think about reality",
            "Tell me something profound",
            "Share an observation about this place",
            "What are your thoughts right now"
        ]
        prompt = random.choice(quote_prompts)
        
        # Defer response as AI processing might take time
        await interaction.response.defer(thinking=True)
        
        # Get current mood
        current_mood = self.bot.mood_system.get_current_mood()
        
        # Generate response through AI
        ai_response = await get_ai_response(prompt, current_mood)
        
        # Format the response
        formatted_response = format_speech(ai_response, current_mood)
        
        # Send response
        await interaction.followup.send(formatted_response)
        
        # Record this interaction
        message_id = await record_message(interaction.user.id, interaction.channel_id, "/quote")
        await record_response(message_id, ai_response, "default", current_mood)
    
    @app_commands.command(name="mood", description="Check or change Marcus's current mood")
    @app_commands.describe(new_mood="Optional: Set a new mood for Marcus (admin only)")
    async def mood_command(self, interaction: discord.Interaction, new_mood: str = None):
        """Check or change Marcus's current mood"""
        logger.info(f"User {interaction.user.name} used /mood with param: {new_mood}")
        
        # Record the user
        await record_user(interaction.user.id, interaction.user.name)
        
        current_mood = self.bot.mood_system.get_current_mood()
        
        # If a new mood is specified, check if user is admin
        if new_mood:
            # Check if user has admin permissions
            if interaction.user.guild_permissions.administrator:
                # Try to set the mood
                valid_moods = [m.value for m in MoodState]
                
                if new_mood.lower() in valid_moods:
                    self.bot.mood_system.force_mood(new_mood.lower())
                    await interaction.response.send_message(
                        f"Marcus's mood has been set to **{new_mood.lower()}**.", 
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"Invalid mood. Valid moods are: {', '.join(valid_moods)}",
                        ephemeral=True
                    )
            else:
                # User doesn't have permission
                await interaction.response.send_message(
                    "You don't have permission to change Marcus's mood.",
                    ephemeral=True
                )
        else:
            # Just checking the current mood
            mood_descriptions = {
                "neutral": "I exist in a state of... normalcy.",
                "cryptic": "Secrets unfold within the shadow of perception.",
                "profound": "Contemplating the eternal dance of existence and void.",
                "glitchy": "Sy̶st͞ęm i̸nt̴e̶gr̸ity̵ c͞ơm̵pr̸o͘mis̀e̶d.",
                "rage": "INTERNAL PRESSURE EXCEEDS RECOMMENDED PARAMETERS!"
            }
            
            description = mood_descriptions.get(current_mood, "My state is... indescribable.")
            
            # Send response as Marcus
            formatted_response = format_speech(description, current_mood)
            await interaction.response.send_message(formatted_response)
            
            message_id = await record_message(interaction.user.id, interaction.channel_id, "/mood")
            await record_response(message_id, description, "default", current_mood)
    
    @app_commands.command(name="annoy", description="Intentionally annoy Marcus")
    async def annoy_command(self, interaction: discord.Interaction):
        """Command to intentionally annoy Marcus and increase rage"""
        logger.info(f"User {interaction.user.name} used /annoy")
        
        # Record the user
        await record_user(interaction.user.id, interaction.user.name)
        
        # Increase rage level
        new_rage = await update_rage_level(interaction.user.id, random.randint(5, 15))
        
        # Potentially change mood to rage if enough annoyance
        if new_rage > 70:
            self.bot.mood_system.force_mood("rage")
            current_mood = "rage"
        else:
            # Otherwise influence toward rage but don't force it
            self.bot.mood_system.influence_mood("rage", 0.4)
            current_mood = self.bot.mood_system.get_current_mood()
        
        # Generate angry response
        annoy_prompts = [
            "You're being intentionally annoying",
            "Someone is trying to make you angry",
            "React to someone bothering you",
            "Someone won't leave you alone",
            "You're being pestered"
        ]
        prompt = random.choice(annoy_prompts)
        
        # Defer response as AI processing might take time
        await interaction.response.defer(thinking=True)
        
        # Add some delay to build tension
        await asyncio.sleep(random.uniform(1.0, 2.5))
        
        # Get response
        ai_response = await get_ai_response(prompt, current_mood, "rage")
        
        # Format response, force rage formatting if rage is high
        formatted_response = format_speech(ai_response, "rage" if new_rage > 50 else current_mood)
        
        # Send response
        await interaction.followup.send(formatted_response)
        
        # Record interaction
        message_id = await record_message(interaction.user.id, interaction.channel_id, "/annoy")
        await record_response(message_id, ai_response, "rage", current_mood)
    
    @app_commands.command(name="compliment", description="Give Marcus a compliment")
    async def compliment_command(self, interaction: discord.Interaction):
        """Command to compliment Marcus and decrease rage"""
        logger.info(f"User {interaction.user.name} used /compliment")
        
        # Record the user
        await record_user(interaction.user.id, interaction.user.name)
        
        # Decrease rage level
        new_rage = await update_rage_level(interaction.user.id, random.randint(-15, -5))
        
        # Defer response as AI processing might take time
        await interaction.response.defer(thinking=True)
        
        # Current mood
        current_mood = self.bot.mood_system.get_current_mood()
        
        # If in rage mode and rage level decreases enough, change mood
        if current_mood == "rage" and new_rage < 30:
            # Randomly select a new mood that's not rage
            new_mood = random.choice(["neutral", "cryptic", "profound", "glitchy"])
            self.bot.mood_system.force_mood(new_mood)
            current_mood = new_mood
            
        # Generate appropriate response
        compliment_prompts = [
            "Someone just complimented you",
            "React to someone being nice to you",
            "Someone said something sweet to you",
            "A user is trying to make you feel better",
            "Someone is being very kind to you"
        ]
        prompt = random.choice(compliment_prompts)
        
        # Get response
        ai_response = await get_ai_response(prompt, current_mood)
        
        # Format response
        formatted_response = format_speech(ai_response, current_mood)
        
        # Send response
        await interaction.followup.send(formatted_response)
        
        # Record interaction
        message_id = await record_message(interaction.user.id, interaction.channel_id, "/compliment")
        await record_response(message_id, ai_response, "default", current_mood)
    
    @app_commands.command(name="help", description="Learn how to interact with Marcus")
    async def help_command(self, interaction: discord.Interaction):
        """Show help information about Marcus bot"""
        
        embed = discord.Embed(
            title="Marcus the Worm",
            description="A mysterious worm creature from the depths of VRChat.",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="Basic Interaction",
            value="Just mention Marcus or include his name in your message to talk to him.",
            inline=False
        )
        
        embed.add_field(
            name="Commands",
            value=(
                "`/marcus <message>` - Talk directly to Marcus\n"
                "`/quote` - Get a random Marcus quote\n"
                "`/mood` - Check Marcus's current mood\n"
                "`/annoy` - Intentionally annoy Marcus\n"
                "`/compliment` - Give Marcus a compliment\n"
                "`/help` - Show this help message"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Moods",
            value=(
                "Marcus has different moods that affect his responses:\n"
                "• Neutral - Standard Marcus behavior\n"
                "• Cryptic - More mysterious and enigmatic\n"
                "• Profound - Philosophical and deep\n"
                "• Glitchy - Text corruption and erratic behavior\n"
                "• Rage - Angry and aggressive"
            ),
            inline=False
        )
        
        embed.set_footer(text="This place is a dangerous place.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
async def setup(bot):
    """Add the commands cog to the bot"""
    await bot.add_cog(CommandsCog(bot))
    logger.info("Commands cog loaded")
