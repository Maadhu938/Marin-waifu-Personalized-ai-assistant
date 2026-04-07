from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sse_starlette.sse import EventSourceResponse
import json
import asyncio

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    streaming: bool = False


class ChatResponse(BaseModel):
    response: str
    emotion: Optional[str] = None
    memory_updated: bool = False
    action_performed: Optional[bool] = False


class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


class FactRequest(BaseModel):
    key: str
    value: Any
    confidence: float = 1.0


class SettingsRequest(BaseModel):
    voice_enabled: Optional[bool] = None
    proactive_enabled: Optional[bool] = None
    mood: Optional[str] = None


ACTION_KEYWORDS = ["open", "go to", "search", "launch", "start", "play", "visit", "browse", "find"]

def classify_intent(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ACTION_KEYWORDS):
        return "action"
    return "chat"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, app_request: Request):
    engine = app_request.app.state.engine
    memory = app_request.app.state.memory
    emotional = app_request.app.state.emotional
    agent_executor = app_request.app.state.agent_executor
    
    if request.streaming:
        raise HTTPException(status_code=400, detail="Use /chat/stream for streaming")
    
    intent = classify_intent(request.message)
    
    if intent == "action":
        result = await agent_executor.execute_task(request.message, context="user requested action")
        
        action_performed = False
        if result.get("success") and result.get("results"):
            tool_results = result["results"]
            success_messages = []
            for tr in tool_results:
                if tr.get("result", {}).get("success"):
                    success_messages.append(tr["result"].get("message", "Done!"))
                    action_performed = True
            
            if success_messages:
                response = f"No way— I'm doing it 😳💖\n\n✨ {', '.join(success_messages)}"
            else:
                response = "Heeey… I tried but something went wrong 😅"
        else:
            response = f"Hmm… I don't know how to do that yet 😅\n\n{result.get('error', '')}"
        from memory.emotion import EmotionTag
        emotion = "excited"
        emotional.update_mood(EmotionTag.EXCITED, intensity=0.7)
    else:
        response = await engine.chat(request.message, streaming=False)
        emotion = emotional.current_mood.value if hasattr(emotional, 'current_mood') else "happy"
        action_performed = False
    
    return ChatResponse(
        response=response,
        emotion=emotion,
        memory_updated=True,
        action_performed=action_performed
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, app_request: Request):
    engine = app_request.app.state.engine
    
    async def event_generator():
        generator = await engine.chat(request.message, streaming=True)
        async for chunk in generator:
            yield {"event": "message", "data": chunk}
        yield {"event": "done", "data": ""}
    
    return EventSourceResponse(event_generator())


@router.post("/agent/execute")
async def execute_tool(req: ToolExecuteRequest, app_request: Request):
    executor = app_request.app.state.agent_executor
    
    result = await executor.registry.execute_tool(
        req.tool_name,
        **req.parameters
    )
    
    return result


@router.get("/agent/tools")
async def list_tools(app_request: Request):
    executor = app_request.app.state.agent_executor
    return {"tools": executor.registry.get_all_tools()}


@router.get("/memory/facts")
async def get_facts(app_request: Request):
    memory = app_request.app.state.memory
    facts = memory.facts.get_all_facts()
    return {"facts": facts}


@router.post("/memory/facts")
async def set_fact(req: FactRequest, app_request: Request):
    memory = app_request.app.state.memory
    memory.facts.set_fact(req.key, req.value, req.confidence)
    return {"success": True, "key": req.key}


@router.get("/memory/reflections")
async def get_reflections(app_request: Request, limit: int = Query(default=10)):
    memory = app_request.app.state.memory
    reflections = memory.reflections.get_recent_reflections(limit)
    return {"reflections": reflections}


@router.get("/memory/persona")
async def get_persona(app_request: Request):
    memory = app_request.app.state.memory
    return {"persona": memory.persona.get_state()}


@router.get("/emotion/state")
async def get_emotion(app_request: Request):
    emotional = app_request.app.state.emotional
    return {
        "mood": emotional.current_mood.value,
        "intensity": emotional.mood_intensity,
        "modulation": emotional.get_response_modulation()
    }


@router.post("/voice/tts")
async def text_to_speech(app_request: Request, text: str = Query(...), voice: Optional[str] = Query(default=None)):
    voice_pipeline = app_request.app.state.voice_pipeline
    
    result = await voice_pipeline.tts.synthesize(text, voice or voice_pipeline.tts.voice)
    
    return {
        "success": True,
        "duration": result.duration,
        "audio_available": bool(result.audio_data)
    }


@router.get("/voice/voices")
async def get_voices(app_request: Request):
    voice_pipeline = app_request.app.state.voice_pipeline
    return {"voices": voice_pipeline.tts.get_available_voices()}


@router.get("/proactive/status")
async def get_proactive_status(app_request: Request):
    proactive = app_request.app.state.proactive
    return proactive.get_stats()


@router.post("/proactive/enable")
async def toggle_proactive(enabled: bool, app_request: Request):
    proactive = app_request.app.state.proactive
    proactive.set_enabled(enabled)
    return {"enabled": enabled}


@router.get("/conversation/history")
async def get_history(app_request: Request):
    engine = app_request.app.state.engine
    return {"history": engine.get_conversation_history()}


@router.post("/conversation/clear")
async def clear_history(app_request: Request):
    engine = app_request.app.state.engine
    engine.clear_history()
    return {"success": True}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Marin"}


@router.get("/proactive/check")
async def check_proactive(app_request: Request):
    """
    Check for proactive Marin message.
    Call this periodically from frontend to get Marin notifications.
    """
    proactive = app_request.app.state.proactive
    proactive.record_activity()  # Record that we checked
    
    message = proactive.check_proactive_message()
    
    return {
        "has_message": message is not None,
        "message": message
    }