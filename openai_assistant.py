#!/usr/bin/env python3
"""
OpenAI Assistant for product query processing.
Implements two-stage GPT-3.5 and GPT-4 assistance for improving product name matching.
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Model name constants - configurable
LEVEL_1_MODEL = "gpt-3.5-turbo"
LEVEL_2_MODEL = "gpt-4"

# Score threshold to trigger OpenAI assistance
SCORE_THRESHOLD = 50.0


@dataclass
class OpenAIResult:
    """Data class for OpenAI search results."""
    model: str
    decision: str  # valid_product, rephrased_successfully, not_a_product, no_match_found
    rephrased_query: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""
    error: Optional[str] = None


class OpenAIAssistant:
    """OpenAI Assistant for product query processing."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = None
        self._init_client()
    
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
    
    def process_with_gpt35(self, search_string: str, search_results: List[Dict[str, Any]]) -> OpenAIResult:
        """
        Process search query with GPT-3.5 for initial analysis and rephrasing.
        
        Args:
            search_string: Original search string
            search_results: Current search results from MongoDB/RapidFuzz
            
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
            # Prepare context from search results
            context = self._prepare_search_context(search_results)
            
            # Create prompt for GPT-3.5
            prompt = self._create_gpt35_prompt(search_string, context)
            
            # Call GPT-3.5
            response = self.client.chat.completions.create(
                model=LEVEL_1_MODEL,
                messages=[
                    {"role": "system", "content": "You are a food product search assistant that helps analyze and improve product search queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            return self._parse_gpt35_response(response, search_string)
            
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_1_MODEL,
                decision="no_match_found",
                error=f"GPT-3.5 error: {str(e)}"
            )
    
    def process_with_gpt4(self, search_string: str, search_results: List[Dict[str, Any]], 
                         gpt35_result: OpenAIResult) -> OpenAIResult:
        """
        Process search query with GPT-4 for advanced analysis.
        
        Args:
            search_string: Original search string
            search_results: Current search results from MongoDB/RapidFuzz
            gpt35_result: Previous GPT-3.5 result
            
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
            # Prepare context from search results
            context = self._prepare_search_context(search_results)
            
            # Create prompt for GPT-4 with GPT-3.5 context
            prompt = self._create_gpt4_prompt(search_string, context, gpt35_result)
            
            # Call GPT-4
            response = self.client.chat.completions.create(
                model=LEVEL_2_MODEL,
                messages=[
                    {"role": "system", "content": "You are an advanced food product search assistant with deep knowledge of food products, brands, and multilingual product names."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )
            
            # Parse response
            return self._parse_gpt4_response(response, search_string)
            
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_2_MODEL,
                decision="no_match_found",
                error=f"GPT-4 error: {str(e)}"
            )
    
    def _prepare_search_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Prepare context from current search results for OpenAI prompts.
        
        Args:
            search_results: List of search results
            
        Returns:
            Formatted context string
        """
        if not search_results:
            return "No existing search results found."
        
        context_parts = []
        for i, result in enumerate(search_results[:5]):  # Limit to top 5 results
            product_name = result.get('given_name', 'Unknown')
            categories = result.get('categories', '')
            brands = result.get('brands', '')
            score = result.get('rapidfuzz_score', result.get('score', 0))
            
            context_parts.append(
                f"{i+1}. Product: {product_name}, "
                f"Categories: {categories}, "
                f"Brands: {brands}, "
                f"Score: {score:.1f}"
            )
        
        return "Current search results:\n" + "\n".join(context_parts)
    
    def _create_gpt35_prompt(self, search_string: str, context: str) -> str:
        """Create prompt for GPT-3.5 analysis."""
        return f"""
Analyze this food product search query and help improve it:

Search Query: "{search_string}"

{context}

Please analyze the search query and provide your response in this JSON format:
{{
    "decision": "valid_product|rephrased_successfully|not_a_product|no_match_found",
    "rephrased_query": "improved search query if applicable",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of your analysis"
}}

Decision meanings:
- valid_product: Query looks like a valid food product
- rephrased_successfully: Query was improved/rephrased for better search
- not_a_product: Query doesn't seem to be a food product
- no_match_found: Unable to help improve the search

Focus on:
1. Is this a valid food product query?
2. Can you rephrase it to improve matching?
3. Are there common misspellings or abbreviations to expand?
4. Is the language/format causing search issues?
"""
    
    def _create_gpt4_prompt(self, search_string: str, context: str, gpt35_result: OpenAIResult) -> str:
        """Create prompt for GPT-4 analysis."""
        gpt35_info = f"GPT-3.5 analysis: {gpt35_result.decision}"
        if gpt35_result.rephrased_query:
            gpt35_info += f", suggested: '{gpt35_result.rephrased_query}'"
        
        return f"""
Advanced analysis of this food product search query:

Search Query: "{search_string}"

{context}

Previous Analysis: {gpt35_info}

Please provide advanced analysis in this JSON format:
{{
    "decision": "valid_product|rephrased_successfully|not_a_product|no_match_found",
    "rephrased_query": "improved search query if applicable",
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation of your analysis"
}}

Use your advanced knowledge to:
1. Identify brand names, product types, and regional variations
2. Handle abbreviations, Polish/multilingual text, and colloquialisms
3. Recognize receipt-style text (e.g., "ParówKurNatTarcz160g")
4. Suggest better search terms that might match the database
5. Consider if this is truly a food product or something else

Be more sophisticated than the initial analysis and provide the best possible search strategy.
"""
    
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
                    rephrased_query=data.get('rephrased_query'),
                    confidence=float(data.get('confidence', 0.0)),
                    reasoning=data.get('reasoning', '')
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
                    decision=decision,
                    reasoning=content[:200] + "..." if len(content) > 200 else content
                )
                
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_1_MODEL,
                decision="no_match_found",
                error=f"Failed to parse GPT-3.5 response: {str(e)}"
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
                    rephrased_query=data.get('rephrased_query'),
                    confidence=float(data.get('confidence', 0.0)),
                    reasoning=data.get('reasoning', '')
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
                    decision=decision,
                    reasoning=content[:200] + "..." if len(content) > 200 else content
                )
                
        except Exception as e:
            return OpenAIResult(
                model=LEVEL_2_MODEL,
                decision="no_match_found",
                error=f"Failed to parse GPT-4 response: {str(e)}"
            )


def process_openai_assistance(search_string: str, rapidfuzz_results: List[Dict[str, Any]]) -> Tuple[Optional[OpenAIResult], Optional[OpenAIResult]]:
    """
    Main function to process OpenAI assistance for a search query.
    
    Args:
        search_string: The search query string
        rapidfuzz_results: Results from RapidFuzz search
        
    Returns:
        Tuple of (gpt35_result, gpt4_result) - may be None if not needed/available
    """
    if not rapidfuzz_results:
        return None, None
    
    # Get best RapidFuzz score
    best_score = max(result.get('rapidfuzz_score', 0) for result in rapidfuzz_results)
    
    # Initialize assistant
    assistant = OpenAIAssistant()
    
    # Check if OpenAI assistance is needed
    if not assistant.should_use_openai(best_score):
        return None, None
    
    print(f"RapidFuzz score {best_score:.1f} is below threshold {SCORE_THRESHOLD}, using OpenAI assistance...")
    
    # Process with GPT-3.5
    gpt35_result = assistant.process_with_gpt35(search_string, rapidfuzz_results)
    
    # Process with GPT-4
    gpt4_result = assistant.process_with_gpt4(search_string, rapidfuzz_results, gpt35_result)
    
    return gpt35_result, gpt4_result