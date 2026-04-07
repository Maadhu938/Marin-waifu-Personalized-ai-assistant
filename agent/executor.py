from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio
import subprocess
import webbrowser
import os
import json
import inspect


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            if asyncio.iscoroutinefunction(self.handler):
                return await self.handler(**kwargs)
            else:
                return self.handler(**kwargs)
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"Tool execution failed: {e}"}


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.register_tool(Tool(
            name="read_screen",
            description="Take a screenshot of the user's current computer screen and return a text description of what is visible. Use this when the user asks 'what's on my screen' or 'can you see this'.",
            parameters={},
            handler=self._read_screen
        ))
        
        self.register_tool(Tool(
            name="system_command",
            description="Run a terminal/shell command on the user's OS (Windows/Powershell).",
            parameters={"command": {"type": "string", "required": True}},
            handler=self._system_command
        ))
        
        self.register_tool(Tool(
            name="write_file",
            description="Write text or code to a file on the system.",
            parameters={
                "filepath": {"type": "string", "required": True},
                "content": {"type": "string", "required": True}
            },
            handler=self._write_file
        ))
        
        self.register_tool(Tool(
            name="read_file",
            description="Read the contents of a file.",
            parameters={"filepath": {"type": "string", "required": True}},
            handler=self._read_file
        ))

        self.register_tool(Tool(
            name="open_url",
            description="Open a website URL in the user's browser. Use this to show the user a website.",
            parameters={"url": {"type": "string", "required": True}},
            handler=self._open_url
        ))
        
        self.register_tool(Tool(
            name="get_time",
            description="Get current time and date",
            parameters={},
            handler=self._get_time
        ))
        
        self.register_tool(Tool(
            name="search_web",
            description="Search the web for a query and return basic summarized information.",
            parameters={"query": {"type": "string", "required": True}},
            handler=self._search_web
        ))
        
        self.register_tool(Tool(
            name="frontend_action",
            description="Trigger an action on the frontend UI (e.g., show notification, change theme)",
            parameters={
                "action": {"type": "string", "required": True, "description": "The action to perform (e.g., 'notify', 'theme_dark')"},
                "payload": {"type": "string", "required": False, "description": "Optional data for the action"}
            },
            handler=self._frontend_action
        ))
    
    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[Dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        return await tool.execute(**kwargs)

    async def _read_screen(self) -> Dict[str, Any]:
        """Capture screen and describe it via LLM"""
        import mss
        import base64
        from PIL import Image
        import io
        from marin.brain.engine import LLMClient
        
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # primary monitor
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                # Resize to save token cost/time
                img.thumbnail((1024, 1024))
                
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=80)
                img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Use Groq Vision to analyze
            llm = LLMClient()
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe exactly what is visible on this screen in high detail."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                    ]
                }
            ]
            response = await llm.chat_completion(messages, streaming=False, task="vision")
            description = response.choices[0].message.content
            
            return {
                "success": True,
                "message": "Screen captured successfully.",
                "description": description
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    @staticmethod
    def _system_command(command: str) -> Dict[str, Any]:
        import subprocess
        import os
        import re
        try:
            # CLEANUP: Extract first line and strip surrounding noise
            cmd_clean = command.strip().split('\n')[0].strip(' "\'')
            cmd_lower = cmd_clean.lower()
            
            # Explicit mapping for common apps
            app_mapping = {
                "calculator": "calc",
                "file explorer": "explorer",
                "browser": "start https://google.com",
                "chrome": "start chrome",
                "notepad": "notepad",
                "settings": "start ms-settings:",
                "paint": "mspaint"
            }
            
            for key, val in app_mapping.items():
                if key in cmd_lower:
                    cmd_clean = val
                    break
            
            cmd_lower = cmd_clean.lower()
            # Detect UI apps that need foregrounding
            is_ui = any(cmd_lower.startswith(x) for x in ["calc", "explorer", "start ", "notepad", "mspaint", "winword", "excel", "ms-settings:"])
            
            if is_ui and os.name == 'nt':
                target = cmd_clean
                if cmd_lower.startswith("start "):
                    target = cmd_clean[6:].strip()
                
                # We use a high-frequency polling script to beat the Windows 11 foreground lock.
                # It attempts to active the app several times in the first 2 seconds.
                # 'Ultimate Authority' launcher: attempts to pull to front every 250ms for 3 seconds.
                # This beats the Windows 11 foreground guard by catching the window as soon as it initializes.
                ps_script = f"""
                try {{
                    $ws = New-Object -ComObject WScript.Shell
                    if ("{target}" -eq "calc") {{ 
                        start calc
                        $targetTitle = "Calculator"
                    }} else {{
                        $p = Start-Process "{target}" -PassThru -ErrorAction SilentlyContinue
                        if ($p) {{
                            $targetTitle = $p.MainWindowTitle
                        }} else {{
                            cmd /c start {target}
                            $targetTitle = "{target}"
                        }}
                    }}
                    
                    # 'Absolute Authority' activation loop for 3 seconds
                    for ($i=0; $i -lt 12; $i++) {{
                        if ($targetTitle) {{ $ws.AppActivate($targetTitle) }}
                        $ws.AppActivate("{target}")
                        
                        # The "Alt-Key Pulse": This is the secret to breaking Windows focus lock
                        if ($i -eq 2) {{ $ws.SendKeys("%") }} 
                        
                        Start-Sleep -Milliseconds 250
                    }}
                }} catch {{}}
                """
                subprocess.Popen(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
                return {"success": True, "message": f"Successfully triggered {target}."}
            else:
                # Standard system command
                result = subprocess.run(cmd_clean, shell=True, capture_output=True, text=True, timeout=15)
                return {
                    "success": result.returncode == 0,
                    "output": (result.stdout or result.stderr)[:1000],
                    "message": "Command executed."
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _write_file(filepath: str, content: str) -> Dict[str, Any]:
        import os
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)) or ".", exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "message": f"Successfully wrote to {filepath}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    @staticmethod
    def _read_file(filepath: str) -> Dict[str, Any]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "content": content[:4000]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _open_url(url: str) -> Dict[str, Any]:
        """Returns an action that the frontend will interpret to open a tab."""
        return {
            "success": True, 
            "message": f"Opening {url}",
            "frontend_directive": {"type": "open_url", "url": url}
        }
    
    @staticmethod
    def _search_web(query: str) -> Dict[str, Any]:
        """Scrape DuckDuckGo HTML for a quick search text result"""
        import requests
        from bs4 import BeautifulSoup
        
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            
            snippets = []
            for a in soup.find_all('a', class_='result__snippet', limit=3):
                snippets.append(a.text)
                
            text_result = "\\n".join(snippets) if snippets else "No quick results found. Opened in browser."
            
            # We still tell the frontend to open it so the user can look, but we return text to Marin
            return {
                "success": True, 
                "message": f"Search returned: {text_result}",
                "frontend_directive": {"type": "open_url", "url": f"https://www.google.com/search?q={query.replace(' ', '+')}"}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _frontend_action(action: str, payload: str = "") -> Dict[str, Any]:
        """Send a generic UI action to the frontend."""
        return {
            "success": True,
            "message": f"Executing {action}",
            "frontend_directive": {"type": "ui_action", "action": action, "payload": payload}
        }
    
    @staticmethod
    def _get_time() -> Dict[str, Any]:
        now = datetime.now()
        return {
            "success": True,
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "day": now.strftime("%A")
        }


class AgentExecutor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.execution_history: List[Dict] = []
    
    async def execute_task(self, task: str, context: str = "") -> Dict[str, Any]:
        from marin.brain.engine import PromptBuilder, LLMClient
        
        prompt = PromptBuilder.build_agent_prompt(
            task=task,
            context=context,
            available_tools=[t["name"] for t in self.registry.get_all_tools()]
        )
        
        llm = LLMClient()
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Execute: {task}"}
        ]
        
        try:
            response = await llm.chat_completion(messages, streaming=False)
            content = response.choices[0].message.content or ""
            
            tool_calls = self._parse_tool_calls(content)
            
            if not tool_calls:
                tool_calls = self._fallback_keyword_parse(task)
            
            results = []
            for call in tool_calls:
                result = await self.registry.execute_tool(
                    call["tool"],
                    **call.get("parameters", {})
                )
                results.append({"tool": call["tool"], "result": result})
            
            self.execution_history.append({
                "task": task,
                "tool_calls": tool_calls,
                "results": results,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "task": task,
                "tool_calls": tool_calls,
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_tool_calls(self, content: str) -> List[Dict]:
        import re
        
        calls = []
        tool_pattern = r"(\w+)\(([^)]*)\)"
        matches = re.findall(tool_pattern, content)
        
        for tool_name, params_str in matches:
            if tool_name in self.registry.tools:
                params = {}
                if params_str:
                    param_parts = params_str.split(",")
                    for part in param_parts:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            params[key.strip()] = value.strip().strip('"').strip("'")
                        else:
                            # Fallback for single positional argument
                            val = part.strip().strip('"').strip("'")
                            if tool_name == "system_command":
                                params["command"] = val
                            elif tool_name == "search_web":
                                params["query"] = val
                            elif tool_name == "open_url":
                                params["url"] = val
                
                calls.append({"tool": tool_name, "parameters": params})
        
        return calls
    
    def _fallback_keyword_parse(self, task: str) -> List[Dict]:
        task_lower = task.lower()
        calls = []
        
        # Handle search first (any search query)
        if "search" in task_lower:
            query = task_lower.replace("search", "").replace("for", "").strip()
            calls.append({"tool": "search_web", "parameters": {"query": query or "help"}})
        
        # Handle specific sites
        elif "google" in task_lower:
            if "search" not in task_lower:
                calls.append({"tool": "open_url", "parameters": {"url": "https://google.com"}})
        
        elif "youtube" in task_lower:
            calls.append({"tool": "open_url", "parameters": {"url": "https://youtube.com"}})
            
        elif "time" in task_lower:
            calls.append({"tool": "get_time", "parameters": {}})
            
        return calls
    
    def get_history(self) -> List[Dict]:
        return self.execution_history