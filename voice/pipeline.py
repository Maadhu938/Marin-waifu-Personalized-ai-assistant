from typing import Optional, AsyncGenerator, List, Tuple
import asyncio
import base64
import json
from datetime import datetime
import tempfile
import os

class STTResult:
    def __init__(self, text: str, confidence: float = 1.0):
        self.text = text
        self.confidence = confidence
        self.timestamp = datetime.now()

class TTSResult:
    def __init__(self, audio_data: bytes, duration: float = 0.0):
        self.audio_data = audio_data
        self.duration = duration
        self.timestamp = datetime.now()

class SpeechToText:
    """Speech-to-Text Pipeline"""
    def __init__(self, engine: str = "whisper"):
        self.engine = engine
    
    async def transcribe(self, audio_data: bytes) -> STTResult:
        # Placeholder for actual transcription logic
        return STTResult(text="Transcribed audio text", confidence=0.95)

class TextToSpeech:
    """Text-to-Speech Pipeline"""
    def __init__(self, engine: str = "edge"):
        self.engine = engine
        self.voice = "en-US-AnaNeural"  # Cute/Cartoon anime voice (MARIN)
        
    async def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None, 
        pitch: Optional[str] = None,
        rate: Optional[str] = None,
        style: Optional[str] = None,
        volume: Optional[str] = None,
        delivery: str = "normal"
    ) -> TTSResult:
        if self.engine == "edge":
            return await self._edge_tts(
                text, 
                voice or self.voice, 
                pitch=pitch, 
                rate=rate,
                style=style,
                volume=volume
            )
        return TTSResult(audio_data=b"", duration=0.0)

    async def synthesize_breath(self, intensity: str = "soft") -> TTSResult:
        """Generate a short breath sample using whisper prosody."""
        # Small "h" gives an audible inhale without words
        text = "h"
        return await self._edge_tts(
            text,
            self.voice,
            pitch=None,
            rate=None,
            style=None,
            volume=None
        )
    
    VOCAL_MAP = {
        "excited": {"pitch": "+10Hz", "rate": "+15%", "style": "burst"},
        "happy": {"pitch": "+7Hz", "rate": "+10%", "style": "cheerful"},
        "teasing": {"pitch": "+5Hz", "rate": "+5%", "style": "playful"},
        "playful": {"pitch": "+5Hz", "rate": "+5%", "style": "playful"},
        "curious": {"pitch": "+4Hz", "rate": "+0%", "style": "inquiring"},
        "supportive": {"pitch": "+2Hz", "rate": "-5%", "style": "gentle"},
        "soft": {"pitch": "+2Hz", "rate": "-8%", "style": "gentle"},
        "thoughtful": {"pitch": "-2Hz", "rate": "-5%", "style": "slow"},
        "sad": {"pitch": "-5Hz", "rate": "-15%", "style": "slow"},
        "busy": {"pitch": "+2Hz", "rate": "+15%", "style": "hurried"},
        "neutral": {"pitch": "+0Hz", "rate": "+0%", "style": "normal"}
    }

    def normalize(self, text: str) -> str:
        """Deep clean of emojis/symbols using a Speech-Only whitelist"""
        import re
        # Fix common mojibake and unify pauses before filtering
        text = (
            text.replace("â€¦", "…")
                .replace("...", "…")
                .replace("â€”", "—")
                .replace("â€“", "—")
                .replace("â€™", "'")
                .replace("â€˜", "'")
                .replace("â€œ", '"')
                .replace("â€�", '"')
        )
        # Ensure math/code operators don't glue words together (code=mx -> code = mx)
        text = re.sub(r'(?<=\w)([=+*/])(?=\w)', r' \1 ', text)
        # Keep punctuation tight to the preceding word (prevents "really ?" cases)
        text = re.sub(r"\s+([.!?…])", r"\1", text)
        # Collapse long runs of dots into a single ellipsis
        text = re.sub(r"[.]{3,}", "…", text)
        
        # PRODUCTION WHITELIST: Only allow standard speech characters and punctuation
        # REMOVED ~ because TTS engines often read it out loud.
        text = re.sub(r'[^a-zA-Z0-9\s.,!?\'’"—…%–=+*/:()\\[\\]{}_<>-]', '', text)
        
        text = text.replace("\n", " ")
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    def express(self, text: str, emotion: str) -> str:
        """Inject randomized natural expressions (Vocal Acting Upgraded)"""
        import random
        emotion = emotion.lower()
        trimmed = text.strip()
        # Skip acting flair on punctuation-only beats (e.g., lone ellipses)
        if not trimmed or not any(c.isalnum() for c in trimmed):
            return trimmed
        if trimmed[0] in ".!?…":
            return trimmed
        is_question = trimmed.endswith("?")
        has_ellipsis = "…" in trimmed or "..." in trimmed
        if (is_question or has_ellipsis) and emotion in ["curious", "happy", "excited"]:
            return trimmed
        
        # Simplified: keep wording, avoid added interjections
        return trimmed

    def performance_split(self, text: str) -> Tuple[List[str], str]:
        """Split text into (completed_sentences, remainder)"""
        import re
        # Normalize ASCII ellipsis and tidy spacing before punctuation
        normalized = text.replace("...", "…")
        normalized = re.sub(r"\s+([.!?…])", r"\1", normalized)
        # Split on sentence enders (avoid splitting inside decimals like 1.5)
        sentence_punct = r'((?<!\d)[.!?…]+(?!\d))'
        parts = re.split(sentence_punct, normalized)
        sentences = []
        remainder = ""
        
        # re.split with groups returns: [text, delimiter, text, delimiter, trailing_text]
        for i in range(0, len(parts) - 1, 2):
            combined = (parts[i] + parts[i+1]).strip()
            # PRODUCTION SAFETY: Only synthesize if there are actual letters/numbers.
            # This stops her from saying "Exclamation point" out loud!
            if combined and any(c.isalnum() for c in combined):
                sentences.append(combined)
        
        remainder = parts[-1] if len(parts) % 2 != 0 else ""
        return sentences, remainder

    async def _edge_tts(
        self, 
        text: str, 
        voice: str, 
        pitch: Optional[str] = None, 
        rate: Optional[str] = None,
        style: Optional[str] = None,
        volume: Optional[str] = None
    ) -> TTSResult:
        try:
            import edge_tts
            import os
            
            # Temporary file for Edge TTS synthesis
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file.close()
            
            # Re-normalize for production safety
            clean_text = self.normalize(text)
            
            # Minimal params to avoid format errors; let Edge defaults handle prosody
            communicate = edge_tts.Communicate(
                clean_text,
                voice=voice,
                rate=rate if rate else "+0%",
                pitch=pitch if pitch else "+0%"
            )
            await communicate.save(temp_file.name)
            
            if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
                with open(temp_file.name, "rb") as f:
                    audio_data = f.read()
                try: os.unlink(temp_file.name)
                except: pass
                return TTSResult(audio_data=audio_data, duration=len(audio_data) / 48000)
            else:
                return TTSResult(audio_data=b"", duration=0.0)
                
        except Exception as e:
            print(f"Edge TTS error: {e}. Trying fallback voice...")
            # PRODUCTION SAFETY: Re-normalize for the fallback to kill emojis
            clean_text = self.normalize(text)
            try:
                # Fallback to Ana (Marin's True Cute Voice)
                communicate = edge_tts.Communicate(
                    clean_text,
                    voice="en-US-AnaNeural",
                    rate=rate if rate else "+0%",
                    pitch=pitch if pitch else "+0%"
                )
                await communicate.save(temp_file.name)
                if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
                    with open(temp_file.name, "rb") as f:
                        audio_data = f.read()
                    try: os.unlink(temp_file.name)
                    except: pass
                    return TTSResult(audio_data=audio_data, duration=len(audio_data) / 48000)
            except:
                pass
            return TTSResult(audio_data=b"", duration=0.0)

    def stop_audio(self):
        # Playback is now browser-side (client-side)
        pass

