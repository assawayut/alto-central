"""Anthropic client wrapper for AI-powered analytics.

This module provides a singleton Anthropic client with tool calling support
for generating charts from natural language prompts.
"""

import logging
from typing import Any, Dict, List, Optional

import anthropic

from app.config.settings import settings

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Wrapper for Anthropic Claude API with tool calling support."""

    # Default model for analytics - Haiku is faster and cheaper
    DEFAULT_MODEL = "claude-3-haiku-20240307"

    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None
        self._async_client: Optional[anthropic.AsyncAnthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        """Get or create synchronous Anthropic client."""
        if self._client is None:
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("Initialized Anthropic client")
        return self._client

    @property
    def async_client(self) -> anthropic.AsyncAnthropic:
        """Get or create async Anthropic client."""
        if self._async_client is None:
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._async_client = anthropic.AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )
            logger.info("Initialized async Anthropic client")
        return self._async_client

    @property
    def is_configured(self) -> bool:
        """Check if Anthropic API key is configured."""
        is_conf = bool(settings.ANTHROPIC_API_KEY)
        if not is_conf:
            logger.warning("[LLM] ANTHROPIC_API_KEY is not configured!")
        return is_conf

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> anthropic.types.Message:
        """Send a chat message with optional tools.

        Args:
            messages: List of message dicts with role and content
            system: System prompt
            tools: List of tool definitions
            model: Model to use (defaults to claude-sonnet-4)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 for deterministic)

        Returns:
            Anthropic Message response
        """
        kwargs: Dict[str, Any] = {
            "model": model or self.DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system

        if tools:
            kwargs["tools"] = tools

        response = await self.async_client.messages.create(**kwargs)
        return response

    async def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: List[Dict[str, Any]],
        tool_executor: callable,
        max_iterations: int = 10,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a multi-turn conversation with tool execution.

        This handles the tool calling loop:
        1. Send message to Claude
        2. If Claude wants to use tools, execute them
        3. Send tool results back to Claude
        4. Repeat until Claude returns text or max iterations

        Args:
            messages: Initial messages
            system: System prompt
            tools: Tool definitions
            tool_executor: Async function(tool_name, tool_input) -> result
            max_iterations: Maximum tool calling iterations
            model: Model to use

        Returns:
            Dict with final_message, tool_calls, and all_messages
        """
        logger.info(f"[LLM] chat_with_tools called")
        logger.info(f"[LLM] Model: {model or self.DEFAULT_MODEL}")
        logger.info(f"[LLM] Tools count: {len(tools)}")
        logger.info(f"[LLM] Max iterations: {max_iterations}")

        current_messages = list(messages)
        tool_calls = []
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"[LLM] Iteration {iteration}/{max_iterations}")

            response = await self.chat(
                messages=current_messages,
                system=system,
                tools=tools,
                model=model,
            )

            logger.info(f"[LLM] Response stop_reason: {response.stop_reason}")
            logger.info(f"[LLM] Response content blocks: {len(response.content)}")

            # Check if response has tool use
            tool_use_blocks = [
                block for block in response.content if block.type == "tool_use"
            ]

            logger.info(f"[LLM] Tool use blocks: {len(tool_use_blocks)}")

            if not tool_use_blocks:
                # No more tool calls, extract final text
                text_blocks = [
                    block.text for block in response.content if block.type == "text"
                ]
                final_message = "\n".join(text_blocks) if text_blocks else ""

                return {
                    "final_message": final_message,
                    "tool_calls": tool_calls,
                    "all_messages": current_messages,
                    "stop_reason": response.stop_reason,
                }

            # Process tool calls
            assistant_content = []
            tool_results = []

            for tool_block in response.content:
                if tool_block.type == "text":
                    assistant_content.append(
                        {"type": "text", "text": tool_block.text}
                    )
                elif tool_block.type == "tool_use":
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": tool_block.id,
                            "name": tool_block.name,
                            "input": tool_block.input,
                        }
                    )

                    # Execute tool
                    try:
                        result = await tool_executor(
                            tool_block.name, tool_block.input
                        )
                        tool_calls.append(
                            {
                                "tool": tool_block.name,
                                "input": tool_block.input,
                                "result": result,
                                "success": True,
                            }
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_block.id,
                                "content": str(result),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Tool execution failed: {tool_block.name}: {e}")
                        tool_calls.append(
                            {
                                "tool": tool_block.name,
                                "input": tool_block.input,
                                "error": str(e),
                                "success": False,
                            }
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_block.id,
                                "content": f"Error: {e}",
                                "is_error": True,
                            }
                        )

            # Add assistant message and tool results
            current_messages.append({"role": "assistant", "content": assistant_content})
            current_messages.append({"role": "user", "content": tool_results})

        # Max iterations reached
        logger.warning(f"Max iterations ({max_iterations}) reached in tool loop")
        return {
            "final_message": "Maximum iterations reached",
            "tool_calls": tool_calls,
            "all_messages": current_messages,
            "stop_reason": "max_iterations",
        }


# Global singleton
_client: Optional[AnthropicClient] = None


def get_anthropic_client() -> AnthropicClient:
    """Get the global Anthropic client instance."""
    global _client
    if _client is None:
        _client = AnthropicClient()
    return _client
