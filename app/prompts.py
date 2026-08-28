import random

PROMPTS = [
    # Thoughts and feelings
    "What's been taking up the most space in your mind lately?",
    "How are you feeling right now, without trying to change it?",
    "What is a thought you keep coming back to these days?",
    "If you could say something completely honestly right now, what would it be?",
    "What feeling is easiest for you to name right now, and what feeling is hardest?",
    # Daily experiences
    "What happened today that you're still thinking about?",
    "What was the strongest moment of your day, good or bad?",
    "What did you do today that you didn't expect to?",
    "What is one small thing that went well today?",
    # Stress and worries
    "What is something that has been harder than usual recently?",
    "What worry keeps showing up even when you try to set it aside?",
    "What part of your day feels the most draining right now?",
    "What\u2019s weighing on you that you haven't put into words yet?",
    # Positive moments
    "What made you smile recently, even briefly?",
    "What is something you're grateful for in this week?",
    "What felt a little easier than expected lately?",
    # Relationships
    "Who has been on your mind lately, and why?",
    "What is something you wish you could say to someone but haven't?",
    "How have your relationships been affecting how you feel this week?",
    "What kind of support would feel helpful to you right now?",
    # Self-reflection
    "What do you need more of in your life right now?",
    "What would you change about your day if you could?",
    "What is something you're quietly proud of recently?",
    "What's a pattern you've noticed in how you respond to stress?",
    "What would you tell yourself this week if you could be kind about it?",
    # Looking forward
    "What is something you're looking forward to?",
    "What's a small thing you'd enjoy doing in the next few days?",
    "If the next week went gently, what would it look like?",
]


def get_prompt(exclude=None):
    options = [p for p in PROMPTS if p != exclude] or list(PROMPTS)
    return random.choice(options)
