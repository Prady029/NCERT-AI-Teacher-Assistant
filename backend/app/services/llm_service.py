"""
LLM Service for NCERT AI Teacher Assistant.
Supports multiple LLM providers (Google Gemini, OpenAI, Anthropic).
"""

import asyncio
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import settings


class LLMProvider(str, Enum):
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate a structured response matching a JSON schema."""
        pass


class GoogleLLMClient(BaseLLMClient):
    """Google Gemini LLM client."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Google Generative AI client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                raise RuntimeError("google-generativeai package not installed. Run: pip install google-generativeai")
        return self._client
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response using Google Gemini."""
        client = self._get_client()
        
        generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
            "max_output_tokens": kwargs.get("max_tokens", 8192),
        }
        
        try:
            response = await asyncio.to_thread(
                client.generate_content,
                prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Google Gemini API error: {str(e)}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream a response using Google Gemini."""
        client = self._get_client()
        
        generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
            "max_output_tokens": kwargs.get("max_tokens", 8192),
        }
        
        try:
            response = await asyncio.to_thread(
                client.generate_content,
                prompt,
                generation_config=generation_config,
                stream=True
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise RuntimeError(f"Google Gemini streaming error: {str(e)}")
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate structured JSON response."""
        structured_prompt = f"""{prompt}

Please respond with a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no additional text."""
        
        response = await self.generate(structured_prompt, **kwargs)
        
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse structured response: {str(e)}")


class OpenAILLMClient(BaseLLMClient):
    """OpenAI LLM client."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        return self._client
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response using OpenAI."""
        client = self._get_client()
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 8192),
                top_p=kwargs.get("top_p", 0.95),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream a response using OpenAI."""
        client = self._get_client()
        
        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 8192),
                top_p=kwargs.get("top_p", 0.95),
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"OpenAI streaming error: {str(e)}")
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate structured JSON response using OpenAI function calling."""
        client = self._get_client()
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 8192),
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            raise RuntimeError(f"OpenAI structured generation error: {str(e)}")


class AnthropicLLMClient(BaseLLMClient):
    """Anthropic Claude LLM client."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        return self._client
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response using Anthropic Claude."""
        client = self._get_client()
        
        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 8192),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream a response using Anthropic Claude."""
        client = self._get_client()
        
        try:
            stream = await client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 8192),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text
        except Exception as e:
            raise RuntimeError(f"Anthropic streaming error: {str(e)}")
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate structured JSON response."""
        structured_prompt = f"""{prompt}

Please respond with a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no additional text."""
        
        response = await self.generate(structured_prompt, **kwargs)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse structured response: {str(e)}")


class LLMService:
    """Main LLM service managing multiple providers."""
    
    def __init__(self):
        self._clients: Dict[LLMProvider, BaseLLMClient] = {}
        self._default_provider = LLMProvider(settings.default_llm_provider)
    
    def _get_client(self, provider: Optional[LLMProvider] = None) -> BaseLLMClient:
        """Get or create LLM client for provider."""
        provider = provider or self._default_provider
        
        if provider not in self._clients:
            if provider == LLMProvider.GOOGLE:
                if not settings.google_api_key:
                    raise ValueError("Google API key not configured")
                self._clients[provider] = GoogleLLMClient(settings.google_api_key, settings.default_model)
            elif provider == LLMProvider.OPENAI:
                if not settings.openai_api_key:
                    raise ValueError("OpenAI API key not configured")
                self._clients[provider] = OpenAILLMClient(settings.openai_api_key)
            elif provider == LLMProvider.ANTHROPIC:
                if not settings.anthropic_api_key:
                    raise ValueError("Anthropic API key not configured")
                self._clients[provider] = AnthropicLLMClient(settings.anthropic_api_key)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        
        return self._clients[provider]
    
    async def generate(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """Generate a response using the specified or default provider."""
        client = self._get_client(provider)
        return await client.generate(prompt, **kwargs)
    
    async def generate_stream(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response using the specified or default provider."""
        client = self._get_client(provider)
        async for chunk in client.generate_stream(prompt, **kwargs):
            yield chunk
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a structured JSON response."""
        client = self._get_client(provider)
        return await client.generate_structured(prompt, schema, **kwargs)
    
    def list_available_providers(self) -> List[LLMProvider]:
        """List available LLM providers based on configured API keys."""
        providers = []
        if settings.google_api_key:
            providers.append(LLMProvider.GOOGLE)
        if settings.openai_api_key:
            providers.append(LLMProvider.OPENAI)
        if settings.anthropic_api_key:
            providers.append(LLMProvider.ANTHROPIC)
        return providers


# Global LLM service instance
llm_service = LLMService()