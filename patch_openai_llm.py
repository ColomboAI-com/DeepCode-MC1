"""
Patch for OpenAI LLM to handle missing usage field in ColomboAI API responses.

This patch monkey-patches the OpenAIAugmentedLLM.generate method to handle
cases where the API response doesn't include the usage field with token counts.
"""

import functools
from typing import Any


def patch_openai_llm():
    """Apply patch to handle missing usage field in API responses."""
    try:
        from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
        
        # Store original generate method
        original_generate = OpenAIAugmentedLLM.generate
        
        @functools.wraps(original_generate)
        async def patched_generate(self, message, request_params=None):
            """Patched generate method that handles missing usage field."""
            # Call original method but wrap the response handling
            import inspect
            
            # Get the original method's code
            original_method = original_generate.__get__(self, type(self))
            
            # We need to intercept at the response handling level
            # Store original executor.execute
            original_execute = self.executor.execute
            
            async def patched_execute(task, *args, **kwargs):
                """Patched execute that adds default usage if missing."""
                result = await original_execute(task, *args, **kwargs)
                
                # Check if this is a ChatCompletion response
                if hasattr(result, 'usage') and result.usage is None:
                    # Create a mock usage object with default values
                    from openai.types.completion_usage import CompletionUsage
                    result.usage = CompletionUsage(
                        prompt_tokens=0,
                        completion_tokens=0,
                        total_tokens=0
                    )
                
                return result
            
            # Temporarily replace executor.execute
            self.executor.execute = patched_execute
            
            try:
                # Call original generate
                return await original_method(message, request_params)
            finally:
                # Restore original executor.execute
                self.executor.execute = original_execute
        
        # Apply the patch
        OpenAIAugmentedLLM.generate = patched_generate
        
        print("✅ OpenAI LLM patch applied successfully")
        return True
        
    except Exception as e:
        print(f"⚠️ Failed to apply OpenAI LLM patch: {e}")
        return False


# Auto-apply patch on import
patch_openai_llm()
