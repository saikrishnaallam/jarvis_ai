import unittest
from unittest.mock import patch, MagicMock
import json
import datetime
import asyncio

# Import Jarvis modules
from llm_engine import LLMEngine, get_weather, toggle_smart_lights, get_current_time, search_wikipedia, get_latest_news
from audio_engine import AudioPipeline
from stt_engine import STTEngine
from tts_engine import TTSEngine

class TestJarvisVoiceAgent(unittest.TestCase):
    
    # =========================================================
    # 1. Custom Tools Tests
    # =========================================================
    
    def test_get_current_time(self):
        """Test get_current_time returns time in correct format."""
        time_str = get_current_time()
        self.assertTrue(time_str.startswith("The current time is"))
        
        # Verify time matches expected system AM/PM formatting
        now = datetime.datetime.now()
        expected_suffix = now.strftime("%p")
        self.assertIn(expected_suffix, time_str)

    def test_get_weather(self):
        """Test get_weather mock tool returns correct description."""
        res = get_weather("Miami")
        self.assertIn("Miami", res)
        self.assertIn("72°F and sunny", res)

    def test_toggle_smart_lights(self):
        """Test toggle_smart_lights returns light state transition message."""
        res = toggle_smart_lights("Living Room", "on")
        self.assertIn("Living Room", res)
        self.assertIn("turned on", res)

    @patch("urllib.request.urlopen")
    def test_search_wikipedia_success(self, mock_urlopen):
        """Test search_wikipedia successfully queries API and parses summary extracts."""
        # Mock JSON response for search results query
        mock_search_json = json.dumps({
            "query": {
                "search": [
                    {"title": "Artificial Intelligence"}
                ]
            }
        }).encode("utf-8")
        
        # Mock JSON response for page summary extract query
        mock_summary_json = json.dumps({
            "extract": "Artificial Intelligence is intelligence demonstrated by machines."
        }).encode("utf-8")
        
        # Create response mock objects
        response_search = MagicMock()
        response_search.read.return_value = mock_search_json
        
        response_summary = MagicMock()
        response_summary.read.return_value = mock_summary_json
        
        # Create context manager mock objects
        mock_search_cm = MagicMock()
        mock_search_cm.__enter__.return_value = response_search
        
        mock_summary_cm = MagicMock()
        mock_summary_cm.__enter__.return_value = response_summary
        
        # urlopen returns search results first, then page extract second
        mock_urlopen.side_effect = [mock_search_cm, mock_summary_cm]
        
        res = search_wikipedia("AI")
        
        self.assertIn("Artificial Intelligence", res)
        self.assertIn("intelligence demonstrated by machines", res)

    @patch("urllib.request.urlopen")
    def test_search_wikipedia_no_results(self, mock_urlopen):
        """Test search_wikipedia returns fallback message when no articles match."""
        mock_search_json = json.dumps({
            "query": {
                "search": []
            }
        }).encode("utf-8")
        
        response_search = MagicMock()
        response_search.read.return_value = mock_search_json
        
        mock_search_cm = MagicMock()
        mock_search_cm.__enter__.return_value = response_search
        
        mock_urlopen.return_value = mock_search_cm
        
        res = search_wikipedia("NonExistentTopic12345")
        self.assertIn("No Wikipedia results found", res)

    @patch("urllib.request.urlopen")
    def test_get_latest_news_success(self, mock_urlopen):
        """Test get_latest_news successfully queries Google News RSS and parses item titles."""
        mock_xml = """
        <rss>
            <channel>
                <item>
                    <title>Breaking News: AI takes over coding tasks</title>
                    <pubDate>Mon, 03 Aug 2026 12:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>
        """.encode("utf-8")
        
        response = MagicMock()
        response.read.return_value = mock_xml
        
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = response
        mock_urlopen.return_value = mock_cm
        
        res = get_latest_news()
        self.assertIn("Breaking News", res)

    # =========================================================
    # 2. LLMEngine Tests
    # =========================================================

    @patch("llm_engine.AsyncClient")
    def test_llm_engine_init(self, mock_async_client):
        """Test LLMEngine initializes prompts, memory buffers, and registers tools."""
        llm = LLMEngine()
        self.assertEqual(llm.model, "llama3.2")
        self.assertIn("You are Jarvis", llm.system_prompt["content"])
        self.assertEqual(len(llm.messages), 1)
        self.assertEqual(llm.messages[0]["role"], "system")
        self.assertIn(search_wikipedia, llm.tools)
        self.assertIn(get_latest_news, llm.tools)

    @patch("llm_engine.AsyncClient")
    def test_llm_memory_pruning(self, mock_async_client):
        """Test that LLMEngine prunes conversation history to prevent context overflow."""
        llm = LLMEngine()
        
        # Add 30 conversations (60 messages) to buffer
        for i in range(30):
            llm._add_to_memory("user", f"query {i}")
            llm._add_to_memory("assistant", f"response {i}")
            
        # Total messages in memory should stay capped to 20 (system prompt + 19 history)
        self.assertLessEqual(len(llm.messages), 20)
        self.assertEqual(llm.messages[0]["role"], "system")

    # =========================================================
    # 3. AudioPipeline Tests
    # =========================================================

    @patch("asyncio.get_running_loop")
    @patch("audio_engine.load_silero_vad")
    def test_audio_pipeline_init(self, mock_load_vad, mock_get_loop):
        """Test AudioPipeline initializes parameters and respects barge-in modes."""
        mock_get_loop.return_value = MagicMock()
        pipeline = AudioPipeline(barge_in_mode="headphones")
        self.assertEqual(pipeline.barge_in_mode, "headphones")
        self.assertEqual(pipeline.sample_rate, 16000)

if __name__ == "__main__":
    unittest.main()
