from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import uuid
import os

Base = declarative_base()


class FactModel(Base):
    __tablename__ = "facts"
    
    id = Column(String, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    confidence = Column(Float, default=1.0)
    source = Column(String, default="conversation")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class ReflectionModel(Base):
    __tablename__ = "reflections"
    
    id = Column(String, primary_key=True)
    summary = Column(Text)
    topics = Column(JSON)
    emotional_tone = Column(String)
    user_state = Column(String)
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.now)


class FactsMemory:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def set_fact(self, key: str, value: Any, confidence: float = 1.0, source: str = "conversation"):
        session = self.Session()
        existing = session.query(FactModel).filter_by(key=key).first()
        
        serialized_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        
        if existing:
            existing.value = serialized_value
            existing.confidence = confidence
            existing.updated_at = datetime.now()
        else:
            fact = FactModel(
                id=str(uuid.uuid4()),
                key=key,
                value=serialized_value,
                confidence=confidence,
                source=source
            )
            session.add(fact)
        
        session.commit()
        session.close()
    
    def get_fact(self, key: str) -> Optional[Any]:
        session = self.Session()
        fact = session.query(FactModel).filter_by(key=key).first()
        session.close()
        
        if fact:
            fact_value = str(fact.value) if fact.value else ""
            try:
                return json.loads(fact_value)
            except:
                return fact_value
        return None
    
    def get_all_facts(self) -> Dict[str, Any]:
        session = self.Session()
        facts = session.query(FactModel).all()
        session.close()
        
        result = {}
        for fact in facts:
            fact_value = str(fact.value) if fact.value else ""
            try:
                result[fact.key] = json.loads(fact_value)
            except:
                result[fact.key] = fact_value
        return result
    
    def search_facts(self, query: str) -> List[Dict]:
        session = self.Session()
        facts = session.query(FactModel).filter(FactModel.key.contains(query)).all()
        session.close()
        
        return [{"key": f.key, "value": f.value, "confidence": f.confidence} for f in facts]


class ReflectionMemory:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path.replace('.db', '_reflections.db')}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_reflection(self, summary: str, topics: List[str], emotional_tone: str, 
                      user_state: str, importance: float = 0.5):
        session = self.Session()
        reflection = ReflectionModel(
            id=str(uuid.uuid4()),
            summary=summary,
            topics=topics,
            emotional_tone=emotional_tone,
            user_state=user_state,
            importance=importance,
            created_at=datetime.now()
        )
        session.add(reflection)
        session.commit()
        session.close()
    
    def get_recent_reflections(self, limit: int = 10) -> List[Dict]:
        session = self.Session()
        reflections = session.query(ReflectionModel).order_by(
            ReflectionModel.created_at.desc()
        ).limit(limit).all()
        session.close()
        
        return [{
            "id": r.id,
            "summary": r.summary,
            "topics": r.topics,
            "emotional_tone": r.emotional_tone,
            "importance": r.importance,
            "created_at": r.created_at.isoformat()
        } for r in reflections]
    
    def search_reflections(self, query: str) -> List[Dict]:
        session = self.Session()
        reflections = session.query(ReflectionModel).filter(
            ReflectionModel.summary.contains(query)
        ).all()
        session.close()
        
        return [{
            "id": r.id,
            "summary": r.summary,
            "topics": r.topics,
            "emotional_tone": r.emotional_tone
        } for r in reflections]


class PersonaMemory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.state_file = db_path.replace('.db', '_persona.json')
        self._load_state()
    
    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "tone_modifier": 0.0,
                "energy_level": 0.7,
                "interaction_count": 0,
                "total_sessions": 0,
                "learned_behaviors": [],
                "preferred_topics": [],
                "communication_style": "casual"
            }
    
    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def update_behavior(self, behavior: str, frequency: int = 1):
        behaviors = self.state.get("learned_behaviors", [])
        found = False
        for b in behaviors:
            if b["name"] == behavior:
                b["count"] += frequency
                found = True
                break
        if not found:
            behaviors.append({"name": behavior, "count": frequency})
        self.state["learned_behaviors"] = behaviors
        self._save_state()
    
    def increment_interaction(self):
        self.state["interaction_count"] += 1
        self._save_state()
    
    def get_tone_modifier(self) -> float:
        interaction_count = self.state.get("interaction_count", 0)
        if interaction_count < 10:
            return 0.1
        elif interaction_count < 50:
            return 0.0
        elif interaction_count < 100:
            return -0.1
        return 0.0
    
    def get_state(self) -> Dict:
        return self.state


class MemorySystem:
    def __init__(self, db_path: str):
        self.facts = FactsMemory(db_path)
        self.reflections = ReflectionMemory(db_path)
        self.persona = PersonaMemory(db_path)
    
    def retrieve_context(self, current_message: str, limit: int = 5) -> str:
        facts = self.facts.get_all_facts()
        
        recent = self.reflections.get_recent_reflections(limit)
        
        facts_context = "\n".join([f"• {k}: {v}" for k, v in facts.items()]) if facts else "No facts stored."
        
        reflections_context = "\n".join([r["summary"] for r in recent]) if recent else "No previous conversations."
        
        return f"""
User Facts:
{facts_context}

Recent Conversations:
{reflections_context}
"""
    
    def extract_and_store_facts(self, message: str, response: str):
        import re
        
        name_patterns = [
            r"(?:my name is|i'm|i am)\s+([a-zA-Z]+)",
            r"(?:call me)\s+([a-zA-Z]+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message.lower())
            if match:
                self.facts.set_fact("user_name", match.group(1), confidence=0.8)
        
        interest_patterns = [
            r"(?:i like|i love|i enjoy)\s+([^.]+)",
            r"(?:interested in|into)\s+([^.]+)"
        ]
        for pattern in interest_patterns:
            matches = re.findall(pattern, message.lower())
            for match in matches:
                current = self.facts.get_fact("interests") or []
                if isinstance(current, list) and match not in current:
                    current.append(match.strip())
                    self.facts.set_fact("interests", current, confidence=0.7)
    
    def create_reflection(self, conversation_history: List[Dict], summary_length: int = 200):
        if len(conversation_history) < 2:
            return
        
        messages = [f"{m['role']}: {m['content']}" for m in conversation_history[-5:]]
        full_convo = " ".join(messages)
        
        if len(full_convo) > summary_length:
            summary = full_convo[:summary_length] + "..."
        else:
            summary = full_convo
        
        topics = []
        if any(w in full_convo.lower() for w in ["code", "programming", "developer"]):
            topics.append("programming")
        if any(w in full_convo.lower() for w in ["work", "job", "career"]):
            topics.append("work")
        if any(w in full_convo.lower() for w in ["game", "play", "fun"]):
            topics.append("entertainment")
        
        emotional_tone = "neutral"
        if any(w in full_convo.lower() for w in ["happy", "excited", "great", "awesome"]):
            emotional_tone = "positive"
        elif any(w in full_convo.lower() for w in ["sad", "bad", "tired"]):
            emotional_tone = "concerned"
        
        self.reflections.add_reflection(
            summary=summary,
            topics=topics,
            emotional_tone=emotional_tone,
            user_state="casual",
            importance=0.5
        )