# 🐛 Marcus the Worm

Marcus is a Discord bot that delivers cryptic quotes, reacts to cursed trigger words, and contains modular features including commands, cogs, and weirdcore lore. He has an evolving personality, emotional system, and rich backstory.

---

## 🧠 Features

- 🗯️ Random quote generation with personality quirks
- 🧃 Trigger-based speech system with contextual awareness
- 😈 Dynamic emotion system with mood influences
- 🔥 Rage escalation system with user-specific tracking
- 🔊 Voice channel integration with personality-aware behavior
- 📚 Rich lore and evolving backstory
- 💾 Memory system for user interactions
- 🎮 Experimental mini-game integration
- ⚙️ Modular Cog system
- 💬 Slash commands and traditional commands

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Discord Bot Token

### Environment Variables

Create a `.env` file with the following variables:

```env
DISCORD_TOKEN=your_discord_token
DATABASE_URL=your_postgres_connection_string
BOT_PREFIX=!
```

### Database Setup

Marcus requires several tables in your PostgreSQL database:

1. `global_context` - Stores conversation context
2. `user_rage` - Tracks user rage levels
3. `marcus_emotional_events` - Records emotional interactions
4. `marcus_memories` - Stores memories of user interactions
5. `marcus_user_emotions` - Tracks user-specific emotional states
6. `marcus_personality_evolution` - Tracks personality trait evolution

Run the SQL statements in the `setup_database.sql` file to create these tables.

### Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up the database tables
4. Run the bot: `python bot.py`

## 🤖 Personality System

Marcus features an advanced personality system with several integrated components:

### Emotion System

The Emotion System manages Marcus's mood, influences, and emotional responses to user interactions. Marcus's mood affects his responses and can be influenced by user messages and events.

### Lore & Backstory

Marcus has an extensive backstory and recurring themes that are dynamically integrated into his responses. Use the `!lore` command to learn more about Marcus's mysterious origin.

### Memory System

Marcus remembers important interactions with users, creating a personalized experience over time. This system allows for callbacks to previous conversations and user-specific relationship development.

### Rage Escalation

Marcus has an advanced rage tracking system that responds to certain trigger words with escalating levels of frustration. Each user has their own rage level tracked separately.

### Voice Channel Integration

Marcus can join voice channels and interact with users based on his emotional state and rage level. He may spontaneously follow users with high rage levels or respond differently based on his current mood. Use `!join` and `!leave` commands to control voice channel presence.

## 🔌 Cog Structure

- `bot.py` - Main bot initialization and event handling
- `speech.py` - Core conversational module
- `emotions.py` - Emotional state management
- `lore.py` - Backstory and thematic elements
- `rage_escalation.py` - Rage tracking and responses
- `voice.py` - Voice channel joining and interaction
- `Martus.py` - Rock Paper Scissors mini-game
- `help.py` - Help command implementation
