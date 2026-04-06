"""LLM client wrapper using LangChain ChatOpenAI."""
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from app.config import config


class LLMClient:
    """Wrapper for LangChain ChatOpenAI client."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the LLM client."""
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables or .env file")
        
        self.model = model or config.OPENAI_MODEL
        
        # Initialize LangChain ChatOpenAI client
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            max_tokens=1000  # Allow longer responses
        )
    
    def chat_completion(self, messages: list[dict]) -> str:
        """Get chat completion from OpenAI using LangChain.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
        
        Returns:
            String content of the response
        """
        # Convert dict messages to LangChain message objects
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            else:  # user or assistant
                langchain_messages.append(HumanMessage(content=content))
        

        response = self.llm.invoke(langchain_messages)
        return response.content
    
    def get_llm(self) -> ChatOpenAI:
        """Get the underlying LangChain ChatOpenAI instance for advanced usage."""
        return self.llm

