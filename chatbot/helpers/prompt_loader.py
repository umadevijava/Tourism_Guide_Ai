"""
Prompt loader utility for managing system prompts and templates.
"""

from pathlib import Path
from typing import Optional


class PromptLoader:
    """Load and manage prompts from files."""
    
    _prompts_cache: dict[str, str] = {}
    
    @classmethod
    def get_prompts_dir(cls) -> Path:
        """Get the prompts directory path."""
        current_dir = Path(__file__).parent.parent.parent
        return current_dir / "prompts"
    
    @classmethod
    def load_prompt(cls, prompt_name: str) -> Optional[str]:
        """
        Load a prompt from file.
        
        Args:
            prompt_name: Name of the prompt file (without extension)
        
        Returns:
            The prompt content or None if not found
        """
        # Check cache first
        if prompt_name in cls._prompts_cache:
            return cls._prompts_cache[prompt_name]
        
        prompts_dir = cls.get_prompts_dir()
        
        # Try .txt first, then .md
        for ext in [".txt", ".md"]:
            prompt_file = prompts_dir / f"{prompt_name}{ext}"
            if prompt_file.exists():
                try:
                    content = prompt_file.read_text(encoding="utf-8")
                    cls._prompts_cache[prompt_name] = content
                    return content
                except Exception as e:
                    print(f"Error loading prompt {prompt_name}: {e}")
                    return None
        
        return None
    
    @classmethod
    def load_tourism_guide(cls) -> Optional[str]:
        """Load the tourism guide prompt."""
        return cls.load_prompt("tourism_guide")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the prompts cache."""
        cls._prompts_cache.clear()
