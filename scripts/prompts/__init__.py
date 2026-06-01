"""
Prompt Templates for Content Generation

Provides type-specific prompts for Tutorial, Analysis, News, Comparison, and
Troubleshoot content.
"""

from .tutorial_prompt import get_tutorial_prompt
from .analysis_prompt import get_analysis_prompt
from .news_prompt import get_news_prompt
from .comparison_prompt import get_comparison_prompt
from .troubleshoot_prompt import get_troubleshoot_prompt

__all__ = [
    'get_tutorial_prompt',
    'get_analysis_prompt',
    'get_news_prompt',
    'get_comparison_prompt',
    'get_troubleshoot_prompt',
]
