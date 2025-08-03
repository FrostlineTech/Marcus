# Marcus Bot Rage System Test Plan

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
