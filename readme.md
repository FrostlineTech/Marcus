# Marcus the Worm Discord Bot

A Discord bot based on the character "Marcus the Worm" from VRChat - a mysterious worm creature known for cryptic, enigmatic, and occasionally profound statements delivered in a deadpan, unenthusiastic manner.

## Character Overview

Marcus is characterized by:

- Deadpan, unenthusiastic speech patterns
- Contradictory and paradoxical statements
- Cryptic observations about reality and existence
- Occasional text "glitches" mid-sentence
- Unexpectedly profound philosophical commentary
- Signature phrases like "This place is a dangerous place" and "I feel happiness as I begin to experience organ failure"

## Features

- Multiple personalities with different response patterns
- Dynamic mood system that changes Marcus's responses over time
- Text formatting effects based on current mood (glitchy, profound, cryptic, rage)
- Integration with DeepSeek R1 chatbot model for AI-driven responses
- Natural conversation flow with conversation history memory
- Context-aware responses to message replies
- PostgreSQL database for storing user interactions and rage levels
- Responds to mentions, name references, and message replies
- Discord slash commands for direct interaction

## Technical Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- DeepSeek R1 chatbot model running locally
- Discord bot token and application setup
- RTX 3060 GPU (optimized configuration included)

### Installation

1. Clone this repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt  
   ```

3. Configure your `.env` file with appropriate credentials
4. Create a PostgreSQL database named "marcus"
5. Run the bot:

   ```bash
   python Main.py
   ```

### Environment Variables (.env)

```env
# Discord settings
DISCORD_TOKEN=your_discord_token
Development_Guild_ID=your_guild_id

# AI settings
MODEL_NAME=lap2004_DeepSeek-R1-chatbot
AI_API_URL=http://127.0.0.1:5000
AI_API_PATH=/v1/chat/completions

# Database connection
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=marcus
```

## Architecture

The bot is built with a modular architecture:

- **Main.py**: Entry point and Discord event handling
- **Commands.py**: Slash command implementations
- **Ai_connection.py**: Interface with the DeepSeek R1 model with conversation context
- **Ai_speech.py**: Speech formatting and text effects
- **Personality_manager.py**: Manages different personality aspects
- **Mood.py**: Handles mood transitions and effects
- **Database_connection.py**: Database operations and user data

## GPU Optimization

This bot includes specific optimizations for the RTX 3060 GPU:

- Batch size and precision adjustments for optimal inference
- Memory-efficient prompt handling
- Temperature adjustments based on mood for response diversity

## Commands

- `/marcus <message>`: Directly interact with Marcus
- `/quote`: Get a random Marcus quote
- `/mood`: Check Marcus's current mood (admins can change it)
- `/annoy`: Intentionally annoy Marcus
- `/compliment`: Give Marcus a compliment
- `/help`: View information about Marcus commands

## Development

To extend the bot's functionality:

1. Add new personality types in `Personality_manager.py`
2. Create new mood states in `Mood.py`
3. Implement additional text effects in `Ai_speech.py`
4. Add new commands in `Commands.py`

## Natural Conversations

Marcus is designed to maintain natural conversations through:

- Conversation history tracking (remembers up to 5 previous exchanges)
- Contextual responses that reference previous parts of the conversation
- Automatic responses to message replies without needing to mention Marcus
- Dynamic personality selection based on message content
- Variable response delays based on personality and mood

## License

This project is licensed for private use only.
