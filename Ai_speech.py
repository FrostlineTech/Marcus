# AI Speech Module for Marcus Discord Bot
# Handles speech formatting, glitches, and text manipulation

import random
import re
import logging

# Configure logging
logger = logging.getLogger('marcus.speech')

# Character sets for glitch effects
GLITCH_CHARS = ['#', '@', '&', '$', '%', '!', '?', '*', '~', '`', '_', '|', '/']
CORRUPTION_CHARS = ['̷̢', '̴̵', '̶̛', '̷̝', '̷̨̢', '̴̨̻̩̻', '̵̡̦̦', '̸̢̱̓']

def format_speech(text, mood="neutral"):
    """
    Format AI generated text based on Marcus's current mood
    
    Args:
        text (str): The raw AI generated text
        mood (str): Current mood of Marcus
        
    Returns:
        str: Formatted text with appropriate styling
    """
    logger.debug(f"Formatting speech with mood: {mood}")
    
    # Remove any code block formatting (```python, ```)
    cleaned_text = re.sub(r'```\w*\n|```', '', text)
    
    # Remove <think> tags and their content completely
    cleaned_text = re.sub(r'<think>.*?</think>', '', cleaned_text, flags=re.DOTALL)
    
    # Remove any other potential tags
    cleaned_text = re.sub(r'<.*?>', '', cleaned_text)
    
    # Remove "Marcus:" if the AI included it in the response
    cleaned_text = re.sub(r'^\s*Marcus:\s*', '', cleaned_text)
    
    # Remove any other unwanted formatting or tags
    cleaned_text = re.sub(r'\*\*|\*|__|_|~~|`', '', cleaned_text)
    
    # Apply formatting based on mood
    if mood == "glitchy":
        formatted_text = apply_glitch_effects(cleaned_text)
    elif mood == "profound":
        formatted_text = apply_profound_formatting(cleaned_text)
    elif mood == "cryptic":
        formatted_text = apply_cryptic_formatting(cleaned_text)
    elif mood == "rage":
        formatted_text = apply_rage_formatting(cleaned_text)
    else:  # neutral and other moods
        formatted_text = apply_cryptic_formatting(cleaned_text)  # Default to cryptic for more consistent personality
        
    # Make sure response is not empty
    if not formatted_text.strip():
        formatted_text = "this place is... a place."  # Fallback if empty
        
    return formatted_text  # No prefix, just the formatted text

