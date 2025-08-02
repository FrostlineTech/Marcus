# Marcus Bot Patch Notes

## Version 2.0.0 - Personality System Update (August 2025)

### Major Features

#### 🧠 Emotion System

- Added new `emotions.py` cog to manage Marcus's emotional state
- Implemented dynamic mood system with weighted influences
- Created user-specific emotional response tracking
- Added mood decay that gradually returns to baseline
- Integrated with rage levels to create cohesive emotional responses

#### 📚 Lore & Backstory System

- Added new `lore.py` cog with extensive backstory fragments
- Created recurring themes and speech quirks for Marcus
- Added `!lore` command for users to discover Marcus's origin story
- Implemented dynamic lore integration in conversations
- Added cryptic references and thematic elements to responses

#### 💾 Memory System

- Implemented long-term memory storage for important user interactions
- Added memory recall based on conversation context and user
- Created relationship tracking based on interaction history
- Improved context awareness with memory integration

#### 🤝 Integration Improvements

- Enhanced `speech.py` to integrate with emotion and lore systems
- Added personality-driven responses based on emotional state
- Created contextual awareness between rage and emotion systems
- Implemented more nuanced responses based on user relationship

### Database Changes

- Added `marcus_emotional_events` table for tracking emotional interactions
- Added `marcus_memories` table for storing user-specific memories
- Added `marcus_user_emotions` table for tracking user emotional states
- Added `marcus_personality_evolution` table for tracking trait changes over time

### Technical Improvements

- Enhanced database query efficiency
- Implemented modular design for better extensibility
- Added comprehensive test suite for new systems

### Bug Fixes

- Fixed edge cases in rage cooldown calculations
- Improved error handling in database operations
- Reduced repetition in response generation
- Enhanced conversation context tracking

#### 🔊 Voice Channel Integration

- Added new `voice.py` cog for voice channel interaction
- Implemented commands to join and leave voice channels
- Created personality-driven voice channel behavior
- Integrated emotional state and rage level with voice interactions
- Added feature to follow users with high rage levels between channels
- Implemented mood-based voice channel join/leave messages

## Future Plans
- Event-based communication system between modules
- Enhanced adaptive communication style per user
- Advanced emotional learning from user reactions
- More user commands for interaction with Marcus's personality
- Voice activity detection and audio responses
