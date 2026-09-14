#!/usr/bin/env python
"""Test compute_response_quality function."""

import sys
sys.path.insert(0, '.')

from utils import compute_response_quality

# Test with two similar responses
full_resp = """Vanguard's four principles for investing success are:

1. Goals - Create clear, appropriate investment goals for your situation
2. Balance - Keep a balanced and diversified mix of investments across asset classes
3. Cost - Minimize fees and investment costs to improve net returns
4. Discipline - Maintain perspective and long-term discipline, avoiding emotional decisions

These principles help investors focus on controllable factors rather than reacting to market noise."""

opt_resp = """Vanguard recommends four key principles:

1. Goals - Define your investment objectives clearly
2. Balance - Diversify across stocks, bonds, and cash
3. Cost - Reduce investment fees and expenses
4. Discipline - Stay focused on long-term strategy

Focus on what you can control instead of market headlines."""

print("Testing compute_response_quality()...")
print("=" * 60)
print()

quality = compute_response_quality(full_resp, opt_resp)

print(f"Quality Metrics:")
print(f"  F1 Score: {quality['f1']:.1%}")
print(f"  Precision: {quality['precision']:.1%}")
print(f"  Recall: {quality['recall']:.1%}")
print(f"  Label: {quality['quality_label']}")
print(f"  Description: {quality['description']}")
print()

if quality['f1'] >= 0.5:
    print("✅ Quality computation working! Responses are semantically similar.")
else:
    print("⚠️ Quality computation working, but responses show low similarity.")
