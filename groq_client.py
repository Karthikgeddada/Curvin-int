# DEPRECATED: This file has been renamed to openrouter_client.py
# All imports should use: from openrouter_client import MultiKeyOpenRouterClient
import warnings
warnings.warn(
    "groq_client is deprecated. Use openrouter_client instead.",
    DeprecationWarning,
    stacklevel=2
)
from openrouter_client import MultiKeyOpenRouterClient  # noqa: F401, E402
