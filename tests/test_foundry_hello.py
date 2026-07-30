#!/usr/bin/env python3
"""
Week 1 milestone: "Hello Model" test for Microsoft Foundry Local.

Confirms the Foundry Local runtime is installed and can run a local LLM
completely offline. Talks to the OpenAI-compatible endpoint that the
Foundry Local service exposes, using the first loaded model.

Prereqs (one-time):
    foundry server start
    foundry model load phi-4-mini
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from dotenv import load_dotenv
from openai import OpenAI

from rag_pipeline import FoundryError, discover_foundry_endpoint, resolve_model_id

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

print("\n" + "=" * 60)
print("  FOUNDRY LOCAL - HELLO MODEL TEST")
print("=" * 60 + "\n")

try:
    base = discover_foundry_endpoint()
except FoundryError as error:
    print(error)
    sys.exit(1)
print(f"1. Foundry endpoint: {base}")

client = OpenAI(base_url=base, api_key="not-needed", timeout=600)

# Match LLM_MODEL against the reported ids — the list includes models that are
# downloaded but NOT loaded, so picking the first one hits "is not loaded".
try:
    model_id = resolve_model_id([m.id for m in client.models.list().data],
                                os.getenv("LLM_MODEL"))
except FoundryError as error:
    print(error)
    sys.exit(1)
print(f"   Model id        : {model_id}")

print("\n2. Sending prompt: 'Say hello in one short sentence.'")
print("   (first call may be slow while the GPU engine warms up...)")
resp = client.chat.completions.create(
    model=model_id,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
    max_tokens=64,
)

answer = (resp.choices[0].message.content or "").strip()
print("\n" + "-" * 60)
print("Model says:", answer)
print("-" * 60)

if not answer:
    print("\n[!] Empty response - model loaded but returned no text.")
    sys.exit(1)

print("\n" + "=" * 60)
print("  HELLO MODEL TEST PASSED - Foundry Local works offline!")
print("=" * 60 + "\n")
