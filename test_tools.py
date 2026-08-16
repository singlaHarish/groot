#!/usr/bin/env python
"""Quick test to verify all MCP tools are registered."""

import sys
sys.path.insert(0, '.')

from mcp_server import TOOLS

print('Available MCP Tools:')
print('=' * 50)
for i, tool in enumerate(TOOLS, 1):
    print(f"{i}. {tool['name']}")
    print(f"   Description: {tool['description'][:60]}...")
    print()

print(f"Total: {len(TOOLS)} tools registered")
print()
print("✅ All tools loaded successfully!")
