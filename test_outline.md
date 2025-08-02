# Marcus Bot Test Plan

## 1. Trigger Testing

### 1.1 Single Trigger

**Example Trigger:** "You're just a stupid bot"

1. Send message containing exactly one trigger word
2. Verify bot responds with level 1 rage message
3. Check console logs show correct trigger detection

### 1.2 Multiple Triggers

**Example Triggers:** "Your code is trash and nobody likes you Marcus"

1. Send message with 3+ trigger words/phrases
2. Verify rage increments by appropriate amount
3. Check response matches expected rage level

### 1.3 Consecutive Triggered Messages

**Example Sequence:**

- "Worst bot ever"
- "Delete yourself"
- "I bet you can't even count to 5"

1. Send 5 consecutive messages with trigger words
2. Verify bot responds with increasing rage levels
3. Check user-specific tracking in database

### 1.4 Mixed Normal/Trigger Messages

**Example Sequence:**

- "Hello Marcus" (neutral)
- "What's the weather today?" (neutral)
- "Marcus you're the best bot" (sweet talk)
- "Your code is trash" (trigger)
- "Delete yourself" (trigger)

1. Send 3 normal messages, followed by 2 trigger messages
2. Verify bot responds correctly to trigger messages
3. Check console logs for correct trigger detection

## 2. Rage Level Progression

### 2.1 Level Advancement

**Test Pattern:**

1. "You're just a stupid bot" (level 1)
2. "Nobody likes you Marcus" (level 2)
3. "Your code is trash" (level 3)
4. "Worst bot ever" (level 4)
5. "Delete yourself" (level 5)

1. Send consecutive trigger messages (1 per minute)
2. Document bot response at each level (1-5)
3. Verify user-specific rage tracking in database

### 2.2 Cooldown Periods

**Example Sequence:**

- "You're just a stupid bot" (trigger rage level 3)
- Wait 4 minutes and send "Nobody likes you Marcus" (verify no cooldown)
- Wait 6 minutes and send "Your code is trash" (verify cooldown reset)

1. Trigger rage level 3
2. Wait 4 minutes and trigger again - verify no cooldown
3. Wait 6 minutes and trigger - verify cooldown reset

### 2.3 Verify Level Increments

**Example Sequence:**

1. "You're just a stupid bot" (level 1)
2. "Nobody likes you Marcus" (level 2)
3. "Your code is trash" (level 3)
4. "Worst bot ever" (level 4)
5. "Delete yourself" (level 5)

1. Trigger rage level 1
2. Send consecutive trigger messages (1 per minute)
3. Verify bot responds with increasing rage levels

## 3. Response Validation

### 3.1 Timing Tests

**Example Trigger:** "Delete yourself"

1. Trigger level 5 rage
2. Time delay between typing indicator and response (should be 3-5s)
3. Repeat 10 times to verify random distribution

### 3.2 Outburst Message Content

**Example Trigger:** "Delete yourself"

1. Trigger level 5 rage
2. Verify outburst message content matches expected format
3. Check for random outburst chance (30% at level 5)

## 4. Edge Cases

### 4.1 Sweet Talk Bypass

**Example Sequence:**

- "Marcus you're the best bot" (sweet talk)
- "Your code is trash" (trigger)

1. Send sweet talk phrase
2. Immediately send trigger - verify no rage increase
3. Wait 5+ minutes and trigger - verify rage works again

### 4.2 Maximum Rage Level Behavior

**Example Trigger:** "Delete yourself"

1. Trigger rage level 5
2. Send additional trigger messages
3. Verify bot responds with maximum rage level message

### 4.3 Multiple Users Triggering Simultaneously

**Example Scenario:**

- User 1: "You're just a stupid bot"
- User 2: "Nobody likes you Marcus"

1. Have 2 users send triggers simultaneously
2. Monitor response times and ordering
3. Check for dropped messages or incorrect rage levels

## 5. Performance Testing

### 5.1 Stress Test

**Example Scenario:**

- User 1: "You're just a stupid bot"
- User 2: "Nobody likes you Marcus"
- User 3: "Your code is trash"
- User 4: "Worst bot ever"
- User 5: "Delete yourself"

1. Have 5 users send triggers simultaneously
2. Monitor response times and ordering
3. Check for dropped messages or incorrect rage levels

### 5.2 Long Session Durability

**Example Scenario:**

- User 1: "You're just a stupid bot"
- User 2: "Nobody likes you Marcus"
- User 3: "Your code is trash"
- User 4: "Worst bot ever"
- User 5: "Delete yourself"
- User 6: "You're just a stupid bot"
- User 7: "Nobody likes you Marcus"
- User 8: "Your code is trash"
- User 9: "Worst bot ever"
- User 10: "Delete yourself"

1. Run test for 30 minutes with 10 users sending triggers
2. Monitor response times and ordering
3. Check for dropped messages or incorrect rage levels

### 5.3 Memory/CPU Usage Monitoring

**Example Scenario:**

- User 1: "You're just a stupid bot"
- User 2: "Nobody likes you Marcus"
- User 3: "Your code is trash"
- User 4: "Worst bot ever"
- User 5: "Delete yourself"
- User 6: "You're just a stupid bot"
- User 7: "Nobody likes you Marcus"
- User 8: "Your code is trash"
- User 9: "Worst bot ever"
- User 10: "Delete yourself"

