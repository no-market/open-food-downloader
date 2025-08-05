#!/usr/bin/env python3
"""
OpenAI Assistant for product query processing.
Implements two-stage Level 1 and Level 2 model assistance for improving product name matching.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Model name constants - configurable
LEVEL_1_MODEL = "gpt-3.5-turbo"
LEVEL_2_MODEL = "gpt-4"

# Score threshold to trigger OpenAI assistance
SCORE_THRESHOLD = 550.0


@dataclass
class OpenAIResult:
    """Data class for OpenAI search results."""
    model: str
    decision: str  # valid_product, rephrased_successfully, not_a_product, no_match_found
    rephrased_query: Optional[str] = None
    error: Optional[str] = None


class OpenAIAssistant:
    """OpenAI Assistant for product query processing with singleton pattern."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(OpenAIAssistant, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize OpenAI client only once."""
        if not self._initialized:
            self.client = None
            self._init_client()
            # Track conversation history for each model
            self.level1_conversation = []
            self.level2_conversation = []
            self.level1_first_call = True
            self.level2_first_call = True
            OpenAIAssistant._initialized = True
    
    def _init_client(self):
        """Initialize OpenAI client with API key from environment."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("Warning: OPENAI_API_KEY environment variable not set")
                return
            
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            
        except ImportError:
            print("Warning: OpenAI package not installed. Run: pip install openai")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
    
    def should_use_openai(self, rapidfuzz_score: float) -> bool:
        """
        Determine if OpenAI assistance should be used based on fuzzy search score.
        
        Args:
            rapidfuzz_score: The best RapidFuzz score from search results
            
        Returns:
            True if OpenAI assistance should be used
        """
        return rapidfuzz_score < SCORE_THRESHOLD
    
    def process_with_level1(self, search_string: str, top_result_name: Optional[str] = None) -> OpenAIResult:
        """
        Process search query with Level 1 model for initial analysis and rephrasing.
        
        Args:
            search_string: Original search string
            top_result_name: Top search result name from fuzzy search (optional)
            
        Returns:
            OpenAIResult with Level 1 model analysis
        """
        if not self.client:
            return OpenAIResult(
                model=LEVEL_1_MODEL,
                decision="no_match_found",
                error="OpenAI client not available"
            )
        
        try:
            # Create user prompt with minimal context
            user_prompt = self._create_level1_user_prompt(search_string, top_result_name)
            
            # For first call, initialize conversation with system message
            if self.level1_first_call:
                self.level1_conversation = [
                    {"role": "system", "content": self._get_level1_system_message()}
                ]
                self.level1_first_call = False
            
            # Add user message to conversation
            self.level1_conversation.append({"role": "user", "content": user_prompt})
            
            # Call Level 1 model with conversation history
            response = self.client.chat.completions.create(
                model=LEVEL_1_MODEL,
                messages=self.level1_conversation,
                temperature=0.3,
                max_tokens=500
            )
            
            # Add assistant response to conversation history
            assistant_response = response.choices[0].message.content
            self.level1_conversation.append({"role": "assistant", "content": assistant_response})
            
            # Parse response
            return self._parse_level1_response(response, search_string)
            
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_1_MODEL,
                decision="no_match_found",
                error=f"Level 1 model error: {str(e)}"
            )
    
    def process_with_level2(self, search_string: str, top_result_name: Optional[str] = None, 
                         level1_result: Optional[OpenAIResult] = None) -> OpenAIResult:
        """
        Process search query with Level 2 model for advanced analysis.
        
        Args:
            search_string: Original search string
            top_result_name: Top search result name from fuzzy search (optional)
            level1_result: Previous Level 1 model result (optional)
            
        Returns:
            OpenAIResult with Level 2 model analysis
        """
        if not self.client:
            return OpenAIResult(
                model=LEVEL_2_MODEL,
                decision="no_match_found",
                error="OpenAI client not available"
            )
        
        try:
            # Create user prompt with minimal context
            user_prompt = self._create_level2_user_prompt(search_string, top_result_name, level1_result)
            
            # For first call, initialize conversation with system message
            if self.level2_first_call:
                self.level2_conversation = [
                    {"role": "system", "content": self._get_level2_system_message()}
                ]
                self.level2_first_call = False
            
            # Add user message to conversation
            self.level2_conversation.append({"role": "user", "content": user_prompt})
            
            # Call Level 2 model with conversation history
            response = self.client.chat.completions.create(
                model=LEVEL_2_MODEL,
                messages=self.level2_conversation,
                temperature=0.2,
                max_tokens=600
            )
            
            # Add assistant response to conversation history
            assistant_response = response.choices[0].message.content
            self.level2_conversation.append({"role": "assistant", "content": assistant_response})
            
            # Parse response
            return self._parse_level2_response(response, search_string)
            
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_2_MODEL,
                decision="no_match_found",
                error=f"Level 2 model error: {str(e)}"
            )
    
    def _get_level1_system_message(self) -> str:
        """Get system message for Level 1 model."""
        return """You are a food product search assistant that helps validate search results and improve product search queries.

You will receive a user's search query and a possible result from the database. Your task is to determine if the possible result matches what the user was actually looking for, or if the search needs improvement.

Provide responses in this exact JSON format:
{
    "decision": "valid_product|rephrased_successfully|not_a_product|no_match_found",
    "rephrased_query": "improved search query if applicable"
}

Decision meanings:
- valid_product: The possible result matches what the user was searching for (good match found)
- rephrased_successfully: The possible result doesn't match, but you can suggest better search terms
- not_a_product: The user's search query doesn't appear to be for a food product
- no_match_found: Unable to help improve the search

