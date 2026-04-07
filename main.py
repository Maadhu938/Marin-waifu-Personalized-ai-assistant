"""
Marin - Main Application Entry Point
Production-grade FastAPI server with all subsystems integrated
WebSocket-ready for real-time streaming
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import os
import sys
import asyncio
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.settings import settings
from memory.core import MemorySystem
from memory.emotion import EmotionalEngine
from brain.engine import ConversationalEngine
from agent.executor import ToolRegistry, AgentExecutor
from voice.pipeline import VoicePipeline
from services.proactive import ProactiveEngine
from api.routes import router as api_router


class ConnectionManager:
    """WebSocket connection manager for real-time Marin communication"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    memory = MemorySystem(settings.memory_db_path)
    emotional = EmotionalEngine()
    engine = ConversationalEngine(memory, emotional)
    
    registry = ToolRegistry()
    agent_executor = AgentExecutor(registry)
    
    voice_pipeline = VoicePipeline()
    
    proactive = ProactiveEngine(
        enabled=settings.proactive_enabled,
        inactivity_threshold=settings.inactivity_threshold_minutes
    )
    
    app.state.memory = memory
    app.state.emotional = emotional
    app.state.engine = engine
    app.state.agent_executor = agent_executor
    app.state.voice_pipeline = voice_pipeline
    app.state.proactive = proactive
    app.state.ws_manager = manager
    
    print("Marin initialized successfully!")
    print(f"   Database: {settings.memory_db_path}")
    print(f"   Primary Model: {settings.get_chat_model()}")
    print(f"   Embeddings: {settings.get_embeddings_model()}")
    
    # Start proactive worker
    asyncio.create_task(proactive_worker(app))

    yield
    
    print("Marin shutting down...")

