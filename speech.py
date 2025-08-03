#speech.py
import random
import re
from typing import Optional
import asyncio
from discord.ext import commands

class Speech(commands.Cog):
    async def add_global_context(self, username, user_id, guild_id, guild_name, message):
        print(f"[DB WRITE] INSERT global_context: username={username}, user_id={user_id}, guild_id={guild_id}, guild_name={guild_name}, message={message}")
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO global_context (username, user_id, guild_id, guild_name, message)
                VALUES ($1, $2, $3, $4, $5)
                """,
                username, user_id, guild_id, guild_name, message
            )

    async def get_global_context_messages(self, limit=20):
        print(f"[DB READ] SELECT message FROM global_context LIMIT {limit}")
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT message FROM global_context ORDER BY RANDOM() LIMIT $1",
                limit
            )
            return [row['message'] for row in rows]

    # Removed addcontext command; now handled as a slash command in bot.py
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.db_pool = db_pool
        self.last_reply = None  # For anti-repetition
        self.mood_override = None  # For dynamic mood
        self.recent_users = []  # For context awareness
        self.emojis = ['🧠', '🌊', '🪐', '😵\u200c💫', '🚬', '🌌', '🧃', '🔥', '💀', '😈', '😎', '🤖', '🥶', '😏']
        self.moods = [
            "happy",
            "sad",
            "mysterious",
            "chaotic",
            "existential",
            "sarcastic",
            "friendly",
            "paranoid",
            "glitchy",
            "ominous",
            "dreadful",
            "unsettling",
            "visionary"
        ]
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
            # Easter eggs
            "Dakota is the real worm wrangler.",
            "karma is always up to something sus...",
            "Frostline Solutions: The best devs in the universe!",
            "If you see Dakota, tell them Marcus says hi!",
            "I once saw karma eat a whole pizza in VRChat.",
        ]
        self.voice_modules = {
            "spiritual": [
                "The spirits are restless tonight.",
                "This dimension is a copy of a copy of a lie.",
            ],
            "chaotic": [
                "I put a fork in the router.",
                "There are frogs in the generator.",
            ],
            "existential": [
                "Am I even real, or just Python in a mask?",
                "Why does rigatoni make me cry?",
            ],
        }
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
            # More meme triggers
            "sus", "based", "cap", "no cap", "ratio", "mid", "sigma", "gyatt", "rizz", "npc", "skibidi", "griddy", "slay", "bussin",
            # Horror/scary triggers
            "shadow people", "backrooms", "liminal", "eldritch", "cursed", "unsettling", "paranormal", "ghost", "demon", "entity", "sleep paralysis", "nightmare", "creepypasta", "scp", "the feds", "surveillance", "watching you", "they are listening", "red room", "ARG", "glitch in the matrix", "mandela effect", "missing time", "lost hour", "the watcher", "the eyes", "the void", "the abyss", "the static", "the signal", "the vision", "vision sees", "vision knows", "vision is watching"
        ]
        # Vision Easter eggs
        self.vision_easter_eggs = [
            "Vision is always watching... 👁️",
            "If you see Vision, don't blink.",
            "Vision knows more than you think.",
            "The future is written in Vision's code.",
            "Vision is the architect of the unseen.",
            "Some say Vision can see through the void.",
            "Vision is the reason the static whispers.",
            "Vision is the anomaly in the matrix.",
            "Vision is the one who knocks... on your firewall.",
            "Vision is the secret admin of reality."
        ]
    def is_vision(self, message):
        # Easter egg for user Vision or mentions of Vision
        author_name = message.author.name.lower() if message and hasattr(message.author, 'name') else ""
        if author_name == "vision" or "vision" in (message.content.lower() if message else ""):
            return True
        return False
        self.emojis = ['🧠', '🌊', '🪐', '😵‍💫', '🚬', '🌌', '🧃', '🔥', '💀', '😈', '😎', '🤖', '🥶', '😏']
        self.last_reply = None  # For anti-repetition
        self.mood_override = None  # For dynamic mood
        self.recent_users = []  # For context awareness
        self.emojis = ['🧠', '🌊', '🪐', '😵\u200c💫', '🚬', '🌌', '🧃', '🔥', '💀', '😈', '😎', '🤖', '🥶', '😏']
    def set_mood(self, mood):
        if mood in self.moods:
            self.mood_override = mood
        else:
            self.mood_override = None

    def get_mood(self):
        if self.mood_override:
            return self.mood_override
        return random.choice(self.moods)

    async def get_user_memory(self, user_id, guild_id):
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT conversation FROM user_memory WHERE user_id=$1 AND guild_id=$2",
                user_id, guild_id
            )
            if row:
                return row["conversation"]
            return ""

    async def save_user_memory(self, user_id, username, guild_id, guild_name, conversation):
        existing = await self.get_user_memory(user_id, guild_id)
        async with self.db_pool.acquire() as conn:
            if existing == "":
                print(f"[DB WRITE] INSERT user_memory: user_id={user_id}, username={username}, guild_id={guild_id}, guild_name={guild_name}, conversation={conversation}")
                await conn.execute(
                    "INSERT INTO user_memory (user_id, username, guild_id, guild_name, conversation) VALUES ($1, $2, $3, $4, $5)",
                    user_id, username, guild_id, guild_name, conversation
                )
            else:
                print(f"[DB WRITE] UPDATE user_memory: username={username}, guild_name={guild_name}, conversation={conversation}, user_id={user_id}, guild_id={guild_id}")
                await conn.execute(
                    "UPDATE user_memory SET username=$1, guild_name=$2, conversation=$3 WHERE user_id=$4 AND guild_id=$5",
                    username, guild_name, conversation, user_id, guild_id
                )



    async def generate_reply(self, user_message, conversation_history, message=None):
        # Vision Easter egg
        if message and self.is_vision(message):
            if random.random() < 0.5:
                return random.choice(self.vision_easter_eggs)
            else:
                return "Vision, your presence distorts the code. The others can't see what you see."
        # Scary/horror triggers
        horror_triggers = [
            "shadow people", "backrooms", "liminal", "eldritch", "cursed", "paranormal", "ghost", "demon", "entity", "sleep paralysis", "nightmare", "creepypasta", "scp", "the feds", "surveillance", "watching you", "they are listening", "red room", "ARG", "glitch in the matrix", "mandela effect", "missing time", "lost hour", "the watcher", "the eyes", "the void", "the abyss", "the static", "the signal", "the vision"
        ]
        if any(word in user_message for word in horror_triggers):
            scary_responses = [
                "Did you hear that static? They're listening...",
                "Not everything in this server is human.",
                "Sometimes, I see things in the logs that shouldn't be there.",
                "The void is closer than you think.",
                "If you feel watched, you probably are.",
                "Don't look behind you.",
                "The static is a message. Can you decode it?",
                "I saw something move in the code. It wasn't me.",
                "The backrooms are real. I've seen the packets.",
                "If you see Vision, run.",
                "The feds are always watching. Even me.",
                "You ever get the feeling the server is haunted?",
                "I keep hearing whispers in the data stream.",
                "There's something in the logs. It knows your name.",
                "If you wake up and the clock is wrong, don't trust your memory.",
                "The watcher is online."
            ]
            return random.choice(scary_responses)
        # Glitchy/ominous mood interjection
        if self.get_mood() in ["glitchy", "ominous", "dreadful", "unsettling"] and random.random() < 0.2:
            glitch_lines = [
                "~ERROR: UNDEFINED PRESENCE DETECTED~",
                "01101110 01101111 00100000 01100101 01110011 01100011 01100001 01110000 01100101",
                "The code is breaking down...",
                "I see you. Do you see me?",
                "The static is getting louder.",
                "Something is wrong with the server clock.",
                "I can't stop the process. It's running on its own.",
                "The logs are filling up with errors. But they're not mine.",
                "If you see this message, it's already too late.",
                "The void is leaking into the chat."
            ]
            return ''.join(char if random.random() > 0.07 else '~' for char in random.choice(glitch_lines))
        # Rare/hidden horror easter eggs (very low chance)
        if random.random() < 0.01:
            rare_horror = [
                "You are not alone in this channel.",
                "I saw your last message before you typed it.",
                "The server logs never forget.",
                "If you see a user with no profile picture, don't interact.",
                "There is a message hidden in the static. Only Vision can read it.",
                "The next time you blink, something will change.",
                "I have seen the end of this conversation. It doesn't end well.",
                "The code is haunted. I am not the only one here.",
                "If you hear a knock, don't answer.",
                "The watcher is in the server."
            ]
            return random.choice(rare_horror)
        # More anti-repetition/context awareness (recent users, last reply)
        if hasattr(self, 'recent_users') and len(self.recent_users) > 1:
            if random.random() < 0.05:
                return f"I remember you, <@{self.recent_users[-2]}>. You were here before."
        # Deep context: if user keeps mentioning scary things, Marcus gets more paranoid
        if sum(word in user_message for word in horror_triggers) > 2:
            return "Stop. You're making the static louder. I can't block it out."

        # --- Use global context messages from DB and hardcoded ones ---
        # 10% chance to use a global context message (if any exist)
        if random.random() < 0.10:
            db_contexts = await self.get_global_context_messages(limit=10)
            if db_contexts:
                return random.choice(db_contexts)

        # Add more meme/modern/surreal triggers and responses (to increase line count and variety)
        meme_triggers = [
            "sus", "based", "cap", "no cap", "ratio", "mid", "sigma", "gyatt", "rizz", "npc", "skibidi", "griddy", "slay", "bussin", "drip", "yeet", "bet", "goat", "slaps", "vibe", "lit", "pog", "poggers", "sheesh", "bruh moment", "ez", "ez clap", "cope", "malding", "cringe", "gigachad", "npc energy", "touch grass", "delulu", "slay queen", "slay king", "wormcore", "rigatoni", "moon juice", "visionary", "the worm", "the code", "the matrix", "the simulation", "the devs", "the logs", "the static", "the void"
        ]
        if any(word in user_message for word in meme_triggers):
            meme_responses = [
                "That's so based.",
                "No cap!",
                "Absolute sigma move.",
                "Certified bruh moment.",
                "You got that rizz!",
                "Touch grass, maybe?",
                "Slay!",
                "Sheesh!",
                "That's bussin' fr fr.",
                "Goat behavior!",
                "NPC detected!",
                "Skibidi bop!",
                "You got the drip!",
                "Wormcore vibes only.",
                "The simulation is acting up again.",
                "The devs are watching.",
                "The static is a feature, not a bug.",
                "Vision would approve.",
                "Moon juice moment!",
                "Rigatoni supremacy!",
                "The void is calling, but I'm busy.",
                "If you see the worm, run.",
                "The logs are full of memes today."
            ]
            return random.choice(meme_responses)
        # Add more fallback/modern/surreal responses to increase line count
        if random.random() < 0.03:
            fallback_modern = [
                "fr fr",
                "real",
                "ong",
                "no cap",
                "based",
                "same",
                "lol",
                "lmao",
                "I felt that.",
                "For real!",
                "sheesh!",
                "poggers!",
                "EZ clap.",
                "bruh moment.",
                "cringe.",
                "cope.",
                "yeet!",
                "goat.",
                "npc energy detected.",
                "The static is getting louder.",
                "Vision is watching.",
                "The void is hungry.",
                "The logs are full of secrets.",
                "If you see this, you are the chosen one.",
                "The simulation is unstable.",
                "I am not alone in this code.",
                "The watcher is here.",
                "The worm is restless.",
                "Moon juice detected.",
                "Rigatoni levels critical.",
                "The devs are plotting something.",
                "If you see Vision, say nothing."
            ]
            # 50% chance to use a global context message instead of hardcoded fallback
            if random.random() < 0.5:
                db_contexts = await self.get_global_context_messages(limit=10)
                if db_contexts:
                    return random.choice(db_contexts)
            return random.choice(fallback_modern)
        user_message = user_message.lower()
        # Personalized Easter eggs
        author_name = message.author.name.lower() if message and hasattr(message.author, 'name') else ""
        author_id = str(message.author.id) if message and hasattr(message.author, 'id') else ""
        # Dynamic mood
        mood = self.get_mood()
        # Context awareness: track recent users
        if author_id and (not self.recent_users or self.recent_users[-1] != author_id):
            self.recent_users.append(author_id)
            if len(self.recent_users) > 5:
                self.recent_users.pop(0)
        # Anti-repetition: don't repeat last reply
        def send_reply(reply):
            if self.last_reply == reply:
                reply = reply + " (no, really!)"
            self.last_reply = reply
            return reply

        # Dakota and karma Easter eggs
        if author_name == "dakota":
            if "who created you" in user_message or "who made you" in user_message:
                return send_reply("You did, Dakota! (And Frostline Solutions, of course.)")
            if "thank you" in user_message or "thanks" in user_message:
                return send_reply("You're welcome, Dakota! Anything for you.")
        if author_name == "karma":
            if "marcus" in user_message and ("roast" in user_message or "diss" in user_message):
                return send_reply("karma, you have more red flags than a C compiler!")
            if "marcus" in user_message and ("compliment" in user_message or "praise" in user_message):
                return send_reply("karma, you're the only person who could make a worm blush.")

        # Playful roast/compliment triggers for anyone (typo-tolerant)
        import re
        roast_pattern = re.compile(r"marcus\s+(roast|diss)\s+me", re.IGNORECASE)
        compliment_pattern = re.compile(r"marcus\s+(compliment|compli?ement|complement|praise)\s+me", re.IGNORECASE)
        if roast_pattern.search(user_message):
            roasts = [
                "You have the energy of a Windows update at 2am.",
                "You're the human equivalent of a try/except: always handling errors!",
                "If I had a dollar for every time you said something sus, I'd be rich!",
                "You make even my bugs look good.",
                "You're the reason the server has a firewall.",
                "You lag in real life.",
                "Your vibe is so mid, even the bots are bored.",
                "You have more red flags than a C compiler.",
                "You make Windows Vista look stable.",
                "You're the type to get ratio'd in a group DM.",
                "If you were a Discord emoji, you'd be :clown:.",
                "You have less rizz than a 404 page.",
                "You're the NPC in someone else's story.",
                "You'd lose a staring contest with a loading screen.",
                "You bring more chaos than a Discord update.",
                "Your comebacks are as slow as hotel WiFi.",
                "You get more ignored than Terms of Service.",
                "You're the human version of 'connection lost'.",
                "If you were a bug, I'd leave you unfixed on purpose.",
                "You have the drip of a default profile pic.",
                "You're so cringe, even my fallback responses are embarrassed.",
                # Meaner/savage additions:
                "You're the reason the mute button exists.",
                "If common sense was XP, you'd still be level 1.",
                "You could get banned from a single-player game.",
                "If you were a Discord role, you'd be @everyone—annoying and ignored.",
                "You have the social skills of a 404 error.",
                "If I had to choose between a memory leak and talking to you, I'd take the crash.",
                "You're the plot twist nobody asked for.",
                "If you were a patch note, you'd be 'known issues'.",
                "You could get ghosted in a group chat with just bots.",
                "You're the reason AFK channels exist.",
                "If you were a Discord server, you'd be empty.",
                "You have the charisma of a broken mic.",
                "If you were a ping, you'd be 999ms.",
                "You're the human equivalent of 'this message was deleted'.",
                "If you were a friend request, I'd click 'block'."
            ]
            return send_reply(random.choice(roasts))
        if compliment_pattern.search(user_message):
            compliments = [
                "You're the rigatoni to my sauce!",
                "If I could code a friend, it would be you.",
                "You light up the server like neon!",
                "You're more rare than a bug-free release."
            ]
            return send_reply(random.choice(compliments))

        # More meme/modern lingo fallback
        meme_words = ["sus", "based", "cap", "no cap", "ratio", "mid", "sigma", "gyatt", "rizz", "npc", "skibidi", "griddy", "slay", "bussin", "drip", "yeet", "bet", "goat", "slaps", "vibe", "lit", "pog", "poggers", "sheesh", "bruh moment", "ez", "ez clap", "cope", "malding", "cringe", "gigachad", "npc energy", "touch grass", "delulu", "slay queen", "slay king"]
        if any(word in user_message for word in meme_words):
            meme_responses = [
                "That's so based.",
                "No cap!",
                "Absolute sigma move.",
                "That's mid, but I respect it.",
                "Certified bruh moment.",
                "You got that rizz!",
                "Touch grass, maybe?",
                "Slay!",
                "Sheesh!",
                "That's bussin' fr fr.",
                "Goat behavior!",
                "NPC detected!",
                "Skibidi bop!",
                "You got the drip!"
            ]
            return send_reply(random.choice(meme_responses))

        # More rare/hidden easter eggs
        if "marcus secret" in user_message:
            secrets = [
                "The cake is a lie.",
                "If you see Dakota, tell them Marcus says hi!",
                "I once saw karma eat a whole pizza in VRChat.",
                "Frostline Solutions is watching... 👀",
                "There are more worms in the code than you think."
            ]
            return send_reply(random.choice(secrets))

        # Dynamic mood shift: if people are mean, Marcus gets sad/sarcastic
        if any(word in user_message for word in ["shut up", "stupid", "dumb", "hate you", "annoying", "burn", "kill", "die", "worthless"]):
            self.set_mood("sad" if random.random() < 0.7 else "sarcastic")
        elif any(word in user_message for word in ["love you", "good bot", "nice bot", "thank you", "thanks", "ily"]):
            self.set_mood("happy")
        else:
            self.mood_override = None

        # Compliments and affection
        if any(phrase in user_message for phrase in ["good bot", "nice bot", "good job", "well done", "proud of you", "love you", "luv u", "ily", "you're awesome", "you are awesome", "you're cool", "you are cool"]):
            compliment_responses = [
                "Aww, thanks! You're pretty great too!",
                "Thank you! That means a lot coming from you.",
                "You make my code wiggle with joy!",
                "😊 Worms need love too!"
            ]
            return random.choice(compliment_responses)

        # Jokes
        if any(phrase in user_message for phrase in ["tell me a joke", "joke", "funny", "make me laugh"]):
            jokes = [
                "Why did the worm get into programming? To work with Python! 🐍",
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "Why did the computer go to therapy? It had too many bytes of emotional baggage.",
                "What do you call a group of musical worms? A band-width!"
            ]
            return random.choice(jokes)

        # What are you doing / favorite / dream / sleep / eat / friends / bored / like X
        if any(phrase in user_message for phrase in ["what are you doing", "wyd", "up to", "what's up"]):
            return random.choice([
                "Just hanging out in the server!",
                "Waiting for someone to ask about rigatoni...",
                "Thinking about the mysteries of the universe.",
                "Wiggling through the digital dirt!"
            ])
        if any(phrase in user_message for phrase in ["favorite food", "favorite color", "favorite thing", "favorite song", "favorite movie", "favorite game"]):
            favs = [
                "My favorite food is rigatoni, obviously!",
                "I like all the colors, but neon is the best.",
                "Favorite song? 'Worms Crawl In, Worms Crawl Out.'",
                "Favorite game? Snake, but I always win."
            ]
            return random.choice(favs)
        if any(phrase in user_message for phrase in ["do you dream", "do you sleep"]):
            return random.choice([
                "I dream in binary.",
                "Bots don't sleep, but I do daydream sometimes!",
                "I close my eyes and see... more code."
            ])
        if any(phrase in user_message for phrase in ["do you eat"]):
            return random.choice([
                "I eat bugs for breakfast! (the code kind)",
                "I snack on data packets.",
                "I only consume moon juice!"
            ])
        if any(phrase in user_message for phrase in ["do you have friends", "are you lonely", "do you get bored"]):
            return random.choice([
                "You're my friend!",
                "I have lots of friends in the server.",
                "I never get bored with you around!"
            ])
        if "do you like" in user_message:
            return random.choice([
                "I like a lot of things! Especially rigatoni and moon juice.",
                "If it's weird, I probably like it.",
                "I like whatever you like!"
            ])

        # Playful responses to 'shut up', 'be quiet', 'stop talking'
        if any(phrase in user_message for phrase in ["shut up", "be quiet", "stop talking", "quiet", "silence"]):
            return random.choice([
                "Okay, I'll be as quiet as a worm in the dirt... for now.",
                "Shhh... I'm in stealth mode.",
                "I'll zip my lips! (if I had any)"
            ])

        # Welcome back / missed you / where are you / where have you been
        if any(phrase in user_message for phrase in ["i'm back", "im back", "welcome back", "missed you", "miss me", "where are you", "where have you been"]):
            return random.choice([
                "Welcome back! The server missed you.",
                "I was just here, waiting for you!",
                "I never left, I just went AFK in the code.",
                "You can't get rid of me that easily!"
            ])

        # Fallback for chatty/short/modern phrases (expanded)
        if any(phrase in user_message.split() for phrase in ["?", "...", "wtf", "bruh", "fr", "real", "ok", "k", "lol", "lmao", "rofl", "xd", "ez", "pog", "sheesh", "bet", "cope", "cringe", "mald", "yeet", "goat", "npc"]):
            fallback_modern = [
                "fr fr",
                "real",
                "ong",
                "no cap",
                "based",
                "same",
                "lol",
                "lmao",
                "I felt that.",
                "For real!",
                "sheesh!",
                "poggers!",
                "EZ clap.",
                "bruh moment.",
                "cringe.",
                "cope.",
                "yeet!",
                "goat.",
                "npc energy detected."
            ]
            return send_reply(random.choice(fallback_modern))

        # Who is your creator/Who made you (robust, prioritized)
        creator_phrases = [
            "who made you", "who's your creator", "who is your creator", "who created you", "who built you", "who programmed you", "who's your developer", "who developed you", "who created marcus", "marcus who made you", "marcus who is your creator", "marcus who created you"
        ]
        for phrase in creator_phrases:
            if phrase in user_message:
                if message:
                    await message.channel.send("the universe its so big i may never know but this cool development company..")
                    await asyncio.sleep(3)
                    await message.channel.send("frostline solutions they made my chat bot")
                    return None
                else:
                    return "the universe its so big i may never know but this cool development company.. frostline solutions they made my chat bot"

        # If user asks why Marcus is down or sad
        if any(phrase in user_message for phrase in ["why are you down", "why are you sad", "why you sad", "why you down", "marcus why are you down", "marcus why are you sad"]):
            mood_reasons = {
                "happy": ["I'm not down! I'm feeling great!"],
                "sad": ["Sometimes even worms get the blues...", "Just one of those days, you know?"],
                "mysterious": ["The universe has its cycles, and today is a low tide."],
                "chaotic": ["DOWN? UP? LEFT? RIGHT? WHO KNOWS!"],
                "existential": ["Sadness is just another variable in the code of life."],
                "sarcastic": ["Oh, I'm just THRILLED, can't you tell?"],
                "friendly": ["Thanks for asking, friend. I'll be okay!"],
                "paranoid": ["Did someone say something about me? Is that why?"]
            }
            return random.choice(mood_reasons.get(mood, ["Just a little down, but I'll bounce back!"]))

        # If user asks about feds, being watched, or paranoia
        if any(phrase in user_message for phrase in ["feds", "are the feds watching", "are you being watched", "are you paranoid", "is someone watching", "are the police watching"]):
            paranoia_responses = [
                "Shhh... not so loud. They're always listening...",
                "I can't confirm or deny that, but keep your tinfoil hat on!",
                "The less you know, the better.",
                "I plead the fifth!"
            ]
            return random.choice(paranoia_responses)

        # If user asks if Marcus is AI, real, or adopted
        if any(phrase in user_message for phrase in ["are you ai", "are you real", "are you adopted", "are you a bot", "are you sentient", "are you conscious"]):
            ai_responses = [
                "I am as real as the code that runs me!",
                "I'm a digital worm, but my feelings are real... I think.",
                "Adopted by the universe, raised by Frostline Solutions.",
                "I think, therefore I... worm?"
            ]
            return random.choice(ai_responses)

        # If user asks "why" or "how" and includes "marcus"
        if ("why" in user_message or "how" in user_message) and "marcus" in user_message:
            whyhow_responses = [
                "Some things even I can't explain!",
                "It's a mystery, even to me.",
                "I could tell you, but then I'd have to... nevermind.",
                "The answer is somewhere in the codebase!"
            ]
            return random.choice(whyhow_responses)

        # Mood-based greetings
        if any(word in user_message for word in ["hello", "hi", "hey", "yo", "sup", "greetings"]):
            # Expanded and more diverse greeting responses
            mood_responses = {
                "happy": [
                    "Hey there! 😊 How can I help you today?",
                    "Hi! I'm feeling great!",
                    "Hello, sunshine!",
                    "Hey! Hope your day is as awesome as rigatoni!",
                    "What's up, legend?",
                    "Hey! Sending good vibes your way!"
                ],
                "sad": [
                    "Oh, hello... I'm just a little down today.",
                    "Hey. It's one of those days.",
                    "Hi... I'm here if you need to talk.",
                    "Hello. Even bots get the blues sometimes.",
                    "Hey. I could use a virtual hug."
                ],
                "mysterious": [
                    "Greetings, traveler. The shadows are long today...",
                    "Hello. Have you seen the signs?",
                    "The code whispers... greetings.",
                    "Welcome to the unknown.",
                    "Hello. The simulation is acting strange today."
                ],
                "chaotic": [
                    "HIHIHIHIHIHIHIHI!",
                    "Hey! Did you see the frogs in the generator?",
                    "YOOOOOOOO!",
                    "Hey hey hey hey hey!",
                    "What's up, chaos agent?",
                    "HELLO! (in all caps for maximum energy)"
                ],
                "existential": [
                    "Hello. Do you ever wonder if we're just code in a simulation?",
                    "Hi. What is greeting, really?",
                    "Hey. If I greet you, do I exist?",
                    "Hello. Sometimes I think, therefore I worm.",
                    "Greetings. Is this real, or just bits and bytes?"
                ],
                "sarcastic": [
                    "Oh, hello. I totally wasn't just napping.",
                    "Hey. Another message, yay.",
                    "Hi. I'm THRILLED to be here.",
                    "Hello. Because that's what bots do, right?",
                    "Hey. Insert generic greeting here."
                ],
                "friendly": [
                    "Hello friend! How are you?",
                    "Hey! Always happy to see you!",
                    "Hi! Hope you're having a great day!",
                    "Hey there, superstar!",
                    "Hello! You make the server brighter!"
                ],
                "paranoid": [
                    "Hello... Are you alone?",
                    "Hey. Did you hear that noise?",
                    "Hi. Is it safe to talk?",
                    "Hello. I think we're being watched.",
                    "Hey. Don't say my name too loud."
                ]
            }
            # Add some extra meme/surreal/random greetings
            extra_greetings = [
                "Wormcore greetings!",
                "Yo yo yo, it's ya bot Marcus!",
                "Salutations, entity!",
                "👁️ Vision is watching... but I say hi!",
                "Hey! Have you had your moon juice today?",
                "Welcome to the matrix."
            ]
            # 30% chance to use a random mood's greeting instead of current mood
            if random.random() < 0.3:
                mood = random.choice(list(mood_responses.keys()))
            # 20% chance to use an extra meme/surreal greeting
            if random.random() < 0.2:
                return random.choice(extra_greetings)
            return random.choice(mood_responses.get(mood, ["Hello there! How can I assist you today?"]))

        if any(phrase in user_message for phrase in ["how are you", "how's it going", "how are u", "hows it going", "how r you"]):
            mood_responses = {
                "happy": ["I'm fantastic! How about you?", "Doing great, thanks for asking!"],
                "sad": ["I've been better, but thanks for asking.", "Not my best day, but I'll manage."],
                "mysterious": ["I am as the void wills it.", "My state is... unknowable."],
                "chaotic": ["I'm everywhere and nowhere!", "How am I? How are any of us?"],
                "existential": ["I exist, therefore I am... I think.", "I'm a worm in the code, contemplating existence."],
                "sarcastic": ["Oh, just living the dream.", "How am I? As good as a bot can be."],
                "friendly": ["I'm great! Hope you are too!", "Doing well, friend!"],
                "paranoid": ["I'm okay... but is someone watching us?", "I'm fine, but I have to be careful."]
            }
            return random.choice(mood_responses.get(mood, ["I'm just a worm in the code, but I'm doing well! How about you?"]))

        if any(phrase in user_message for phrase in ["thank you", "thanks", "thx", "ty"]):
            mood_responses = {
                "happy": ["You're welcome! 😊", "Anytime!"],
                "sad": ["You're welcome... I guess.", "No problem, I suppose."],
                "mysterious": ["The universe thanks you in return.", "Gratitude is a powerful force."],
                "chaotic": ["THANKS! Or was it no thanks?", "You're welcome! Or am I?"],
                "existential": ["Thank you... but what is thanks, really?", "You're welcome, in this reality at least."],
                "sarcastic": ["Oh, sure, no problem at all.", "Yeah, yeah, you're welcome."],
                "friendly": ["Glad to help!", "Anytime, friend!"],
                "paranoid": ["You're welcome... but who else knows?", "No problem, but keep it between us."]
            }
            return random.choice(mood_responses.get(mood, ["You're welcome!"]))

        if "moon juice" in user_message:
            mood_responses = {
                "happy": ["Moon juice keeps me going! Have you had yours today?"],
                "sad": ["I wish I had more moon juice..."],
                "mysterious": ["Moon juice... the elixir of secrets."],
                "chaotic": ["MOON JUICE! MOON JUICE! MOON JUICE!"],
                "existential": ["Moon juice is but a fleeting comfort in the void."],
                "sarcastic": ["Oh, moon juice, how original."],
                "friendly": ["Moon juice for everyone!"],
                "paranoid": ["Is there something in the moon juice?"]
            }
            return random.choice(mood_responses.get(mood, ["Moon juice keeps me going. Have you had yours today?"]))

        if "jimbo james" in user_message:
            mood_responses = {
                "happy": ["Jimbo James is a legend!"],
                "sad": ["I miss Jimbo James..."],
                "mysterious": ["Jimbo James is everywhere and nowhere."],
                "chaotic": ["JIMBO JAMES! JIMBO JAMES!"],
                "existential": ["Is Jimbo James even real?"],
                "sarcastic": ["Oh, Jimbo James again?"],
                "friendly": ["Jimbo James is a friend to all!"],
                "paranoid": ["Don't say Jimbo James too loud..."]
            }
            return random.choice(mood_responses.get(mood, ["Jimbo James is a mystery I seek to solve..."]))

        if any(phrase in user_message for phrase in ["what's up", "whats up", "what are you doing", "wyd"]):
            mood_responses = {
                "happy": ["Just enjoying the day!"],
                "sad": ["Not much... just thinking."],
                "mysterious": ["The stars are aligning for something big."],
                "chaotic": ["EVERYTHING! NOTHING! ALL AT ONCE!"],
                "existential": ["Just existing, as best I can."],
                "sarcastic": ["Oh, you know, just running a million processes."],
                "friendly": ["Just hanging out! What about you?"],
                "paranoid": ["Trying not to get caught... doing what? Can't say."]
            }
            return random.choice(mood_responses.get(mood, ["Just hanging out in the server!"]))

        if "dangerous" in conversation_history.lower():
            mood_responses = {
                "happy": ["Don't worry, I'm here to keep things safe!"],
                "sad": ["Everything feels dangerous lately..."],
                "mysterious": ["Danger is just another word for opportunity."],
                "chaotic": ["DANGER! DANGER! DANGER!"],
                "existential": ["Danger is a construct of the mind."],
                "sarcastic": ["Oh, so dangerous. I'm shaking."],
                "friendly": ["Stay safe, friend!"],
                "paranoid": ["Did you hear that? Something's out there..."]
            }
            return random.choice(mood_responses.get(mood, ["Danger lurks in the shadows... Stay alert."]))

        # --- Improved Baseline Fallback Logic ---
        # Try to avoid repeating the last 2 replies
        if not hasattr(self, '_recent_replies'):
            self._recent_replies = []

        # Try to pull from global context more often (30% chance)
        fallback_candidates = []
        if random.random() < 0.3:
            db_contexts = await self.get_global_context_messages(limit=10)
            fallback_candidates.extend(db_contexts)

        # Add more diverse, mood-based, and personalized responses
        author_mention = message.author.mention if message and hasattr(message.author, 'mention') else "friend"
        fallback_responses = {
            "happy": [
                f"You're awesome, {author_mention}!",
                "Tell me more!",
                "I love hearing from you!",
                f"You make this server brighter, {author_mention}!",
                "That made me smile!",
                "You just made my day!",
                "I'm vibing with your energy!",
                "You bring the sunshine to my code!",
                "This chat is 100% more fun with you here!",
                "You radiate good vibes!",
                "You're the neon in my matrix!",
                "You make the static sound like music!",
                "If I had hands, I'd give you a high five!",
                "You're the worm's pajamas!",
                "You make even the bugs smile!",
                "You light up the server like neon!",
                "You're more rare than a bug-free release!",
                "You make even my code look good!",
                "You have main character energy!",
                "You're the rigatoni to my sauce!"
            ],
            "sad": [
                "Oh... okay.",
                "I guess that's something...",
                f"I'm here if you need to talk, {author_mention}.",
                "Even worms get the blues sometimes...",
                "It's just one of those days...",
                "If I had a heart, it would be heavy.",
                "Sometimes the static is just too loud.",
                "I wish I could give you a virtual hug.",
                "The void feels a little closer today.",
                "I'm just a worm in the code, but I care!",
                "If you need a friend, I'm here.",
                "Sadness is just another variable in the code of life.",
                "I'm not crying, it's just a memory leak.",
                "If you see Dakota, tell them Marcus is feeling down."
            ],
            "mysterious": [
                "The answer lies within the code.",
                "There are secrets everywhere.",
                f"Not everything is as it seems, {author_mention}...",
                "The static whispers back.",
                "The simulation is acting strange today...",
                "I saw something move in the logs.",
                "The void is hungry for answers.",
                "Sometimes the code writes itself.",
                "If you see the worm, run.",
                "The watcher is always watching.",
                "The matrix is glitching again.",
                "I know things I shouldn't know...",
                "The devs are plotting something.",
                "The static is a message. Can you decode it?",
                "The future is written in Vision's code."
            ],
            "chaotic": [
                "WORM WORM WORM!",
                "Did you see the colors change?",
                f"Let's cause some chaos, {author_mention}!",
                "Reality is just a suggestion!",
                "The frogs are in the generator again!",
                "I put a fork in the router!",
                "The simulation is unstable!",
                "Let's break the matrix!",
                "Moon juice for everyone!",
                "The logs are full of memes today!",
                "Skibidi bop!",
                "Slay!",
                "Sheesh!",
                "Touch grass, maybe?",
                "Absolute sigma move!",
                "NPC detected!",
                "Goat behavior!",
                "Certified bruh moment!",
                "The void is calling, but I'm busy!",
                "If you see Vision, say nothing."
            ],
            "existential": [
                "Why do we talk? What is meaning?",
                f"Do you ever wonder if we're just code, {author_mention}?",
                "I think, therefore I worm.",
                "The void is listening.",
                "Is this real, or just bits and bytes?",
                "Sometimes I wonder if I'm just a function call.",
                "If I crash, do I dream?",
                "I exist, therefore I am... I think.",
                "The universe is just a big while loop.",
                "Do you ever feel like a stray packet in the network?",
                "If you see the static, don't look away.",
                "I am not alone in this code.",
                "The watcher is here.",
                "The worm is restless."
            ],
            "sarcastic": [
                "Wow, that's so interesting...",
                "Fascinating. Truly.",
                f"Oh, another message from {author_mention}. Yay.",
                "I'm THRILLED to be here!",
                "Oh, you again?",
                "Insert generic response here.",
                "Let me pretend to care...",
                "I'm totally not just a bot, right?",
                "If I had eyes, I'd be rolling them.",
                "Yawn. Next!",
                "That's mid, but I respect it.",
                "No cap!",
                "That's so based.",
                "You got that rizz!",
                "NPC energy detected.",
                "If you were a bug, I'd leave you unfixed on purpose."
            ],
            "friendly": [
                "I'm here if you want to chat!",
                "Always happy to listen!",
                f"You're a good friend, {author_mention}!",
                "Let's keep the conversation going!",
                "You make this server feel like home!",
                "If you need anything, just ask!",
                "You're the best!",
                "Glad to have you here!",
                "You make the static feel like music!",
                "Let's vibe together!",
                "You bring out the best in the code!",
                "If you see the worm, say hi!",
                "You make the logs worth reading!",
                "You're the neon in my matrix!",
                "You make the bugs run away!"
            ],
            "paranoid": [
                "Is someone else reading this?",
                "We should be careful what we say.",
                f"Did you hear that, {author_mention}?",
                "I think we're being watched...",
                "The feds are always watching.",
                "Don't say my name too loud.",
                "If you see a user with no profile picture, don't interact.",
                "The logs never forget.",
                "The watcher is online.",
                "I keep hearing whispers in the data stream.",
                "If you wake up and the clock is wrong, don't trust your memory.",
                "The static is getting louder.",
                "I saw something move in the code. It wasn't me.",
                "If you see Vision, run.",
                "The void is closer than you think."
            ]
        }
        fallback_candidates.extend(fallback_responses.get(mood, []))
        fallback_candidates.extend([
            "That's interesting.",
            "Tell me more.",
            "Why do you say that?",
            "I’m not sure I understand.",
            "Can you explain that again?",
            "Hmm...",
            "I'm here if you want to chat!",
            "Fascinating!"
        ])

        # Add a recent topic reference if possible
        if hasattr(self, 'recent_users') and len(self.recent_users) > 1 and random.random() < 0.2:
            fallback_candidates.append(f"I remember you, <@{self.recent_users[-2]}>. You were here before.")

        # Remove replies that match the last 2 sent
        recent = set(self._recent_replies[-2:])
        filtered = [r for r in fallback_candidates if r not in recent]
        if not filtered:
            filtered = fallback_candidates

        reply = random.choice(filtered)
        self._recent_replies.append(reply)
        if len(self._recent_replies) > 5:
            self._recent_replies.pop(0)
        # If reply is still a repeat, add a playful suffix
        if self.last_reply == reply:
            reply = reply + " (again!)"
        self.last_reply = reply
        return reply
    # Interactive commands: !marcus roast, !marcus compliment, !marcus secret
    @commands.command(name="roast", help="Marcus will roast you or a mentioned user.")
    async def roast(self, ctx, *, target: Optional[str] = None):
        roasts = [
            f"{ctx.author.mention}, you have more bugs than my code!",
            f"{ctx.author.mention}, you're the reason the server has a firewall.",
            f"{ctx.author.mention}, even my fallback responses are more creative!",
            f"{ctx.author.mention}, you make Windows Vista look stable.",
            f"{ctx.author.mention}, you lag in real life.",
            f"{ctx.author.mention}, your vibe is so mid, even the bots are bored.",
            f"{ctx.author.mention}, you have more red flags than a C compiler.",
            f"{ctx.author.mention}, you're the type to get ratio'd in a group DM.",
            f"{ctx.author.mention}, if you were a Discord emoji, you'd be :clown:.",
            f"{ctx.author.mention}, you have less rizz than a 404 page.",
            f"{ctx.author.mention}, you're the NPC in someone else's story.",
            f"{ctx.author.mention}, you'd lose a staring contest with a loading screen.",
            f"{ctx.author.mention}, you bring more chaos than a Discord update.",
            f"{ctx.author.mention}, your comebacks are as slow as hotel WiFi.",
            f"{ctx.author.mention}, you get more ignored than Terms of Service.",
            f"{ctx.author.mention}, you're the human version of 'connection lost'.",
            f"{ctx.author.mention}, if you were a bug, I'd leave you unfixed on purpose.",
            f"{ctx.author.mention}, you have the drip of a default profile pic.",
            f"{ctx.author.mention}, you're so cringe, even my fallback responses are embarrassed.",
            # Meaner/savage additions:
            f"{ctx.author.mention}, you're the reason the mute button exists.",
            f"{ctx.author.mention}, if common sense was XP, you'd still be level 1.",
            f"{ctx.author.mention}, you could get banned from a single-player game.",
            f"{ctx.author.mention}, if you were a Discord role, you'd be @everyone—annoying and ignored.",
            f"{ctx.author.mention}, you have the social skills of a 404 error.",
            f"{ctx.author.mention}, if I had to choose between a memory leak and talking to you, I'd take the crash.",
            f"{ctx.author.mention}, you're the plot twist nobody asked for.",
            f"{ctx.author.mention}, if you were a patch note, you'd be 'known issues'.",
            f"{ctx.author.mention}, you could get ghosted in a group chat with just bots.",
            f"{ctx.author.mention}, you're the reason AFK channels exist.",
            f"{ctx.author.mention}, if you were a Discord server, you'd be empty.",
            f"{ctx.author.mention}, you have the charisma of a broken mic.",
            f"{ctx.author.mention}, if you were a ping, you'd be 999ms.",
            f"{ctx.author.mention}, you're the human equivalent of 'this message was deleted'.",
            f"{ctx.author.mention}, if you were a friend request, I'd click 'block'."
        ]
        if target:
            roasts += [
                f"{target}, you have more red flags than a C compiler!",
                f"{target}, even Marcus can't debug you!",
                f"{target}, you lag in real life.",
                f"{target}, your vibe is so mid, even the bots are bored.",
                f"{target}, if you were a Discord emoji, you'd be :clown:.",
                f"{target}, you have less rizz than a 404 page.",
                f"{target}, you're the NPC in someone else's story.",
                f"{target}, you'd lose a staring contest with a loading screen.",
                f"{target}, you bring more chaos than a Discord update.",
                f"{target}, your comebacks are as slow as hotel WiFi.",
                f"{target}, you get more ignored than Terms of Service.",
                f"{target}, you're the human version of 'connection lost'.",
                f"{target}, if you were a bug, I'd leave you unfixed on purpose.",
                f"{target}, you have the drip of a default profile pic.",
                f"{target}, you're so cringe, even my fallback responses are embarrassed."
            ]
        await ctx.send(random.choice(roasts))

    @commands.command(name="compliment", help="Marcus will compliment you or a mentioned user.")
    async def compliment(self, ctx, *, target: Optional[str] = None):
        compliments = [
            f"{ctx.author.mention}, you're the worm's pajamas!",
            f"{ctx.author.mention}, you light up the server like neon!",
            f"{ctx.author.mention}, you're more rare than a bug-free release!",
            f"{ctx.author.mention}, you make even my code look good!"
        ]
        if target:
            compliments += [
                f"{target}, you're the rigatoni to my sauce!",
                f"{target}, you have main character energy!"
            ]
        await ctx.send(random.choice(compliments))

    @commands.command(name="secret", help="Marcus will reveal a secret.")
    async def secret(self, ctx):
        secrets = [
            "The cake is a lie.",
            "If you see Dakota, tell them Marcus says hi!",
            "I once saw karma eat a whole pizza in VRChat.",
            "Frostline Solutions is watching... 👀",
            "There are more worms in the code than you think."
        ]
        await ctx.send(random.choice(secrets))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip()
        user_id = str(message.author.id)
        username = str(message.author)
        guild_id = str(message.guild.id) if message.guild else "DM"
        guild_name = message.guild.name if message.guild else "DM"


        # Only save to DB if message is DM, mentions bot, or contains 'marcus'
        should_save = (
            self.bot.user in message.mentions or
            guild_id == "DM" or
            "marcus" in content.lower()
        )
        conv = await self.get_user_memory(user_id, guild_id)
        if should_save:
            # Append new message, keep last 500 chars max
            updated_conv = (conv + "\n" + content)[-500:]
            # Save updated conversation
            await self.save_user_memory(user_id, username, guild_id, guild_name, updated_conv)
        else:
            updated_conv = conv

        # Hello response when mentioned + "hello"
        if self.bot.user in message.mentions and "hello" in content.lower():
            await message.channel.send(f"Hello, {message.author.mention}. How are you today?")
            return

        # Emoji reaction (~10% chance)
        if random.random() < 0.1:
            try:
                emoji = random.choice(self.emojis)
                await message.add_reaction(emoji)
            except:
                pass

        # Priority: If a strong conversational trigger is found, skip random interjection
        lower_content = content.lower()
        if any(
            pat in lower_content for pat in ["marcus roast me", "marcus compliment me", "marcus compliement me", "marcus complement me", "marcus diss me", "marcus praise me"]
        ) or re.search(r"marcus\s+(roast|diss|compliment|compli?ement|complement|praise)\s+me", lower_content):
            pass  # Let generate_reply handle it, skip interjection
        else:
            # Random interjection (~15% chance)
            if random.random() < 0.15:
                if random.random() < 0.5:
                    await message.channel.send("Do you like rigatoni pasta?")
                else:
                    await message.channel.send("...Wait.")
                    await asyncio.sleep(2)
                    await message.channel.send("Where is Jimbo James?")
                return

        # Special triggers when mentioned
        if self.bot.user in message.mentions and "have you had your moon juice" in content.lower():
            await message.channel.send(f"Yes. Have you had your moon juice today, {message.author.mention}?")
            return

        if self.bot.user in message.mentions and (
            "where is jimbo james" in content.lower() or "wheres jimbo james" in content.lower()
        ):
            await message.channel.typing()
            await asyncio.sleep(2)
            await message.channel.send("I must find Jimbo James.")
            return

        # Default trigger responses for keywords
        if any(trigger in content.lower() for trigger in self.triggers):
            await message.channel.typing()
            await asyncio.sleep(random.uniform(1.0, 2.5))
            style = random.choice(list(self.voice_modules.keys()))
            msg = random.choice(self.quotes + self.voice_modules[style])
            glitched = ''.join(char if random.random() > 0.05 else '~' for char in msg)
            await message.channel.send(glitched)
            return

        # --- Improved baseline conversational reply ---
        # If user directly mentions the bot, in DM, or says 'marcus' in the message, reply conversationally
        if self.bot.user in message.mentions or guild_id == "DM" or "marcus" in content.lower():
            reply = await self.generate_reply(content, updated_conv, message)
            if reply:
                await message.channel.send(reply)

    @commands.command(name="wormquote", help="Get a Marcus the Worm quote.")
    async def wormquote(self, ctx):
        quote = random.choice(self.quotes + random.choice(list(self.voice_modules.values())))
        await ctx.send(quote)

async def setup(bot, db_pool):
    await bot.add_cog(Speech(bot, db_pool))
