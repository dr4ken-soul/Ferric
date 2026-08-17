"""Provider adapters for Ferric's shared event schema."""

from ferric.adapters.anthropic import normalise_anthropic
from ferric.adapters.mcp import normalise_mcp
from ferric.adapters.openai import normalise_openai

__all__ = ["normalise_anthropic", "normalise_mcp", "normalise_openai"]
