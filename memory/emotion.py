from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json


class EmotionTag(Enum):
    HAPPY = "happy"
    CURIOUS = "curious"
    TEASING = "teasing"
    SUPPORTIVE = "supportive"
    EXCITED = "excited"
    THOUGHTFUL = "thoughtful"
    SAD = "sad"
    BUSY = "busy"


@dataclass
class MemoryItem:
    id: str
    content: str
    created_at: datetime
    importance: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserFact:
    key: str
    value: Any
    confidence: float = 1.0
    source: str = "conversation"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Reflection:
    id: str
    summary: str
    topics: List[str]
    emotional_tone: str
    user_state: str
    created_at: datetime
    importance: float = 0.5


@dataclass
class PersonaState:
    tone_modifier: float = 0.0
    energy_level: float = 0.7
    last_mood: EmotionTag = EmotionTag.HAPPY
    interaction_count: int = 0
    total_sessions: int = 0
    learned_behaviors: List[str] = field(default_factory=list)


class EmotionalEngine:
    def __init__(self):
        self.current_mood = EmotionTag.HAPPY
        self.mood_intensity: float = 0.7
        self.emotion_history: List[Dict] = []
        self.conversation_sentiment: float = 0.0
    
    async def detect_emotion_async(self, text: str, llm_client=None) -> EmotionTag:
        """Use LLM (Groq fast model) to detect emotion, fallback to heuristics"""
        if not llm_client:
            return self._heuristic_emotion(text)
            
        prompt = f"""Analyze the user's text and detect their emotion.
Reply with ONLY ONE WORD from this list: happy, curious, teasing, supportive, excited, thoughtful, sad, busy.

User text: "{text}"
"""
        try:
            response = await llm_client.chat_completion(
                [{"role": "user", "content": prompt}], 
                streaming=False,
                task="emotion"
            )
            content = response.choices[0].message.content.strip().lower()
            
            # Clean punctuation
            import re
            content = re.sub(r'[^\w\s]', '', content)
            
            try:
                return EmotionTag(content)
            except ValueError:
                return self._heuristic_emotion(text)
        except Exception as e:
            print(f"Emotion detection failed: {e}")
            return self._heuristic_emotion(text)
            
    def _heuristic_emotion(self, text: str) -> EmotionTag:
        """Original keyword-based heuristic fallback"""
        text_lower = text.lower()
        
        excitement_markers = ["omg", "wow", "amazing", "awesome", "excited", "!", "no way"]
        curiosity_markers = ["how", "why", "what if", "wonder", "tell me", "explain"]
        sadness_markers = ["sad", "down", "feel bad", "tired", "lonely", "upset"]
        
        if any(m in text_lower for m in excitement_markers):
            return EmotionTag.EXCITED
        elif any(m in text_lower for m in curiosity_markers):
            return EmotionTag.CURIOUS
        elif any(m in text_lower for m in sadness_markers):
            return EmotionTag.SAD
        
        return EmotionTag.HAPPY
        
    def detect_emotion(self, text: str) -> EmotionTag:
        # Keeping synchronous version for backward compatibility if used directly
        return self._heuristic_emotion(text)
    
    def update_mood(self, emotion: EmotionTag, intensity: float = 0.5):
        self.current_mood = emotion
        self.mood_intensity = intensity
        self.emotion_history.append({
            "emotion": emotion.value,
            "intensity": intensity,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_response_modulation(self) -> Dict[str, Any]:
        return {
            "mood": self.current_mood.value,
            "intensity": self.mood_intensity,
            "emoji_usage": "high" if self.mood_intensity > 0.7 else "normal",
            "response_length": "long" if self.current_mood in [ EmotionTag.CURIOUS, EmotionTag.EXCITED] else "normal",
            "exclamation_level": "high" if self.current_mood == EmotionTag.EXCITED else "normal"
        }
    
    def reset_session(self):
        self.conversation_sentiment = 0.0