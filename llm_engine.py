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

def search_web(query: str) -> str:
    """Search the web to get the most current, real-time live web information, facts, stock prices, scores, or news."""
    print(f"🔧 [Tool Execution] Searching the web for '{query}'...")
    
    # 1. Fetch real-time stock price if querying for popular stock symbols
    stock_info = ""
    query_lower = query.lower()
    tickers = {
        "tesla": "TSLA",
        "apple": "AAPL",
        "microsoft": "MSFT",
        "google": "GOOGL",
        "amazon": "AMZN",
        "nvidia": "NVDA",
        "meta": "META",
        "netflix": "NFLX",
        "amd": "AMD",
        "intel": "INTC"
    }
    
    ticker_found = None
    for name, ticker in tickers.items():
        if name in query_lower:
            ticker_found = ticker
            break
            
    if ticker_found and any(w in query_lower for w in ["stock", "price", "share", "value"]):
        import urllib.request
        import json
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_found}?interval=1m&range=1d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                currency = meta.get("currency", "USD")
                if price:
                    stock_info = f"Real-Time Stock Price for {ticker_found}: {price:.2f} {currency}.\n\n"
        except Exception as e:
            print(f"[Stock Lookup] Failed to fetch ticker {ticker_found}: {e}")

    # 2. Query DuckDuckGo text search for general context
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=4)
            if not results:
                if stock_info:
                    return stock_info
                return f"No web search results found for '{query}'."
            
            reports = []
            for r in results:
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")
                reports.append(f"[{title}] ({href}): {body}")
                
            return stock_info + "Live Web Search Results:\n" + "\n\n".join(reports)
    except Exception as e:
        if stock_info:
            return stock_info
        return f"Error searching the web: {str(e)}"

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
        self.tools = [get_weather, toggle_smart_lights, get_current_time, search_wikipedia, get_latest_news, search_web]
        
        # Async Queues (Connected in main.py)
        self.tts_queue = asyncio.Queue()
        
    def get_relevant_tools(self, text: str) -> list:
        """Determines exactly which tools (if any) are relevant to the user query to prevent model confusion."""
        text_lower = text.lower()
        
        # 1. Filter out common conversational greetings to prevent search triggers
        greetings = ["how are you", "how is it going", "how's it going", "how are you doing", "what is up", "what's up", "whats up"]
        if any(g in text_lower for g in greetings):
            return []
            
        # 2. Weather Tool
        if any(kw in text_lower for kw in ["weather", "temperature", "forecast", "temp", "rain", "sunny", "hot", "cold"]):
            return [get_weather]
            
        # 3. Smart Lights Tool
        if any(kw in text_lower for kw in ["light", "lamp", "turn on", "turn off", "switch on", "switch off", "toggle"]):
            # Special check to make sure it's about lights, not general greetings/chat containing 'on' or 'off'
            if "light" in text_lower or "lamp" in text_lower or "switch" in text_lower:
                return [toggle_smart_lights]
                
        # 4. Time Tool
        if any(kw in text_lower for kw in ["time", "clock", "date", "day is it"]):
            return [get_current_time]
            
        # 5. News Tool
        if any(kw in text_lower for kw in ["breaking news", "happen today"]):
            return [get_latest_news]
            
        # 6. Live Web & General Knowledge Search Tool
        # Triggers for question words, entities, research, or real-time event topics
        search_keywords = [
            "who", "what", "where", "why", "how", "when", "which", "whose",
            "heard of", "know about", "know of", "do you know", "tell me",
            "search", "wikipedia", "news", "latest", "current", "today", "yesterday",
            "stock", "price", "score", "game", "winner", "who won", "dollar", "rate", "exchange",
            "happening", "right now", "situation", "whats going on", "what's going on"
        ]
        if any(kw in text_lower for kw in search_keywords):
            return [search_web]
            
        # No tools for general statements/chat
        return []
        
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
                
        # Dynamically determine the exact tools to pass based on keywords to prevent model confusion
        tools_to_pass = self.get_relevant_tools(latest_user_text) or None
        
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