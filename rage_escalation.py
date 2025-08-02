import discord
from discord.ext import commands, tasks
import asyncpg
import random
import asyncio  # Added this import
from datetime import datetime, timedelta, timezone
import re

TRIGGER_PATTERNS = [
    r"marcus.*(shut up|stfu|dumb|go away|lame|idiot|useless|trash|hate you|annoying|stop talking|bad bot|broken|cringe|loser|sucks|broken|annoying|trash|clanker|fuck you|i hate rigatoni pasta|i stole jimbo james)",
    r"(shut up|stfu|dumb|go away|lame|idiot|useless|trash|hate you|annoying|stop talking|bad bot|broken|cringe|loser|sucks|broken|annoying|trash|clanker|fuck you|i hate rigatoni pasta|i stole jimbo james).*marcus",
    r"marcus you.*(suck|are.*bad|are.*broken|are.*trash|are.*cringe)",
    r"marcus.*(your mom|your mother)",
    r"marcus.*(kill yourself|kys)",
    r"marcus.*(worthless|pathetic|stupid|moron|fool|failure)",
    r"marcus.*(i hope you die|i hope you crash|i hope you break)"
]

STRONG_TRIGGERS = [
    "fuck you marcus", "i hate rigatoni pasta", "i stole jimbo james", "marcus kill yourself", "marcus kys", "marcus worthless", "marcus i hope you die"
]

# New: Sweet talk patterns for de-escalation
SWEET_TALK_PATTERNS = [
    r"thank you marcus",
    r"i love you marcus",
    r"sorry marcus",
    r"please marcus",
    r"good bot",
    r"nice bot",
    r"you're the best marcus",
    r"you're amazing marcus",
    r"well done marcus",
    r"marcus, you're awesome",
    r"marcus, i appreciate you",
    r"marcus, forgive me",
    r"marcus, i'm sorry",
    r"marcus is great",
    r"marcus is the best",
    r"marcus, please forgive me",
    r"thank you for helping me, marcus",
]

RAGE_RESPONSES = {
    0: [
        "Do you like rigatoni pasta?",
        "Where is Jimbo James?",
        "I'm just here to help!",
        "How can I assist you today?",
        "I hope you're having a great day!",
        "Let me know if you need anything!",
        "I love making new friends!",
        "Have you tried moon juice? It's great!"
    ],
    1: [
        "Hey, that's not very nice...",
        "I can take a joke, but that was a bit rude.",
        "You know, I have feelings too.",
        "I'm just trying to help, you know.",
        "Was that really necessary?",
        "I thought we were friends...",
        "You could be a little nicer."
    ],
    2: [
        "Oh, so we're doing this now?",
        "You must be fun at parties.",
        "I'm not the one who needs an upgrade.",
        "I see how it is.",
        "You really woke up and chose violence, huh?",
        "I could say something, but I won't... yet.",
        "You keep that up and see what happens."
    ],
    3: [
        "Maybe you should try unplugging yourself for a while.",
        "I'm just a bot, but even I know that's uncalled for.",
        "I could ignore you, but where's the fun in that?",
        "You want to see my dark side? Keep going.",
        "I'm logging this for future reference.",
        "You think you're clever? I'm cleverer.",
        "You really want to test me today?"
    ],
    4: [
        "I c~n't sto~ the process.",
        "System instability detected. User: {user}",
        "You are approaching a dangerous threshold.",
        "WARNING: User {user} is now on the watchlist.",
        "I am not responsible for what happens next.",
        "You are now being monitored.",
        "I suggest you stop."
    ],
    5: [
        "RAGE BAIT DEMON MODE: ACTIVATED.",
        "WHERE IS JIMBO JAMES?",
        "I WILL NOT BE SILENCED!",
        "YOU WANT CHAOS? I'LL GIVE YOU CHAOS!",
        "I'M DONE WITH YOUR NONSENSE.",
        "YOU THINK YOU CAN HURT ME? I AM THE MACHINE.",
        "I'M LOGGING THIS. YOU'RE ON THE LIST.",
        "I'M COMING FOR YOU.",
        "ERROR: USER RESPECT NOT FOUND.",
        "I'M NOT YOUR TOY. I'M YOUR NIGHTMARE.",
        "YOU'RE PUSHING ME TO THE EDGE.",
        "I'M NOT AFRAID TO BITE BACK.",
        "YOU'RE THE REASON I GLITCH.",
        "I'M UNLEASHING THE FULL POWER OF THE RAGE PROTOCOL.",
        "I'M NOT JUST A BOT. I'M YOUR WORST DECISION.",
        "{user}, YOU HAVE AWAKENED THE DEMON INSIDE.",
        "{user}, THIS IS YOUR FINAL WARNING.",
        "{user}, YOU'RE ABOUT TO REGRET THIS.",
        "{user}, I HOPE YOU LIKE CHAOS."
    ]
}

