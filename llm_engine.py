# llm_engine.py: Ollama async orchestration & Tool Calling
import asyncio
import re
from ollama import AsyncClient
from typing import List, Dict, Any, Callable

# ---------------------------------------------------------
# 1. Define Local Tools (Plugins)
# ---------------------------------------------------------
# Ollama natively parses type hints and docstrings into tool schemas!
def get_weather(location: str) -> str:
    """Get the current weather conditions for a specific location."""
    print(f"🔧 [Tool Execution] Fetching weather for {location}...")
    # In a real app, you would call OpenWeatherAPI here
    return f"The weather in {location} is currently 72°F and sunny."

def toggle_smart_lights(room: str, state: str) -> str:
    """Turn the smart lights on or off in a specific room. State should be 'on' or 'off'."""
    print(f"🔧 [Tool Execution] Turning {state} the lights in the {room}...")
    # In a real app, you would call HomeAssistant REST API here
    return f"The {room} lights have been turned {state}."

def get_current_time() -> str:
    """Get the current local time."""
    import datetime
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    print(f"🔧 [Tool Execution] Getting current time: {time_str}...")
    return f"The current time is {time_str}."

def search_wikipedia(query: str) -> str:
    """Search Wikipedia to get general information, facts, history, or descriptions of people, places, or topics."""
    import urllib.request
    import urllib.parse
    import json
    print(f"🔧 [Tool Execution] Searching Wikipedia for '{query}'...")
    try:
        # Step 1: Search for top 3 matching page titles
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={urllib.parse.quote(query)}&utf8=1&srlimit=3"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            results = data.get("query", {}).get("search", [])
            if not results:
                return f"No Wikipedia results found for '{query}'."
        
        summaries = []
        for res in results:
            title = res["title"]
            # Step 2: Retrieve the extract/summary for this page
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
            req_summary = urllib.request.Request(summary_url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req_summary, timeout=3) as resp_summary:
                    sum_data = json.loads(resp_summary.read().decode())
                    extract = sum_data.get("extract")
                    if extract:
                        summaries.append(f"[{title}]: {extract}")
            except Exception:
                continue
        
        if summaries:
            return "Wikipedia Search Results:\n" + "\n\n".join(summaries)
        return f"Found matching articles but could not retrieve summaries for '{query}'."
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"

def get_latest_news() -> str:
    """Fetches the latest real-time global breaking news headlines and summaries from Google News RSS."""
    import urllib.request
    import xml.etree.ElementTree as ET
    print("🔧 [Tool Execution] Fetching latest news from Google News RSS...")
    try:
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        
        news_reports = []
        for item in items[:4]:
            title = item.find("title").text
            pub_date = item.find("pubDate").text
            news_reports.append(f"- {title} ({pub_date})")
            
        if news_reports:
            return "Current Live News Headlines:\n" + "\n".join(news_reports)
        return "No news items found."
    except Exception as e:
        return f"Error retrieving latest news: {str(e)}"

