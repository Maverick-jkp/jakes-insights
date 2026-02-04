"""
Prompt Templates for Content Generation

Provides type-specific prompts for Tutorial, Analysis, and News content.
"""

from .tutorial_prompt import get_tutorial_prompt
from .analysis_prompt import get_analysis_prompt
from .news_prompt import get_news_prompt

__all__ = [
    'get_tutorial_prompt',
    'get_analysis_prompt',
    'get_news_prompt'
]