Evaluation process:
1. Analyze the user's search query to understand what food product they want
2. Check if the possible result matches their intent
3. If no match, determine if you can suggest better search terms
4. Consider misspellings, abbreviations, language issues, or formatting problems"""

    def _get_level2_system_message(self) -> str:
        """Get system message for Level 2 model."""
        return """You are an advanced food product search assistant with deep knowledge of food products, brands, and multilingual product names.

You will receive a user's search query and a possible result from the database. Your task is to provide advanced analysis to determine if the possible result matches what the user was looking for, or suggest sophisticated search improvements.

Provide responses in this exact JSON format:
{
    "decision": "valid_product|rephrased_successfully|not_a_product|no_match_found",
    "rephrased_query": "improved search query if applicable"
}

Use your advanced knowledge for:
1. Deep analysis of the user's intent from their search query
2. Sophisticated matching between search intent and possible result
3. Advanced handling of brand names, product types, and regional variations
4. Complex abbreviations, Polish/multilingual text, and colloquialisms
5. Recognition of receipt-style text (e.g., "ParówKurNatTarcz160g")
6. Suggesting optimal search terms that might better match the database
7. Advanced determination if this is truly a food product

Apply sophisticated reasoning beyond basic analysis to provide the best possible search strategy."""

    def _create_level1_user_prompt(self, search_string: str, top_result_name: Optional[str]) -> str:
        """Create user prompt for Level 1 model with minimal context."""
        prompt = f'User Search Query: "{search_string}"'
        
        if top_result_name:
            prompt += f'\nPossible Result: "{top_result_name}"'
        
        return prompt

    def _create_level2_user_prompt(self, search_string: str, top_result_name: Optional[str], 
                                level1_result: Optional[OpenAIResult]) -> str:
        """Create user prompt for Level 2 model with minimal context."""
        prompt = f'User Search Query: "{search_string}"'
        
        if top_result_name:
            prompt += f'\nPossible Result: "{top_result_name}"'
        
        if level1_result:
            prompt += f'\nPrevious Analysis: {level1_result.decision}'
            if level1_result.rephrased_query:
                prompt += f', suggested: "{level1_result.rephrased_query}"'
        
        return prompt
    
    def _parse_level1_response(self, response, search_string: str) -> OpenAIResult:
        """Parse Level 1 model response."""
        try:
            content = response.choices[0].message.content
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return OpenAIResult(
                    model=LEVEL_1_MODEL,
                    decision=data.get('decision', 'no_match_found'),
                    rephrased_query=data.get('rephrased_query')
                )
            else:
                # Fallback: try to extract decision from text
                content_lower = content.lower()
                if 'not_a_product' in content_lower:
                    decision = 'not_a_product'
                elif 'rephrased' in content_lower or 'improved' in content_lower:
                    decision = 'rephrased_successfully'
                elif 'valid' in content_lower:
                    decision = 'valid_product'
                else:
                    decision = 'no_match_found'
                
                return OpenAIResult(
                    model=LEVEL_1_MODEL,
                    decision=decision
                )
                
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_1_MODEL,
                decision="no_match_found",
                error=f"Failed to parse Level 1 model response: {str(e)}"
            )
    
    def _parse_level2_response(self, response, search_string: str) -> OpenAIResult:
        """Parse Level 2 model response."""
        try:
            content = response.choices[0].message.content
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return OpenAIResult(
                    model=LEVEL_2_MODEL,
                    decision=data.get('decision', 'no_match_found'),
                    rephrased_query=data.get('rephrased_query')
                )
            else:
                # Fallback: try to extract decision from text
                content_lower = content.lower()
                if 'not_a_product' in content_lower:
                    decision = 'not_a_product'
                elif 'rephrased' in content_lower or 'improved' in content_lower:
                    decision = 'rephrased_successfully'
                elif 'valid' in content_lower:
                    decision = 'valid_product'
                else:
                    decision = 'no_match_found'
                
                return OpenAIResult(
                    model=LEVEL_2_MODEL,
                    decision=decision
                )
                
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_2_MODEL,
                decision="no_match_found",
                error=f"Failed to parse Level 2 model response: {str(e)}"
            )
    
    def export_conversations(self, output_dir: str = ".") -> Dict[str, str]:
        """
        Export conversation histories to JSON files.
        
        Args:
            output_dir: Directory to save conversation files
            
        Returns:
            Dictionary with file paths for exported conversations
        """
        exported_files = {}
        
        try:
            # Export Level 1 conversation if it exists
            if self.level1_conversation:
                level1_file = os.path.join(output_dir, "openai_level1_conversation.json")
                with open(level1_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "model": LEVEL_1_MODEL,
                        "conversation": self.level1_conversation,
                        "total_messages": len(self.level1_conversation),
                        "exported_at": datetime.now().isoformat()
                    }, f, indent=2, ensure_ascii=False)
                exported_files["level1"] = level1_file
                print(f"Exported Level 1 conversation to: {level1_file}")
            
            # Export Level 2 conversation if it exists
            if self.level2_conversation:
                level2_file = os.path.join(output_dir, "openai_level2_conversation.json")
                with open(level2_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "model": LEVEL_2_MODEL,
                        "conversation": self.level2_conversation,
                        "total_messages": len(self.level2_conversation),
                        "exported_at": datetime.now().isoformat()
                    }, f, indent=2, ensure_ascii=False)
                exported_files["level2"] = level2_file
                print(f"Exported Level 2 conversation to: {level2_file}")
                
        except Exception as e:
            print(f"Warning: Failed to export conversations: {e}")
        
        return exported_files