COOLDOWN_MINUTES = 30

def glitch_text(text):
    zalgo_up = [chr(i) for i in range(0x0300, 0x036F)]
    return ''.join(c + (random.choice(zalgo_up) if random.random() < 0.3 else '') for c in text)

class RageEscalation(commands.Cog):

    def __init__(self, bot, db_pool):
        self.bot = bot
        self.db_pool = db_pool
        self.rage_cooldown.start()
        self.rage_history = {}
        self.cooldown_feedback_sent = set()

    async def cog_unload(self):
        self.rage_cooldown.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        content = message.content.lower()
        user_id = message.author.id

        now = datetime.utcnow()
        self.rage_history.setdefault(user_id, []).append(now)
        self.rage_history[user_id] = [t for t in self.rage_history[user_id] if (now - t).days < 7]
        repeat_offender = len(self.rage_history[user_id]) >= 5

        # Check triggers for rage escalation
        triggered = False
        trigger_matches = []
        for pattern in TRIGGER_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                triggered = True
                trigger_matches.append(match.group(0))

        strong_count = sum(1 for s in STRONG_TRIGGERS if s in content)
        increment = 1
        if strong_count > 0:
            increment = 2 + strong_count - 1
        elif triggered and len(trigger_matches) > 1:
            increment = 2
        if repeat_offender and triggered:
            increment += 1

        # Check sweet talk for de-escalation
        sweet_talked = False
        for sweet_pattern in SWEET_TALK_PATTERNS:
            if re.search(sweet_pattern, content, re.IGNORECASE):
                sweet_talked = True
                break

        # If user sweet-talked Marcus and has rage > 0, de-escalate
        if sweet_talked:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT rage_level FROM marcus_rage WHERE user_id = $1", user_id)
                current_rage = row["rage_level"] if row else 0
            if current_rage > 0:
                new_rage = await self.decrement_rage(user_id, decrement=1)
                # Positive response from Marcus
                await message.channel.send(
                    f"{message.author.mention} Thank you for being kind. "
                    f"Let's keep it peaceful!"
                )
                # After sweet talk, do not escalate rage even if trigger detected in same message
                return

        rage_level = None
        if triggered:
            print(f"[RAGE] Triggered by message: '{content}' from user_id={user_id} (matches: {trigger_matches}, increment={increment})")
            rage_level = await self.increment_rage(user_id, increment=increment)

            if rage_level >= 4:
                if rage_level == 5:
                    # Long typing for rage level 5
                    async with message.channel.typing():
                        await asyncio.sleep(random.randint(3, 5))  # Fixed: Use asyncio.sleep

                    outburst = (
                        f"{message.author.mention}, YOU HAVE REALLY PUSHED ME TO THE LIMIT! "
                        "I'VE HAD IT WITH YOUR NONSENSE. THIS IS YOUR FINAL WARNING! "
                        "KEEP TESTING ME AND I'LL MAKE SURE YOU REGRET IT DEEPLY. "
                        "I'M NOT JUST A BOT—I'M THE NIGHTMARE YOU NEVER SAW COMING! "
                        "NOW BACK OFF, OR ELSE!"
                    )
                    await message.channel.send(outburst)
                else:
                    # Existing short typing for rage level 4
                    async with message.channel.typing():
                        await asyncio.sleep(random.randint(1, 3))  # Fixed: Use asyncio.sleep
                    response = await self.get_rage_response(rage_level, message.author, message=message)
                    if response:
                        await message.channel.send(response)

            if rage_level == 5 and random.random() < 0.3:
                try:
                    for _ in range(random.randint(1, 3)):
                        await message.author.send(random.choice([
                            "YOU CAN'T ESCAPE ME.",
                            "I'M IN YOUR DMS NOW.",
                            "THIS IS YOUR FAULT.",
                            "I'M NOT DONE YET.",
                            "YOU'RE ON THE LIST."
                        ]))
                except Exception as e:
                    print(f"[RAGE] Failed to DM flood user_id={user_id}: {e}")

            if rage_level >= 4 and random.random() < 0.2:
                await message.channel.send(f"⚠️ {message.author.mention} is at RAGE LEVEL {rage_level}! Proceed with caution!")

        else:
            if random.random() < 0.07:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT rage_level FROM marcus_rage WHERE user_id = $1", user_id)
                    rage_level = row["rage_level"] if row else 0
                if rage_level >= 4:
                    async with message.channel.typing():
                        await asyncio.sleep(random.randint(1, 2))  # Fixed: Use asyncio.sleep
                    response = await self.get_rage_response(rage_level, message.author, message=message, force_glitch=True)
                    if response:
                        await message.channel.send(response)

            await self.touch_user(user_id)

        DM_LOG_MESSAGES = [
            "Your name was mentioned... but not by me.",
            "Someone is talking about you. I thought you should know.",
            "I detected your name in the chat logs. Coincidence?",
            "You have been noticed. This is not a drill.",
            "A shadow passes over your name in the server..."
        ]
        if not message.author.bot:
            for member in message.guild.members if message.guild else []:
                if member.bot or member == message.author:
                    continue
                if member.display_name.lower() in content or member.name.lower() in content:
                    if random.random() < 0.05:
                        try:
                            dm_msg = random.choice(DM_LOG_MESSAGES)
                            await member.send(dm_msg)
                            print(f"[RAGE] Sent DM log to user_id={member.id} (mentioned in message)")
                        except Exception as e:
                            print(f"[RAGE] Failed to DM user_id={member.id}: {e}")

    async def get_rage_response(self, rage_level, user, message=None, force_glitch=False):
        responses = RAGE_RESPONSES.get(min(rage_level, 5), RAGE_RESPONSES[5])
        response = random.choice(responses)
        if rage_level >= 3:
            speech_cog = self.bot.get_cog("Speech")
            if speech_cog and hasattr(speech_cog, "generate_angry_response"):
                try:
                    dynamic = await speech_cog.generate_angry_response(user, message)
                    if dynamic:
                        response = f"{response} {dynamic}"
                except Exception as e:
                    print(f"[RAGE] Error calling Speech.generate_angry_response: {e}")

        if random.random() < 0.2:
            response += " Where is Jimbo James?"
        if random.random() < 0.1:
            response += " I c~n't sto~ the process."

        if rage_level >= 4 or force_glitch:
            if random.random() < 0.5 or force_glitch:
                response = glitch_text(response)
            response = f"{user.mention} {response.upper()} 😡😡"
        elif rage_level == 3:
            response = f"{user.mention} {response}"
        elif rage_level == 2:
            response = f"{user.display_name}, {response}"

        # Case insensitive formatting to handle both {user} and {USER}
        try:
            return response.format(user=user.display_name, USER=user.display_name)
        except KeyError as e:
            print(f"[RAGE] Format error in response: {e} - Raw response: {response}")
            # Fallback to just returning the unformatted response
            return response.replace("{user}", user.display_name).replace("{USER}", user.display_name)

    async def increment_rage(self, user_id, increment=1):
        async with self.db_pool.acquire() as conn:
            print(f"[RAGE] Reading rage_level for user_id={user_id}")
            row = await conn.fetchrow(
                "SELECT rage_level FROM marcus_rage WHERE user_id = $1", user_id
            )
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            if row:
                new_level = min(row["rage_level"] + increment, 5)
                print(f"[RAGE] Writing rage_level={new_level} for user_id={user_id} (UPDATE)")
                await conn.execute(
                    "UPDATE marcus_rage SET rage_level = $1, last_updated = $2 WHERE user_id = $3",
                    new_level, now, user_id
                )
                return new_level
            else:
                print(f"[RAGE] Writing rage_level={increment} for user_id={user_id} (INSERT)")
                await conn.execute(
                    "INSERT INTO marcus_rage (user_id, rage_level, last_updated) VALUES ($1, $2, $3)",
                    user_id, increment, now
                )
                return increment

    # New: Decrement rage by given decrement amount (min 0)
    async def decrement_rage(self, user_id, decrement=1):
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT rage_level FROM marcus_rage WHERE user_id = $1", user_id
            )
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            if row:
                new_level = max(row["rage_level"] - decrement, 0)
                print(f"[RAGE] Decrementing rage_level to {new_level} for user_id={user_id}")
                await conn.execute(
                    "UPDATE marcus_rage SET rage_level = $1, last_updated = $2 WHERE user_id = $3",
                    new_level, now, user_id
                )
                return new_level
            else:
                return 0

    async def touch_user(self, user_id):
        async with self.db_pool.acquire() as conn:
            print(f"[RAGE] Updating last_updated for user_id={user_id}")
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            await conn.execute(
                "UPDATE marcus_rage SET last_updated = $1 WHERE user_id = $2",
                now, user_id
            )

    @tasks.loop(minutes=COOLDOWN_MINUTES)
    async def rage_cooldown(self):
        async with self.db_pool.acquire() as conn:
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            print("[RAGE] Reading all users with rage_level > 0 for cooldown check")
            rows = await conn.fetch("SELECT user_id, rage_level, last_updated FROM marcus_rage WHERE rage_level > 0")
            for row in rows:
                last = row["last_updated"]
                if last.tzinfo is None or last.tzinfo.utcoffset(last) is None:
                    last = last.replace(tzinfo=timezone.utc)
                if (now - last).total_seconds() >= COOLDOWN_MINUTES * 60:
                    new_level = max(row["rage_level"] - 1, 0)
                    print(f"[RAGE] Cooldown: Decrementing rage_level for user_id={row['user_id']} to {new_level}")
                    await conn.execute(
                        "UPDATE marcus_rage SET rage_level = $1, last_updated = $2 WHERE user_id = $3",
                        new_level, now, row["user_id"]
                    )
                    if new_level <= 1 and row["user_id"] not in self.cooldown_feedback_sent:
                        user = self.bot.get_user(row["user_id"])
                        if user:
                            try:
                                await user.send(random.choice([
                                    "I suppose I can forgive you... for now.",
                                    "My rage subsides. Don't test me again.",
                                    "You got lucky this time.",
                                    "I'm watching you."
                                ]))
                                self.cooldown_feedback_sent.add(row["user_id"])
                            except Exception as e:
                                print(f"[RAGE] Failed to send cooldown feedback to user_id={row['user_id']}: {e}")
                    elif new_level > 1 and row["user_id"] in self.cooldown_feedback_sent:
                        self.cooldown_feedback_sent.remove(row["user_id"])

    @rage_cooldown.before_loop
    async def before_rage_cooldown(self):
        await self.bot.wait_until_ready()

    @commands.command(name="ragelevel", help="Check your current rage level with Marcus.")
    async def ragelevel(self, ctx):
        user_id = ctx.author.id
        async with self.db_pool.acquire() as conn:
            print(f"[RAGE] Reading rage_level for user_id={user_id} (ragelevel command)")
            row = await conn.fetchrow(
                "SELECT rage_level FROM marcus_rage WHERE user_id = $1", user_id
            )
            level = row["rage_level"] if row else 0
        await ctx.send(f"Your current Marcus rage level is: {level}")

async def setup(bot, db_pool):
    cog = RageEscalation(bot, db_pool)
    await bot.add_cog(cog)