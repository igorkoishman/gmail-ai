#!/usr/bin/env python3
import json
import re
import time
import ssl
from typing import Any, List, Dict
from google import genai
from config import Config

# SSL Patching for Gemini
ssl._create_default_https_context = ssl._create_unverified_context

def extract_json(text: str) -> Any:
    if not text: return None
    
    # 1. Try to find JSON within a markdown block (```json ... ```)
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text, re.IGNORECASE)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If markdown block content is still malformed, try further cleaning
            pass

    # 2. If no markdown block, or if it failed, try to find a standalone JSON object/array
    # This regex is more permissive and tries to find the first '{...}' or '[...]' block
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        json_str = match.group(0) # Use group(0) for the entire match
        
        # Clean up common LLM artifacts that might still be present
        json_str = json_str.replace('json', '').strip()
        json_str = json_str.replace('`', '')
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass # Fall through to return None
            
    return None

def gemini_classify(payload: List[Dict], api_key: str, model_name: str, categories: List[str]) -> List[Dict]:
    client = genai.Client(api_key=api_key)
    prompt = f"""
Classify each email into ONE category from this list:
{categories}

Return ONLY valid JSON:
{{
  "results": [
    {{"threadId":"string", "category":"string", "confidence":0.0, "reason":"max 12 words"}}
  ]
}}

Emails:
{json.dumps(payload, ensure_ascii=False)}
""".strip()

    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            resp = client.models.generate_content(model=model_name, contents=prompt)
            data = extract_json(resp.text)
            if data and "results" in data:
                return data["results"]
        except Exception as e:
            if "503" in str(e) and attempt < max_retries:
                time.sleep((attempt + 1) * 5)
                continue
            raise e
    return []