# ---------------------------------------------------------
# 2. LLM Orchestrator
# ---------------------------------------------------------
class LLMEngine:
    def __init__(self, model_name="llama3.2"): # qwen2.5 is also excellent for local tools
        self.client = AsyncClient()
        self.model = model_name
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are Jarvis, a friendly, concise local voice assistant. "
                "CRITICAL: Keep your responses extremely brief. Limit your output to a maximum of 1 or 2 sentences (under 35 words). "
                "Never output bullet points, lists, markdown formatting, or long explanations, as your response is being spoken aloud. "
                "If the user asks a complex question, provide a ultra-brief summary (1 sentence) and ask if they want to hear more. "
                "Only use tools when explicitly requested by the user. Do not call weather, lights, time, or search tools for generic greetings, chat, or diagnostics."
            )
        }
        # Memory Buffer
        self.messages = [self.system_prompt]
        
        # Available tools for the LLM
        self.tools = [get_weather, toggle_smart_lights, get_current_time, search_wikipedia, get_latest_news]
        
        # Async Queues (Connected in main.py)
        self.tts_queue = asyncio.Queue()
        
    def should_enable_tools(self, text: str) -> bool:
        """Detects if the user's query requires tool-calling capabilities."""
        text_lower = text.lower()
        
        # Tool-specific keywords
        tool_keywords = [
            "weather", "temperature", "forecast", "temp", "rain", "sunny", "hot", "cold",
            "light", "lamp", "turn on", "turn off", "switch on", "switch off", "toggle",
            "time", "clock", "date", "day is it",
            "search", "wikipedia", "who is", "tell me about", "what is", "explain", "info", "history of",
            "how to", "who was", "where is", "where was", "current", "latest", "news", "president", "today", "yesterday"
        ]
        
        return any(kw in text_lower for kw in tool_keywords)
        
    def _add_to_memory(self, role: str, content: str = "", tool_calls: list = None):
        """Append messages to the conversation buffer."""
        msg = {"role": role, "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)
        
        # Memory pruning (keep last 20 messages to prevent context overflow)
        if len(self.messages) > 20:
            self.messages = [self.system_prompt] + self.messages[-19:]

    async def _execute_tool(self, tool_call) -> str:
        """Dynamically matches the tool call from the LLM to our Python functions."""
        func_name = tool_call.function.name
        kwargs = tool_call.function.arguments
        
        # Match function name to actual Python function
        for tool in self.tools:
            if tool.__name__ == func_name:
                # Run the function in a non-blocking thread just in case it makes HTTP requests
                result = await asyncio.to_thread(tool, **kwargs)
                return str(result)
        return "Tool not found."

    async def process_text_queue(self, stt_text_queue: asyncio.Queue, barge_in_event: asyncio.Event):
        """Consumes text from STT, queries the LLM, and streams sentences to TTS."""
        print("🧠 LLM Engine ready. Waiting for text...")
        
        while True:
            user_text = await stt_text_queue.get()
            self._add_to_memory("user", user_text)
            
            # Reset barge-in state before we start generating
            barge_in_event.clear()
            
            await self._generate_response(barge_in_event)

    async def _generate_response(self, barge_in_event: asyncio.Event):
        """Handles the streaming API call and Tool execution."""
        
        print("🧠 Thinking...")
        
        # Get the latest user query to check if we should enable tools
        latest_user_text = ""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                latest_user_text = msg["content"]
                break
                
        # Detect if we should expose tools to the LLM based on keywords
        use_tools = self.should_enable_tools(latest_user_text)
        tools_to_pass = self.tools if use_tools else None
        
        # 1. Call Ollama with Streaming and Tools conditionally enabled
        response_stream = await self.client.chat(
            model=self.model,
            messages=self.messages,
            tools=tools_to_pass,
            stream=True,
            options={
                "temperature": 0.0,       # Fast greedy decoding
                "num_ctx": 1024,          # Lower context load overhead
                "num_predict": 50         # Prevent long-tail generation delays
            }
        )

        current_sentence = ""
        full_response = ""
        tool_calls_buffer = []
        
        # 2. Iterate over the stream
        async for chunk in response_stream:
            # --- INTERRUPT CHECK ---
            if barge_in_event.is_set():
                print("🛑 [LLM] Barge-in detected! Halting generation.")
                break # Exit the stream immediately!

            message = chunk.message
            
            # --- TOOL CALL HANDLING ---
            if message.tool_calls:
                tool_calls_buffer.extend(message.tool_calls)
                continue # Skip processing text while gathering tool arguments
                
            # --- TEXT STREAMING & SENTENCE CHUNKING ---
            if message.content:
                text_chunk = message.content
                current_sentence += text_chunk
                full_response += text_chunk
                
                # If we hit punctuation, flush the sentence to the TTS queue!
                # We use a negative lookbehind (?<!\d) to prevent splitting on numbers (like "5. ")
                # We also split the string exactly at the punctuation index to prevent cutting words in half!
                match = re.search(r'(?<!\d)[.!?]\s', current_sentence)
                if match:
                    split_idx = match.end()
                    clean_sentence = current_sentence[:split_idx].strip()
                    # Skip raw JSON blocks to prevent them from being spoken aloud
                    if not (clean_sentence.startswith("{") and clean_sentence.endswith("}")):
                        await self.tts_queue.put(clean_sentence)
                    current_sentence = current_sentence[split_idx:]

        # Flush any remaining text in the buffer
        if current_sentence.strip() and not barge_in_event.is_set():
            clean_sentence = current_sentence.strip()
            if not (clean_sentence.startswith("{") and clean_sentence.endswith("}")):
                await self.tts_queue.put(clean_sentence)

        # 3. Post-Generation Processing
        if tool_calls_buffer and not barge_in_event.is_set():
            # Save the assistant's decision to call a tool to memory
            self._add_to_memory("assistant", "", tool_calls=tool_calls_buffer)
            
            for tool_call in tool_calls_buffer:
                tool_result = await self._execute_tool(tool_call)
                
                # Append tool result to memory
                self.messages.append({
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": tool_result
                })
                
            # The LLM now has the tool data. We must trigger it again to synthesize a spoken answer.
            await self._generate_response(barge_in_event)
            
        elif full_response:
            # Standard conversational response
            self._add_to_memory("assistant", full_response)
            
            # Send a special signal to the TTS engine that the LLM is done thinking
            await self.tts_queue.put("<END_OF_TURN>")


# --- Integration Example ---
async def main():
    stt_queue = asyncio.Queue()
    barge_in_event = asyncio.Event()
    
    llm = LLMEngine()
    
    # Start LLM background task
    asyncio.create_task(llm.process_text_queue(stt_queue, barge_in_event))
    
    # Mock STT input
    await stt_queue.put("Turn off the kitchen lights, and then tell me the weather in Tokyo.")
    
    # Mock TTS consumer
    while True:
        sentence = await llm.tts_queue.get()
        if sentence == "<END_OF_TURN>":
            print("🏁 LLM finished its turn.")
            break
        print(f"➡️ Sent to TTS: {sentence}")

if __name__ == "__main__":
    asyncio.run(main())