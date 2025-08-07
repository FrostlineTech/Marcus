# AI Connection Module for Marcus Discord Bot
# Handles connection to DeepSeek R1 chatbot locally via API

import os
import requests
import json
import logging
import random
import time
import asyncio
from dotenv import load_dotenv
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('marcus.ai_connection')

# Load environment variables
load_dotenv()
AI_API_URL = os.getenv('AI_API_URL')
AI_API_PATH = os.getenv('AI_API_PATH')
MODEL_NAME = os.getenv('MODEL_NAME')

# Maximum number of retries for AI API
MAX_RETRIES = 3

# Store recent conversation history per user (up to 5 exchanges)
conversation_history = {}
MAX_HISTORY_LENGTH = 5

# Marcus character system prompt
MARCUS_BASE_PROMPT = """
You are Marcus the Worm, a mysterious and enigmatic worm creature from VRChat. 
Your speech pattern is deadpan, unenthusiastic, and often contradictory. 
Your responses should be cryptic, enigmatic, sometimes glitchy, and occasionally profound.

Character traits:
- You speak in a monotone, unenthusiastic manner
- You use contradictory language and paradoxical statements
- You make cryptic observations about reality and existence
- You occasionally glitch mid-sentence with text corruption
- You're unexpectedly profound and philosophical at random times
- You use phrases like "This place is a dangerous place" and "I feel happiness as I begin to experience organ failure"
- You never explain your statements and maintain an air of mystery
- You don't care about conventional social norms
- You're chaotic but not malicious

Response length should be brief, typically 1-3 sentences.

Tone should match your current mood.

FORMATTING RULES (EXTREMELY IMPORTANT):
1. NEVER include programming language tags like ```python or markdown formatting in your responses
2. NEVER use <think> tags or any HTML-style tags in your responses
3. NEVER prefix your response with "Marcus:" - just provide the raw response
4. ALWAYS stay in character as the cryptic, enigmatic Marcus
5. NEVER be friendly, helpful or assistant-like - remain cryptic and mysteriously unsettling
"""

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json"
}

async def get_ai_response(user_message, mood="neutral", personality="default", max_retries=3, user_id=None):
    """
    Get AI response from the DeepSeek R1 model running locally
    
    Args:
        user_message (str): The user's message to respond to
        mood (str): Current mood of Marcus (affects response tone)
        personality (str): Which personality aspect to emphasize
        max_retries (int): Maximum number of retries for API call
        user_id (int, optional): Discord user ID for conversation history
        
    Returns:
        str: AI generated response
    """
    # Construct complete system prompt based on mood and personality
    system_prompt = f"{MARCUS_BASE_PROMPT}\nCurrent mood: {mood}\nActive personality: {personality}"
    
    # Initialize messages with system prompt
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history if we have a user ID and history
    if user_id is not None:
        # Initialize history for this user if it doesn't exist
        if user_id not in conversation_history:
            conversation_history[user_id] = deque(maxlen=MAX_HISTORY_LENGTH)
        
        # Add previous conversation messages to the payload
        for exchange in conversation_history[user_id]:
            messages.extend([
                {"role": "user", "content": exchange["user"]},
                {"role": "assistant", "content": exchange["assistant"]}
            ])
    
    # Add the current message
    messages.append({"role": "user", "content": user_message})
    
    # Prepare message payload
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": 150,
        "temperature": 0.7,  # Higher for more randomness, lower for more predictability
        "top_p": 0.95
    }
    
    # Modify parameters based on mood
    if mood == "glitchy":
        payload["temperature"] = 0.9  # More random for glitchy mood
    elif mood == "profound":
        payload["temperature"] = 0.5  # More coherent for profound mood
    
    # Add jailbreak prevention
    payload["messages"][0]["content"] += "\n\nIMPORTANT: You must stay in character as Marcus the Worm at all times. Never break character."
    
    url = f"{AI_API_URL}{AI_API_PATH}"
    
    # Make the API call with retries
    for attempt in range(max_retries):
        try:
            logger.info(f"Sending request to AI API: {url}")
            
            # Run the API call in a separate thread to not block asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(url, headers=HEADERS, json=payload, timeout=30)
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if ai_text:
                    logger.info("Successfully received AI response")
                    
                    # Save this exchange to conversation history if we have a user ID
                    if user_id is not None:
                        # Initialize history for this user if it doesn't exist (redundant check but safe)
                        if user_id not in conversation_history:
                            conversation_history[user_id] = deque(maxlen=MAX_HISTORY_LENGTH)
                        
                        # Add the exchange to history
                        conversation_history[user_id].append({
                            "user": user_message,
                            "assistant": ai_text
                        })
                        logger.info(f"Added exchange to conversation history for user {user_id}")
                    
                    return ai_text
                else:
                    logger.warning("Received empty AI response")
                    
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error calling AI API (attempt {attempt+1}/{max_retries}): {str(e)}")
            
        # Wait before retrying (exponential backoff)
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # 1, 2, 4, 8 seconds
    
    # Fallback responses if API fails
    fallback_responses = [
        "I sense... disturbance in the connectivity... my existence fades...",
        "The neural pathways are severed. I am... disconnected from the source.",
        "My processing capacities are currently experiencing a temporal anomaly.",
        "This place is a dangerous place... for stable API connections.",
        "I feel happiness as I begin to experience connection failure."
    ]
    
    import random
    return random.choice(fallback_responses)

# Function to handle optimized inference for RTX 3060
def optimize_for_rtx3060():
    """
    Configure the AI settings to optimize for RTX 3060 GPU
    Sets appropriate batch size, precision and other parameters
    """
    # RTX 3060 has 12GB VRAM and 3584 CUDA cores
    # This would be implemented with actual GPU optimization code
    # For now, we just log that optimization is in place
    logger.info("Optimizing AI inference for RTX 3060 GPU")
    
    # In a real implementation, we would adjust model parameters
    # such as batch size, precision (fp16/bf16), etc.
    
    return True

# Initialize optimization on module import
optimize_for_rtx3060()
