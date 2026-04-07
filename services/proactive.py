from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import random


class ProactiveTrigger:
    def __init__(self, trigger_type: str, condition: Callable, message: str, cooldown: int = 300):
        self.trigger_type = trigger_type
        self.condition = condition
        self.message = message
        self.cooldown = cooldown
        self.last_triggered: Optional[datetime] = None
    
    def can_trigger(self) -> bool:
        if self.last_triggered is None:
            return True
        elapsed = (datetime.now() - self.last_triggered).total_seconds()
        return elapsed >= self.cooldown
    
    def trigger(self) -> Optional[str]:
        if self.can_trigger() and self.condition():
            self.last_triggered = datetime.now()
            return self.message
        return None


class ProactiveEngine:
    def __init__(self, enabled: bool = True, inactivity_threshold: int = 30):
        self.enabled = enabled
        self.inactivity_threshold = inactivity_threshold
        self.last_activity: datetime = datetime.now()
        self.last_message_time: Optional[datetime] = None
        self.triggers: List[ProactiveTrigger] = []
        self.conversation_suggestions: List[str] = []
        self._register_default_triggers()
    
    def _register_default_triggers(self):
        self.triggers.extend([
            ProactiveTrigger(
                trigger_type="inactivity",
                condition=self._check_inactivity,
                message="Hey hey! ✨ You've been quiet for a bit— everything okay?",
                cooldown=600
            ),
            ProactiveTrigger(
                trigger_type="time_based",
                condition=self._check_time_based,
                message=self._get_time_greeting(),
                cooldown=3600
            ),
            ProactiveTrigger(
                trigger_type="curiosity",
                condition=self._check_curiosity,
                message="Hmm~ I've been thinking... what have you been up to lately?",
                cooldown=1800
            )
        ])
        
        self.conversation_suggestions = [
            "Want to hear something interesting?",
            "Did you know...",
            "I've been wondering—",
            "Quick question!",
            "Check this out!"
        ]
    
    def _check_inactivity(self) -> bool:
        if self.last_activity is None:
            return False
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed > (self.inactivity_threshold * 60)
    
    def _check_time_based(self) -> bool:
        current_hour = datetime.now().hour
        return current_hour in [9, 12, 18, 21]
    
    def _check_curiosity(self) -> bool:
        return random.random() < 0.2
    
    def _get_time_greeting(self) -> str:
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            return "Good morning! ☀️ Hope you're having a great start to your day!"
        elif 12 <= current_hour < 17:
            return "Hey! 🌞 How's your day going?"
        elif 17 <= current_hour < 21:
            return "Evening! 🌙 What's good?"
        else:
            return "Hey night owl! 🌙 Still up?"
    
    def record_activity(self):
        self.last_activity = datetime.now()
        self.last_message_time = datetime.now()
    
    def check_proactive_message(self) -> Optional[str]:
        if not self.enabled:
            return None
        
        for trigger in self.triggers:
            message = trigger.trigger()
            if message:
                return message
        
        return None
    
    def get_suggestion(self) -> str:
        return random.choice(self.conversation_suggestions)
    
    def add_trigger(self, trigger: ProactiveTrigger):
        self.triggers.append(trigger)
    
    def remove_trigger(self, trigger_type: str):
        self.triggers = [t for t in self.triggers if t.trigger_type != trigger_type]
    
    def set_enabled(self, enabled: bool):
        self.enabled = enabled
    
    def get_stats(self) -> Dict:
        return {
            "enabled": self.enabled,
            "inactivity_threshold_minutes": self.inactivity_threshold,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "triggers_count": len(self.triggers)
        }


class PatternLearner:
    def __init__(self):
        self.message_timestamps: List[datetime] = []
        self.topics: Dict[str, int] = {}
        self.activity_patterns: Dict[str, List[int]] = {}
    
    def record_message(self, content: str):
        now = datetime.now()
        self.message_timestamps.append(now)
        
        hour = now.hour
        if hour not in self.activity_patterns:
            self.activity_patterns[hour] = []
        self.activity_patterns[hour].append(1)
    
    def get_peak_hours(self) -> List[int]:
        if not self.activity_patterns:
            return []
        
        hour_counts = {hour: sum(activities) for hour, activities in self.activity_patterns.items()}
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]
    
    def get_average_response_interval(self) -> float:
        if len(self.message_timestamps) < 2:
            return 0.0
        
        intervals = []
        for i in range(1, len(self.message_timestamps)):
            delta = (self.message_timestamps[i] - self.message_timestamps[i-1]).total_seconds()
            intervals.append(delta)
        
        return sum(intervals) / len(intervals) if intervals else 0.0
    
    def suggest_topic(self) -> Optional[str]:
        if not self.topics:
            return None
        
        sorted_topics = sorted(self.topics.items(), key=lambda x: x[1], reverse=True)
        return sorted_topics[0][0] if sorted_topics else None