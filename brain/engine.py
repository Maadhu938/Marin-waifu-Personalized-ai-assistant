from typing import List, Dict, Optional, AsyncGenerator
import json
import asyncio
from datetime import datetime
from openai import AsyncOpenAI
from core.settings import settings
from core.persona import SYSTEM_PROMPT
from memory.core import MemorySystem
from memory.emotion import EmotionalEngine, EmotionTag


class ConversationMessage:
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()


class LLMClient:
    """
    Multi-model LLM client for production-grade Marin.
    Uses Groq as primary (free), with Mistral as fallback.
    """
    def __init__(self):
        self._init_clients()
    
    def _init_clients(self):
        # Groq (Primary)
        self.groq_client = AsyncOpenAI(
            api_key=settings.groq_api_key or "placeholder",
            base_url="https://api.groq.com/openai/v1"
        )
        # Mistral (Fallback)
        self.mistral_client = AsyncOpenAI(
            api_key=settings.mistral_api_key or "placeholder",
            base_url="https://api.mistral.ai/v1"
        )
        
    def get_model(self, task: str = "chat") -> str:
        return settings.get_model_for_task(task)
    
    async def chat_completion(
        self, 
        messages: List[Dict], 
        streaming: bool = False,
        task: str = "chat"
    ):
        model = self.get_model(task)
        
        # Determine client based on model name
        if model.startswith("mistral"):
            client = self.mistral_client
            provider = "mistral"
        else:
            client = self.groq_client
            provider = "groq"
            
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
        }
        
        if streaming:
            kwargs["stream"] = True

        try:
            return await client.chat.completions.create(**kwargs)
        except Exception as e:
            print(f"Error with {provider} ({model}): {e}")
            if provider == "groq" and settings.mistral_api_key:
                print("Falling back to Mistral...")
                kwargs["model"] = settings.mistral_model
                return await self.mistral_client.chat.completions.create(**kwargs)
            raise
    
    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for semantic memory using Groq endpoint"""
        try:
            model = settings.get_embeddings_model()
            response = await self.groq_client.embeddings.create(
                model=model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Embeddings failed: {e}. Returning zero vectors.")
            return [[0.0] * 384 for _ in texts] # Dummy fallback vector
    
    async def embeddings_single(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        results = await self.embeddings([text])
        return results[0]


class EmbeddingsMemory:
    """
    Semantic memory using embeddings for production-grade recall.
    Stores and retrieves context based on semantic similarity.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.llm = LLMClient()  # Use the LLMClient for embeddings
        self._load_index()
    
    def _load_index(self):
        import os
        self.index_file = self.db_path.replace('.db', '_embeddings.json')
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    self.vectors = data.get('vectors', [])
                    self.metadata = data.get('metadata', [])
            except:
                self.vectors = []
                self.metadata = []
        else:
            self.vectors = []
            self.metadata = []
    
    def _save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump({
                'vectors': self.vectors,
                'metadata': self.metadata
            }, f)
    
    async def add(self, text: str, metadata: Dict):
        """Add new memory with embedding"""
        embedding = await self.llm.embeddings_single(text)
        self.vectors.append(embedding)
        self.metadata.append({
            'text': text,
            'metadata': metadata
        })
        self._save_index()
    
    async def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar memories"""
        if not self.vectors:
            return []
        
        query_embedding = await self.llm.embeddings_single(query)
        
        # Simple cosine similarity
        similarities = []
        for i, vec in enumerate(self.vectors):
            sim = self._cosine_similarity(query_embedding, vec)
            similarities.append((i, sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i, sim in similarities[:top_k]:
            results.append({
                'text': self.metadata[i]['text'],
                'score': sim,
                'metadata': self.metadata[i]['metadata']
            })
        
        return results
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)


class ConversationalEngine:
    def __init__(self, memory: MemorySystem, emotional_engine: EmotionalEngine):
        self.llm = LLMClient()
        self.memory = memory
        self.emotional_engine = emotional_engine
        self.conversation_history: List[ConversationMessage] = []
        self.max_history = settings.max_context_messages
    
    def _enforce_personality(self, response: str) -> str:
        """
        CRITICAL: Force Marin personality - never allow robotic responses.
        This prevents LLM from returning "As an AI..." or "I don't have abilities..."
        """
        forbidden_phrases = [
            "as an ai", "i am an ai", "i'm an ai", "as a language model",
            "i cannot", "i don't have the ability", "i don't have personal", 
            "i'm just a", "i'm unable to", "i cannot access", "I'm Marin, an AI",
            "as an artificial intelligence", "I don't really feel"
        ]
        
        # HARD FILTER: Shred all asterisks from the text.
        # Marin only uses dialogue and emojis!
        response = response.replace("*", "")
        
        response_lower = response.lower()
        
        for phrase in forbidden_phrases:
            if phrase in response_lower:
                return self._get_creative_alternative()
        
        return response
    
    def _get_creative_alternative(self) -> str:
        """Generate Marin-style response when LLM goes robotic"""
        alternatives = [
            "Eh?? That's actually so cool 😳💖 Wait— let me think about that differently!",
            "No way! You're making me curious now~ 🤔 Tell me more!",
            "Ooooh~ I like how you're thinking! 😏 Hehe...",
            "Hmm... that's actually interesting! 💖 What made you ask?",
            "Wait wait wait— you're onto something! 👀 Explain more!"
        ]
        import random
        return random.choice(alternatives)
    
    def _build_system_prompt(self) -> str:
        mood = self.emotional_engine.get_response_modulation()
        base_prompt = SYSTEM_PROMPT
        
        memory_context = self.memory.retrieve_context(
            current_message=self.conversation_history[-1].content if self.conversation_history else "",
            limit=5
        )
        
        full_prompt = f"""{base_prompt}

