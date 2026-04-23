"""
tests/test_content_analyst.py — Evaluation script for the Content Analyst Agent (Member 2)

"""

import unittest
import os
import json
from unittest.mock import patch, MagicMock
from tools.fetch_resource import fetch_resource
from agents.content_analyst import content_analyst_node

class TestContentAnalyst(unittest.TestCase):

    # ----------------------------------------------------------------------
    # 1. Unit tests for fetch_resource() tool
    # ----------------------------------------------------------------------
    
    @patch('requests.get')
    def test_fetch_resource_success(self, mock_get):
        """check if fetch_resource successfully retrieves content and handles truncation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"extract": "Chloroplasts are organelles found in plant cells."}        
        
        mock_get.return_value = mock_response
        
        result = fetch_resource("Chloroplast", max_chars=20)
                
        self.assertTrue(result["success"]) 
        self.assertEqual(len(result["content"]), 20)  
        self.assertEqual(result["source"], "Wikipedia API") 

    def test_fetch_resource_empty_query(self):
        """check if fetch_resource raises ValueError when query is empty."""
        with self.assertRaises(ValueError):
            fetch_resource("") 

    @patch('requests.get')
    def test_fetch_resource_network_error(self, mock_get):
        """Check if network error occurs, the function should handle it gracefully and return success=False"""
        mock_get.side_effect = Exception("Connection Timeout")
        result = fetch_resource("Photosynthesis")
        self.assertFalse(result["success"]) 
        self.assertIn("Error", result["content"])

    # ----------------------------------------------------------------------
    # 2. Integration tests for content_analyst_node()
    # ----------------------------------------------------------------------

    @patch('agents.content_analyst.ChatOllama')
    @patch('agents.content_analyst.fetch_resource')
    def test_content_analyst_node_integration(self, mock_fetch, mock_llm):
        """Check if content_analyst_node correctly integrates fetch_resource and LLM to produce notes and logs."""
        # Mocking values
        mock_fetch.return_value = {"success": True, "content": "Fake resource text", "query": "test", "source": "test"}
        mock_llm.return_value.invoke.return_value.content = "# Study Notes\n## Subtopic 1\nContent" 
        
        initial_state = {
            "topic": "Biology",
            "grade_level": 10,
            "syllabus": {"topic": "Biology", "subtopics": ["Subtopic 1"]},
            "log": []
        }
        
        result = content_analyst_node(state=initial_state)
        
        self.assertIn("notes", result)
        self.assertTrue(result["notes"].startswith("#")) # Markdown check
        self.assertEqual(len(result["log"]), 1) # Logging check
        
        out_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "notes.md")
        self.assertTrue(os.path.exists(out_path))

    # ----------------------------------------------------------------------
    # 3. LLM-as-Judge (Real Ollama test)
    # ----------------------------------------------------------------------

    def test_llm_judge_coherence(self):
        """Check if an actual LLM can judge the quality of generated notes."""
        from langchain_ollama import ChatOllama
        
        generated_notes = "# Photosynthesis\n## Light Reaction\nDetails about light."
        judge_llm = ChatOllama(model="gemma3:1b")
        
        judge_prompt = (
            f"As an educational supervisor, grade the following study notes from 1-10 "
            f"based on clarity and grade-appropriateness: \n{generated_notes}\n"
            "Respond ONLY with the number."
        )
        
        
        try:
            response = judge_llm.invoke(judge_prompt).content.strip()
            score = int(''.join(filter(str.isdigit, response)))
            self.assertGreaterEqual(score, 3) 
        except ValueError:
            print(f"Judge returned non-numeric score: {response}")

if __name__ == "__main__":
    unittest.main()