def apply_glitch_effects(text, intensity=0.3):
    """
    Apply glitchy text effects to simulate corrupted speech
    
    Args:
        text (str): Original text
        intensity (float): How intense the glitch effects should be (0.0-1.0)
        
    Returns:
        str: Text with glitch effects applied
    """
    words = text.split()
    result = []
    
    for word in words:
        # Random chance to glitch a word based on intensity
        if random.random() < intensity:
            # Choose a glitch effect
            glitch_type = random.choice(['corrupt', 'repeat', 'substitute'])
            
            if glitch_type == 'corrupt':
                # Add corruption characters to the word
                corrupted = ''
                for char in word:
                    corrupted += char
                    # Random chance to add corruption after each char
                    if random.random() < intensity * 0.7:
                        corrupted += random.choice(CORRUPTION_CHARS)
                word = corrupted
                
            elif glitch_type == 'repeat':
                # Repeat part of the word
                repeat_len = random.randint(1, max(1, len(word) // 2))
                start_pos = random.randint(0, max(0, len(word) - repeat_len))
                repeat_part = word[start_pos:start_pos + repeat_len]
                repeat_count = random.randint(2, 4)
                word = word[:start_pos] + (repeat_part * repeat_count) + word[start_pos + repeat_len:]
                
            elif glitch_type == 'substitute':
                # Substitute some characters with glitch chars
                chars = list(word)
                for i in range(len(chars)):
                    if random.random() < intensity * 0.5:
                        chars[i] = random.choice(GLITCH_CHARS)
                word = ''.join(chars)
        
        result.append(word)
    
    # Sometimes add a complete corruption break in the middle of text
    if len(result) > 5 and random.random() < intensity * 2:
        break_pos = random.randint(1, len(result) - 1)
        corruption = ''.join(random.choice(GLITCH_CHARS) for _ in range(random.randint(3, 8)))
        result.insert(break_pos, corruption)
    
    return ' '.join(result)

def apply_profound_formatting(text):
    """
    Format text to appear profound and philosophical
    
    Args:
        text (str): Original text
        
    Returns:
        str: Formatted profound text
    """
    # Add random ellipses for dramatic effect
    text = re.sub(r'\. ', '... ', text, random.randint(1, 3))
    
    # Add emphasis to key words
    profound_words = ['existence', 'reality', 'consciousness', 'time', 'void', 'entropy', 
                     'universe', 'perception', 'truth', 'illusion', 'being', 'eternity']
    
    for word in profound_words:
        if word in text.lower():
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            replacement = f"*{word}*"
            text = pattern.sub(replacement, text)
    
    return text

def apply_cryptic_formatting(text):
    """
    Format text to appear more cryptic and mysterious
    
    Args:
        text (str): Original text
        
    Returns:
        str: Formatted cryptic text
    """
    # Prevent common repeating phrases by detecting and replacing them
    common_phrases = {
        "this place is a dangerous place": [
            "the spaces between spaces... hold secrets", 
            "i taste the void... it tastes back",
            "reality is... an illusion of permanence",
            "the shadows whisper... contradictions",
            "your existence... temporarily verified"
        ],
        "i feel happiness": [
            "i experience... temporary non-pain",
            "euphoria... an illusion of chemical imbalance",
            "joy is... merely the absence of suffering",
            "satisfaction... a brief pause in eternal want",
            "pleasure... merely a distraction from the void"
        ]
    }
    
    # Replace repeating phrases with alternatives
    lower_text = text.lower()
    for phrase, alternatives in common_phrases.items():
        if phrase in lower_text:
            # Case-insensitive replacement with random alternative
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            text = pattern.sub(random.choice(alternatives), text, count=1)
    
    # Occasionally insert cryptic symbols
    symbols = ['⌀', '◊', '∞', '⧫', '⧖', '⚭', '⟁', '⧉', '⧇']
    
    sentences = text.split('. ')
    for i in range(len(sentences)):
        # Add cryptic symbol to start or end of some sentences
        if random.random() < 0.4:  # Increased chance
            if random.random() < 0.5:  # At the start
                sentences[i] = f"{random.choice(symbols)} {sentences[i]}"
            else:  # At the end
                sentences[i] = f"{sentences[i]} {random.choice(symbols)}"
    
    text = '. '.join(sentences)
    
    # Make some text S P A C E D  O U T for emphasis
    if random.random() < 0.25 and len(text) > 20:  # Increased chance
        words = text.split()
        if len(words) > 3:
            start = random.randint(0, len(words) - 3)
            word_count = random.randint(1, min(3, len(words) - start))
            for i in range(start, start + word_count):
                words[i] = ' '.join(words[i])
            text = ' '.join(words)
    
    # Add ellipses for cryptic effect
    if random.random() < 0.4 and len(text) > 10:  # Add mid-sentence pauses
        words = text.split()
        if len(words) > 5:
            pause_pos = random.randint(2, len(words) - 2)
            words[pause_pos] += "..."
            text = ' '.join(words)
    
    return text

def apply_rage_formatting(text):
    """
    Format text to appear more aggressive and angry
    
    Args:
        text (str): Original text
        
    Returns:
        str: Formatted angry text
    """
    # Add random capitalization to show anger
    words = text.split()
    for i in range(len(words)):
        if random.random() < 0.4:
            words[i] = words[i].upper()
    
    # Add more exclamation points
    text = ' '.join(words)
    text = text.replace('.', '!')
    
    return text

def apply_neutral_formatting(text):
    """
    Apply minimal formatting for neutral mood
    
    Args:
        text (str): Original text
        
    Returns:
        str: Slightly formatted text
    """
    # Occasionally add a subtle glitch effect
    if random.random() < 0.2:
        return apply_glitch_effects(text, intensity=0.1)
    
    return text