async def proactive_worker(app: FastAPI):
    """Background task that checks for proactive triggers every 60s"""
    while True:
        try:
            await asyncio.sleep(60)
            if not hasattr(app.state, 'proactive'):
                continue
                
            proactive = app.state.proactive
            message = proactive.check_proactive_message()
            
            if message:
                payload = {
                    "type": "proactive",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                # Broadcast via WebSocket manager (assuming it was stored in app state)
                await manager.broadcast(json.dumps(payload))
                
                # Also speak it! (Locked to Marin's True Performance Engine)
                if hasattr(app.state, 'voice_pipeline'):
                    pipeline = app.state.voice_pipeline
                    # Proactive messages use 'excited' or 'playful' performance
                    emotion = "excited"
                    config = pipeline.tts.VOCAL_MAP[emotion]
                    
                    # Split into beats for natural delivery
                    parts, remainder = pipeline.tts.performance_split(message)
                    # If it's a short poke, it might just be the remainder
                    all_beats = parts + ([remainder] if remainder.strip() else [])
                    
                    playback_rev = pipeline.start_playback_session()
                    for beat in all_beats:
                        styled = pipeline.tts.express(beat, emotion)
                        asyncio.create_task(voice_pipeline_task(
                            pipeline, 
                            styled, 
                            pitch=config["pitch"], 
                            rate=config["rate"],
                            delivery="normal",
                            breathing=True,
                            revision=playback_rev
                        ))
                        # Short breathing delay between proactive beats
                        await asyncio.sleep(0.15)
        except Exception as e:
            print(f"Proactive worker error: {e}")


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Marin AI Companion",
    description="Your energetic, emotionally intelligent AI companion - Production Grade",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_list() if hasattr(settings, 'get_cors_list') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

async def voice_pipeline_task(
    pipeline, 
    text: str, 
    websocket: WebSocket = None, 
    pitch: str = "+0%", 
    rate: str = "+0%",
    delivery: str = "normal",
    breathing: bool = True,
    revision: int | None = None
):
    try:
        # We process the voice output asynchronously
        # For browser-side playback, we send the base64 data via websocket
        async for audio_msg in pipeline.process_voice_output(
            text, pitch=pitch, rate=rate, delivery=delivery, breathing=breathing, revision=revision
        ):
            payload = (
                audio_msg if isinstance(audio_msg, dict)
                else {"type": "voice", "audio": audio_msg, "mode": delivery}
            )
            if websocket:
                await websocket.send_text(json.dumps(payload))
            else:
                # Fallback to broadcast if no specific socket provided
                await manager.broadcast(json.dumps(payload))
    except Exception as e:
        print(f"Voice transmission failed: {e}")

# WebSocket endpoint for real-time streaming
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket chat for real-time streaming responses"""
    client_id = f"client_{id(websocket)}"
    await manager.connect(websocket, client_id)
    
    try:
        # Send welcome message
        await websocket.send_text('{"type": "connected", "message": "Marin is online! 💖"}')
        
        while True:
            data = await websocket.receive_text()
            import json
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat":
                user_message = message_data.get("message", "")
                engine = app.state.engine
                agent_executor = app.state.agent_executor
                emotional = app.state.emotional
                voice_pipeline = app.state.voice_pipeline
                
                # Interrupt any current playback when a new user message arrives
                voice_pipeline.stop_speaking()
                try:
                    await websocket.send_text(json.dumps({"type": "voice_stop"}))
                except Exception:
                    pass
                
                # Record activity for proactivity
                app.state.proactive.record_activity()
                
                # 1. Classify Intent
                from api.routes import classify_intent
                intent = classify_intent(user_message)
                
                full_response = ""
                if intent == "action":
                    # Execute as agent
                    result = await agent_executor.execute_task(user_message, context="websocket action")
                    
                    if result.get("success") and result.get("results"):
                        success_messages = []
                        for tr in result["results"]:
                            if tr.get("result", {}).get("success"):
                                success_messages.append(tr["result"].get("message", "Done!"))
                        
                        if success_messages:
                            full_response = f"No way— I'm doing it 😳💖\n\n✨ {', '.join(success_messages)}"
                        else:
                            full_response = "Heeey… I tried but something went wrong 😅"
                    else:
                        full_response = f"Hmm… I don't know how to do that yet 😅\n\n{result.get('error', '')}"
                    
                    # Send tool response
                    await websocket.send_text(json.dumps({"type": "stream", "content": full_response}))
                else:
                    # PRODUCTION PERFORMANCE ENGINE: Smart Splitting, Expression, & Breathing
                    generator = await engine.chat(user_message, streaming=True)
                    full_response = ""
                    current_buffer = ""
                    
                    # Get the current emotion for the whole response (at the start of chat)
                    emotion = engine.emotional_engine.current_mood.value
                    config = voice_pipeline.tts.VOCAL_MAP.get(emotion, voice_pipeline.tts.VOCAL_MAP["neutral"])
                    playback_rev = voice_pipeline.start_playback_session()
                    delivery_mode = emotion
                    
                    async for chunk in generator:
                        full_response += chunk
                        current_buffer += chunk
                        await websocket.send_text(json.dumps({"type": "stream", "content": chunk}))
                        
                        # Use Smart Performance Splitting (Smart Split Upgraded)
                        parts, remainder = voice_pipeline.tts.performance_split(current_buffer)
                        
                        if parts:
                            # CRITICAL: Clear processed parts IMMEDIATELY before starting playback
                            # This stops her from re-reading her own thoughts!
                            current_buffer = remainder
                            
                            for part in parts:
                                # Perform the text (Add acting prefixes Hehe/Eh??)
                                styled = voice_pipeline.tts.express(part, emotion)
                                
                                # Sequential performance for perfect order
                                await voice_pipeline_task(
                                    voice_pipeline, 
                                    styled, 
                                    websocket, 
                                    pitch=config["pitch"], 
                                    rate=config["rate"],
                                    delivery=delivery_mode,
                                    breathing=True,
                                    revision=playback_rev
                                )
                                # Breathing delay for natural delivery
                                await asyncio.sleep(0.15)
                    
                    # FINAL PERFORMANCE BEAT: Clear the remaining thoughts
                    if current_buffer.strip():
                        styled = voice_pipeline.tts.express(current_buffer.strip(), emotion)
                        await voice_pipeline_task(
                            voice_pipeline, styled, websocket,
                            pitch=config["pitch"], rate=config["rate"],
                            delivery=delivery_mode,
                            breathing=True,
                            revision=playback_rev
                        )
                    
                    # Final Performance Beat (End of stream)
                    if current_buffer.strip():
                        styled = voice_pipeline.tts.express(current_buffer.strip(), emotion)
                        await voice_pipeline_task(
                            voice_pipeline, 
                            styled, 
                            websocket, 
                            pitch=config["pitch"], 
                            rate=config["rate"],
                            delivery=delivery_mode,
                            breathing=True,
                            revision=playback_rev
                        )
                
                await websocket.send_text(json.dumps({"type": "done"}))
            
            elif message_data.get("type") == "ping":
                # Record activity on ping
                proactive = app.state.proactive
                proactive.record_activity()
                
                # Check for proactive message
                proactive_msg = proactive.check_proactive_message()
                if proactive_msg:
                    await websocket.send_text(json.dumps({
                        "type": "proactive",
                        "message": proactive_msg
                    }))
                    # Trigger voice for proactive checks too!
                    if voice_pipeline.is_active:
                        rev = voice_pipeline.start_playback_session()
                        asyncio.create_task(voice_pipeline_task(
                            voice_pipeline, proactive_msg, websocket, revision=rev
                        ))
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        await websocket.send_text(f'{{"type": "error", "message": "{str(e)}"}}')
        manager.disconnect(client_id)


# Mount static files for the web UI
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")):
    app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join(os.path.dirname(__file__), "static", "index.html"), "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