class VoicePipeline:
    def __init__(self):
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.is_active = True
        self._playback_revision = 0
    
    def _next_playback_revision(self) -> int:
        self._playback_revision += 1
        return self._playback_revision
    
    def current_revision(self) -> int:
        return self._playback_revision
    
    def start_playback_session(self) -> int:
        return self._next_playback_revision()
    
    async def process_voice_input(self, audio_data: bytes) -> STTResult:
        return await self.stt.transcribe(audio_data)
    async def process_voice_output(
        self, 
        text: str, 
        pitch: str = "+0%", 
        rate: str = "+0%",
        delivery: str = "normal",
        breathing: bool = False,
        revision: Optional[int] = None
    ) -> AsyncGenerator[dict, None]:
        import re
        import base64
        local_rev = revision if revision is not None else self._next_playback_revision()

        # Clean input
        clean_text = re.sub(r'\*.*?\*', '', text)
        clean_text = re.sub(r':[a-zA-Z0-9_-]+:', '', clean_text)
        clean_text = clean_text.replace('*', '')
        # Strip emoji / pictographs once (keep expressive text)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002700-\U000027BF"  # dingbats
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # symbols extended-A
            "\U00002600-\U000026FF"  # miscellaneous symbols
            "]+",
            flags=re.UNICODE
        )
        clean_text = emoji_pattern.sub('', clean_text)

        if not clean_text.strip():
            return

        # Emotion config
        emotion = delivery.lower()
        config = self.tts.VOCAL_MAP.get(emotion, self.tts.VOCAL_MAP["neutral"])

        # Split into performance chunks
        sentences, remainder = self.tts.performance_split(clean_text)

        # Speak each sentence
        for sentence in sentences:
            styled = self.tts.express(sentence, emotion)
            result = await self.tts.synthesize(
                styled,
                pitch=config["pitch"],
                rate=config["rate"],
                delivery=emotion
            )
            if self.current_revision() != local_rev:
                return
            if result.audio_data:
                yield {
                    "type": "voice",
                    "mode": emotion,
                    "audio": base64.b64encode(result.audio_data).decode("utf-8")
                }
            await asyncio.sleep(0.12)

        # Handle remainder
        if remainder.strip():
            styled = self.tts.express(remainder, emotion)
            result = await self.tts.synthesize(
                styled,
                pitch=config["pitch"],
                rate=config["rate"],
                delivery=emotion
            )
            if self.current_revision() != local_rev:
                return
            if result.audio_data:
                yield {
                    "type": "voice",
                    "mode": emotion,
                    "audio": base64.b64encode(result.audio_data).decode("utf-8")
                }
    def stop_speaking(self):
        # Increment revision so in-flight generators self-cancel
        self._next_playback_revision()
    
    def set_voice(self, voice_id: str):
        self.tts.voice = voice_id
    
    def toggle(self, active: bool = None):
        if active is not None:
            self.is_active = active
        else:
            self.is_active = not self.is_active