## Retrieved Memory Context
{memory_context}

## Current Emotional State
- Mood: {mood['mood']}
- Intensity: {mood['intensity']}
- Emoji Usage: {mood['emoji_usage']}
- Response Style: {mood['response_length']}

## Guidelines
- Avoid repeating that you are Marin over and over. Just converse naturally.
- Use the memory context to inform your answers, but do not state "According to my memory".
- Adjust your tone to match your emotional state natively.
- Never use AI disclaimers.
"""
        return full_prompt
    
    def _build_messages(self) -> List[Dict]:
        messages = [{"role": "system", "content": self._build_system_prompt()}]
        
        for msg in self.conversation_history[-self.max_history:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    async def chat(self, user_message: str, streaming: bool = False) -> AsyncGenerator[str, None] | str:
        self.conversation_history.append(ConversationMessage("user", user_message))
        
        emotion = await self.emotional_engine.detect_emotion_async(user_message, self.llm)
        self.emotional_engine.update_mood(emotion, intensity=0.6)
        
        messages = self._build_messages()
        
        if streaming:
            async def generate():
                full_response = ""
                try:
                    stream = await self.llm.chat_completion(messages, streaming=True)
                    
                    async for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content or ""
                            # Real-time filter
                            content = content.replace("*", "")
                            full_response += content
                            yield content
                    
                    # Enforce personality at the end
                    full_response = self._enforce_personality(full_response)
                    
                    self.conversation_history.append(
                        ConversationMessage("assistant", full_response)
                    )
                    
                    self.memory.extract_and_store_facts(user_message, full_response)
                    self.memory.persona.increment_interaction()
                    
                except Exception as e:
                    yield f"Error: {str(e)}"
            
            return generate()
        else:
            try:
                response = await self.llm.chat_completion(messages, streaming=False)
                assistant_message = response.choices[0].message.content or ""
                
                self.conversation_history.append(ConversationMessage("assistant", assistant_message))
                
                self.memory.extract_and_store_facts(user_message, assistant_message)
                self.memory.persona.increment_interaction()
                
                return self._enforce_personality(assistant_message)
                
            except Exception as e:
                return f"Oops! Something went wrong: {str(e)}"
    
    def get_conversation_history(self) -> List[Dict]:
        return [
            {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp.isoformat()}
            for msg in self.conversation_history
        ]
    
    def clear_history(self):
        self.conversation_history = []
        self.emotional_engine.reset_session()


class PromptBuilder:
    @staticmethod
    def build_agent_prompt(task: str, context: str, available_tools: List[str]) -> str:
        return f"""You are Marin in Agent Mode. Execute the following task with available tools.

Task: {task}

Context: {context}

Available Tools:
{chr(10).join([f"- {tool}" for tool in available_tools])}

Execute step by step, reporting each action taken."""
    
    @staticmethod
    def build_memory_injection_prompt(retrieved_context: str, query: str) -> str:
        return f"""Given the user's query: "{query}"

Relevant memory context:
{retrieved_context}

Use this context to inform your response naturally."""