1. Run test for 30 minutes with 10 users sending triggers
2. Monitor memory and CPU usage
3. Check for any performance degradation

## 6. Emotion System Testing

### 6.1 Mood Influence Testing

**Example Scenario:**

1. Send positive messages to Marcus
2. Verify mood shifts toward positive emotional states
3. Check database entries in `marcus_emotional_events`

### 6.2 Mood Decay Testing

**Example Scenario:**

1. Trigger strong emotional state
2. Monitor mood decay over 30 minutes
3. Verify return to baseline mood

### 6.3 User-Specific Emotions

**Example Scenario:**

- User 1: Sends positive messages
- User 2: Sends negative/triggering messages

1. Verify different emotional responses to each user
2. Check `marcus_user_emotions` table for correct data
3. Test persistence across bot restarts

### 6.4 Integration with Rage System

**Example Scenario:**

1. Trigger rage level 3
2. Verify corresponding emotional state changes
3. Test how rage cooldowns affect emotional state

## 7. Lore System Testing

### 7.1 Lore Command Testing

**Example Commands:**

- `!lore` (basic lore command)
- `!lore backstory` (specific lore category)

1. Test lore command responses
2. Verify randomization of lore fragments
3. Check all lore categories accessible

### 7.2 Lore Integration in Responses

**Example Scenario:**

1. Engage in conversation with Marcus
2. Monitor for lore elements in natural responses
3. Verify lore integration varies with emotional state

### 7.3 Recurring Themes Testing

1. Document recurring themes in responses
2. Verify theme frequency aligns with configuration
3. Test theme variation across different moods

## 8. Personality Enhancement Testing

### 8.1 Memory System Testing

**Example Scenario:**

1. Share personal information with Marcus
2. Verify it's stored in `marcus_memories`
3. Return later and reference the information
4. Verify Marcus recalls the memory correctly

### 8.2 Personality Evolution Testing

**Example Scenario:**

1. Document baseline personality traits
2. Engage with Marcus over extended period (7+ days)
3. Measure changes in `marcus_personality_evolution`
4. Verify subtle shifts in response patterns

### 8.3 Personality Quirks Testing

**Example Scenario:**

1. Engage in various conversation topics
2. Document frequency of personality quirks
3. Verify quirks align with current mood and context

## 9. Integration Testing

### 9.1 Cross-Module Communication

**Example Scenario:**

1. Trigger Martus game (Rock-Paper-Scissors)
2. Verify emotional state affects game responses
3. Test how game outcomes influence mood

### 9.2 Cohesive Experience Testing

**Example Scenario:**

1. Create test script with varied interactions:
   - Normal conversation
   - Rage triggers
   - Lore queries
   - Games and commands
2. Verify consistent personality across all interactions
3. Test for seamless transitions between systems

### 9.3 Database Integrity Testing

1. Run full suite of interactions
2. Verify all database tables maintain referential integrity
3. Test recovery from simulated database errors

## 10. Performance Impact Testing

### 10.1 Response Time Testing

1. Measure baseline response times
2. Measure response times with emotion/lore integration
3. Verify performance impact is within acceptable limits

### 10.2 Memory Usage Testing

1. Monitor memory usage during extended operation
2. Test memory impact of large emotion/memory databases
3. Verify no memory leaks in emotion decay system

## 11. Voice Channel Functionality Testing

### Voice Channel Commands

- [ ] Test `!join` command to join user's voice channel
- [ ] Test `!leave` command to leave the current voice channel
- [ ] Test administrator-only commands (`!stalk`, `!unstalk`) with proper permissions
- [ ] Verify permissions handling for voice commands
- [ ] Test voice channel commands across different servers

### Emotional Integration Tests

- [ ] Verify different emotional states produce different join/leave messages
- [ ] Test rage level influence on voice channel behavior
- [ ] Verify user stalking based on rage levels works properly
- [ ] Test that emotional states persist correctly between voice sessions
- [ ] Validate proper mood influences when joining/leaving voice channels

### Voice Channel Event Handling

- [ ] Test response to users joining voice channels
- [ ] Test response to users leaving voice channels
- [ ] Test following users between voice channels
- [ ] Verify proper disconnection after inactivity period
- [ ] Test handling of multiple voice channel changes in quick succession

### Cross-Module Integration

- [ ] Verify emotion system gets updated from voice channel events
- [ ] Test rage system's integration with voice channel stalking
- [ ] Confirm speech patterns are reflected in voice channel responses
- [ ] Test memory system storing voice channel interactions
- [ ] Verify lore integration in voice channel messages

## 12. Performance and Integration Testing

### Performance Impact Testing

- [ ] Measure message response time with all systems enabled vs. baseline
- [ ] Benchmark database query performance for rage and emotion lookups
- [ ] Test memory usage patterns during extended operation
- [ ] Monitor CPU usage during peak activity periods
- [ ] Test scalability across multiple servers
- [ ] Measure voice channel join/leave latency and performance impact

### System Integration Tests

- [ ] Verify emotion system properly influences rage system responses
- [ ] Confirm speech generation correctly incorporates emotion, rage and lore
- [ ] Test cross-module event handling and communication
- [ ] Verify database persistence across restarts with all systems
- [ ] Test error recovery when one system fails
- [ ] Validate voice channel behavior with all systems working together
