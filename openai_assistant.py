#!/usr/bin/env python3
"""
OpenAI Assistant for product query processing.
Implements two-stage GPT-3.5 and GPT-4 assistance for improving product name matching.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Model name constants - configurable
LEVEL_1_MODEL = "gpt-3.5-turbo"
LEVEL_2_MODEL = "gpt-4"

# Score threshold to trigger OpenAI assistance
SCORE_THRESHOLD = 55.0


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
            self.gpt35_conversation = []
            self.gpt4_conversation = []
            self.gpt35_first_call = True
            self.gpt4_first_call = True
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
    
    def process_with_gpt35(self, search_string: str, top_result_name: Optional[str] = None) -> OpenAIResult:
        """
        Process search query with GPT-3.5 for initial analysis and rephrasing.
        
        Args:
            search_string: Original search string
            top_result_name: Top search result name from fuzzy search (optional)
            
        Returns:
            OpenAIResult with GPT-3.5 analysis
        """
        if not self.client:
            return OpenAIResult(
                model=LEVEL_1_MODEL,
                decision="no_match_found",
                error="OpenAI client not available"
            )
        
        try:
            # Create user prompt with minimal context
            user_prompt = self._create_gpt35_user_prompt(search_string, top_result_name)
            
            # For first call, initialize conversation with system message
            if self.gpt35_first_call:
                self.gpt35_conversation = [
                    {"role": "system", "content": self._get_gpt35_system_message()}
                ]
                self.gpt35_first_call = False
            
            # Add user message to conversation
            self.gpt35_conversation.append({"role": "user", "content": user_prompt})
            
            # Call GPT-3.5 with conversation history
            response = self.client.chat.completions.create(
                model=LEVEL_1_MODEL,
                messages=self.gpt35_conversation,
                temperature=0.3,
                max_tokens=500
            )
            
            # Add assistant response to conversation history
            assistant_response = response.choices[0].message.content
            self.gpt35_conversation.append({"role": "assistant", "content": assistant_response})
            
            # Parse response
            return self._parse_gpt35_response(response, search_string)
            
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_1_MODEL,
                decision="no_match_found",
                error=f"Level 1 model error: {str(e)}"
            )
    
    def process_with_gpt4(self, search_string: str, top_result_name: Optional[str] = None, 
                         level1_result: Optional[OpenAIResult] = None) -> OpenAIResult:
        """
        Process search query with GPT-4 for advanced analysis.
        
        Args:
            search_string: Original search string
            top_result_name: Top search result name from fuzzy search (optional)
            level1_result: Previous Level 1 model result (optional)
            
        Returns:
            OpenAIResult with GPT-4 analysis
        """
        if not self.client:
            return OpenAIResult(
                model=LEVEL_2_MODEL,
                decision="no_match_found",
                error="OpenAI client not available"
            )
        
        try:
            # Create user prompt with minimal context
            user_prompt = self._create_gpt4_user_prompt(search_string, top_result_name, level1_result)
            
            # For first call, initialize conversation with system message
            if self.gpt4_first_call:
                self.gpt4_conversation = [
                    {"role": "system", "content": self._get_gpt4_system_message()}
                ]
                self.gpt4_first_call = False
            
            # Add user message to conversation
            self.gpt4_conversation.append({"role": "user", "content": user_prompt})
            
            # Call GPT-4 with conversation history
            response = self.client.chat.completions.create(
                model=LEVEL_2_MODEL,
                messages=self.gpt4_conversation,
                temperature=0.2,
                max_tokens=600
            )
            
            # Add assistant response to conversation history
            assistant_response = response.choices[0].message.content
            self.gpt4_conversation.append({"role": "assistant", "content": assistant_response})
            
            # Parse response
            return self._parse_gpt4_response(response, search_string)
            
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_2_MODEL,
                decision="no_match_found",
                error=f"Level 2 model error: {str(e)}"
            )
    
    def _get_gpt35_system_message(self) -> str:
        """Get system message for Level 1 model."""
        return """You are a food product search assistant that helps analyze and improve product search queries.

Your task is to analyze search queries and provide responses in this exact JSON format:
{
    "decision": "valid_product|rephrased_successfully|not_a_product|no_match_found",
    "rephrased_query": "improved search query if applicable"
}

Decision meanings:
- valid_product: Query looks like a valid food product
- rephrased_successfully: Query was improved/rephrased for better search
- not_a_product: Query doesn't seem to be a food product
- no_match_found: Unable to help improve the search

Focus on:
1. Is this a valid food product query?
2. Can you rephrase it to improve matching?
3. Are there common misspellings or abbreviations to expand?
4. Is the language/format causing search issues?"""

    def _get_gpt4_system_message(self) -> str:
        """Get system message for Level 2 model."""
        return """You are an advanced food product search assistant with deep knowledge of food products, brands, and multilingual product names.

Your task is to provide advanced analysis of search queries in this exact JSON format:
{
    "decision": "valid_product|rephrased_successfully|not_a_product|no_match_found",
    "rephrased_query": "improved search query if applicable"
}

Use your advanced knowledge to:
1. Identify brand names, product types, and regional variations
2. Handle abbreviations, Polish/multilingual text, and colloquialisms
3. Recognize receipt-style text (e.g., "ParówKurNatTarcz160g")
4. Suggest better search terms that might match the database
5. Consider if this is truly a food product or something else

