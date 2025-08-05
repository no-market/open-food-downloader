#!/usr/bin/env python3
"""
Test conversation export functionality.
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, Mock

from openai_assistant import OpenAIAssistant


class TestConversationExport(unittest.TestCase):
    """Test conversation export functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset singleton instance for each test
        OpenAIAssistant._instance = None
        OpenAIAssistant._initialized = False
    
    def test_export_conversations_both_levels(self):
        """Test exporting conversations for both levels."""
        assistant = OpenAIAssistant()
        
        # Mock conversation data
        assistant.level1_conversation = [
            {"role": "system", "content": "Level 1 system message"},
            {"role": "user", "content": "Test query"},
            {"role": "assistant", "content": "Level 1 response"}
        ]
        
        assistant.level2_conversation = [
            {"role": "system", "content": "Level 2 system message"},
            {"role": "user", "content": "Test query"},
            {"role": "assistant", "content": "Level 2 response"}
        ]
        
        # Test export with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = assistant.export_conversations(temp_dir)
            
            # Check that both files were exported
            self.assertIn("level1", exported_files)
            self.assertIn("level2", exported_files)
            
            # Verify files exist
            level1_file = exported_files["level1"]
            level2_file = exported_files["level2"]
            
            self.assertTrue(os.path.exists(level1_file))
            self.assertTrue(os.path.exists(level2_file))
            
            # Verify file contents
            with open(level1_file, 'r') as f:
                level1_data = json.load(f)
                self.assertEqual(level1_data["model"], "gpt-3.5-turbo")
                self.assertEqual(level1_data["total_messages"], 3)
                self.assertEqual(len(level1_data["conversation"]), 3)
                self.assertIn("exported_at", level1_data)
            
            with open(level2_file, 'r') as f:
                level2_data = json.load(f)
                self.assertEqual(level2_data["model"], "gpt-4")
                self.assertEqual(level2_data["total_messages"], 3)
                self.assertEqual(len(level2_data["conversation"]), 3)
                self.assertIn("exported_at", level2_data)
    
    def test_export_conversations_level1_only(self):
        """Test exporting conversation for level 1 only."""
        assistant = OpenAIAssistant()
        
        # Mock only level 1 conversation
        assistant.level1_conversation = [
            {"role": "system", "content": "Level 1 system message"},
            {"role": "user", "content": "Test query"},
            {"role": "assistant", "content": "Level 1 response"}
        ]
        
        # Ensure level 2 is empty
        assistant.level2_conversation = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = assistant.export_conversations(temp_dir)
            
            # Check that only level 1 file was exported
            self.assertIn("level1", exported_files)
            self.assertNotIn("level2", exported_files)
            
            # Verify file exists
            level1_file = exported_files["level1"]
            self.assertTrue(os.path.exists(level1_file))
    
    def test_export_conversations_no_conversations(self):
        """Test exporting when no conversations exist."""
        assistant = OpenAIAssistant()
        
        # Ensure both conversations are empty
        assistant.level1_conversation = []
        assistant.level2_conversation = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = assistant.export_conversations(temp_dir)
            
            # Check that no files were exported
            self.assertEqual(len(exported_files), 0)
    
    def test_export_conversations_default_directory(self):
        """Test exporting to default directory."""
        assistant = OpenAIAssistant()
        
        # Mock level 1 conversation
        assistant.level1_conversation = [
            {"role": "user", "content": "Test query"},
            {"role": "assistant", "content": "Test response"}
        ]
        
        try:
            # Export to current directory
            exported_files = assistant.export_conversations()
            
            # Check that file was exported
            self.assertIn("level1", exported_files)
            
            # Verify file exists in current directory
            level1_file = exported_files["level1"]
            self.assertTrue(os.path.exists(level1_file))
            self.assertTrue(level1_file.endswith("openai_level1_conversation.json"))
            
        finally:
            # Clean up any files created in current directory
            for file in ["openai_level1_conversation.json", "openai_level2_conversation.json"]:
                if os.path.exists(file):
                    os.remove(file)
    
    def test_conversation_export_handles_unicode(self):
        """Test that conversation export handles unicode characters properly."""
        assistant = OpenAIAssistant()
        
        # Mock conversation with unicode characters
        assistant.level1_conversation = [
            {"role": "user", "content": "Błękitne borówki 500g"},
            {"role": "assistant", "content": "Znaleziono: borówka amerykańska 🫐"}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = assistant.export_conversations(temp_dir)
            
            # Verify file was created and contains unicode
            level1_file = exported_files["level1"]
            with open(level1_file, 'r', encoding='utf-8') as f:
                level1_data = json.load(f)
                
            # Check unicode content is preserved
            self.assertIn("Błękitne", level1_data["conversation"][0]["content"])
            self.assertIn("🫐", level1_data["conversation"][1]["content"])


if __name__ == "__main__":
    print("Testing Conversation Export Functionality...")
    print("=" * 50)
    
    unittest.main(verbosity=2)