Be more sophisticated than initial analysis and provide the best possible search strategy."""

    def _create_gpt35_user_prompt(self, search_string: str, top_result_name: Optional[str]) -> str:
        """Create user prompt for Level 1 model with minimal context."""
        prompt = f'Search Query: "{search_string}"'
        
        if top_result_name:
            prompt += f'\nTop Result: "{top_result_name}"'
        
        return prompt

    def _create_gpt4_user_prompt(self, search_string: str, top_result_name: Optional[str], 
                                level1_result: Optional[OpenAIResult]) -> str:
        """Create user prompt for Level 2 model with minimal context."""
        prompt = f'Search Query: "{search_string}"'
        
        if top_result_name:
            prompt += f'\nTop Result: "{top_result_name}"'
        
        if level1_result:
            prompt += f'\nPrevious Analysis: {level1_result.decision}'
            if level1_result.rephrased_query:
                prompt += f', suggested: "{level1_result.rephrased_query}"'
        
        return prompt
    
    def _parse_gpt35_response(self, response, search_string: str) -> OpenAIResult:
        """Parse GPT-3.5 response."""
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
    
    def _parse_gpt4_response(self, response, search_string: str) -> OpenAIResult:
        """Parse GPT-4 response."""
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


def create_research_function(collection):
    """
    Create a re-search function for use with OpenAI assistance.
    
    Args:
        collection: MongoDB collection for searching
        
    Returns:
        Function that can perform search with a new query string
    """
    def research_with_query(new_search_string: str) -> List[Dict[str, Any]]:
        """Perform search with new query string and return results with rapidfuzz scores."""
        try:
            # Import search functions (avoid circular imports)
            from utils import format_search_string, compute_given_name
            
            # Format the new search string 
            formatted_string = format_search_string(new_search_string)
            
            # Perform direct search (same logic as search_products_direct)
            search_terms = re.findall(r'\b\w+\b', formatted_string.lower())
            
            if not search_terms:
                return []
            
            # Build MongoDB query
            regex_query = {
                "$text": {
                    "$search": " ".join(search_terms)
                }
            }
            
            # Execute search
            cursor = collection.find(regex_query, {"score": {"$meta": "textScore"}})
            cursor = cursor.sort([("score", {"$meta": "textScore"})])
            results = list(cursor)
            
            # Add RapidFuzz scores and given_name
            from utils import compute_rapidfuzz_score
            for result in results:
                result['rapidfuzz_score'] = compute_rapidfuzz_score(new_search_string, result)
                result['given_name'] = compute_given_name(result)
            
            # Sort by RapidFuzz score
            results.sort(key=lambda x: x.get('rapidfuzz_score', 0), reverse=True)
            
            return results
            
        except Exception as e:
            print(f"Warning: Re-search failed: {e}")
            return []
    
    return research_with_query


def process_openai_assistance(search_string: str, rapidfuzz_results: List[Dict[str, Any]], 
                             search_function=None) -> Tuple[Optional[OpenAIResult], Optional[OpenAIResult]]:
    """
    Main function to process OpenAI assistance for a search query with re-search logic.
    
    Args:
        search_string: The search query string
        rapidfuzz_results: Results from RapidFuzz search
        search_function: Function to perform search again (for re-search logic)
        
    Returns:
        Tuple of (level1_result, level2_result) - may be None if not needed/available
    """
    if not rapidfuzz_results:
        return None, None
    
    # Get best RapidFuzz score and top result name
    best_score = max(result.get('rapidfuzz_score', 0) for result in rapidfuzz_results)
    top_result_name = rapidfuzz_results[0].get('given_name') if rapidfuzz_results else None
    
    # Initialize assistant (singleton)
    assistant = OpenAIAssistant()
    
    # Check if OpenAI assistance is needed
    if not assistant.should_use_openai(best_score):
        return None, None
    
    print(f"RapidFuzz score {best_score:.1f} is below threshold {SCORE_THRESHOLD}, using OpenAI assistance...")
    
    # Process with Level 1 model
    level1_result = assistant.process_with_gpt35(search_string, top_result_name)
    
    # Check if Level 1 provided a rephrased query and we have a search function
    if (level1_result.decision == "rephrased_successfully" and 
        level1_result.rephrased_query and 
        search_function):
        
        print(f"Level 1 model suggested '{level1_result.rephrased_query}', performing re-search...")
        
        # Perform re-search with the rephrased query
        try:
            research_results = search_function(level1_result.rephrased_query)
            if research_results:
                research_best_score = max(result.get('rapidfuzz_score', 0) for result in research_results)
                print(f"Re-search best score: {research_best_score:.1f}")
                
                # If re-search score is good enough, skip Level 2 model
                if research_best_score >= SCORE_THRESHOLD:
                    print(f"Re-search score {research_best_score:.1f} is above threshold, skipping Level 2 model")
                    return level1_result, None
                else:
                    print(f"Re-search score {research_best_score:.1f} still below threshold, continuing to Level 2 model")
                    # Update top result name for Level 2 model
                    top_result_name = research_results[0].get('given_name') if research_results else top_result_name
        except Exception as e:
            print(f"Warning: Re-search failed: {e}")
    
    # Process with Level 2 model
    level2_result = assistant.process_with_gpt4(search_string, top_result_name, level1_result)
    
    return level1_result, level2_result