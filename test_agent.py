"""Minimal test to verify the agent builds and runs."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print(f"Python: {sys.version}")
print(f"API Key set: {'Yes' if os.getenv('GOOGLE_API_KEY') else 'No'}")
print()

# Step 1: Check imports
print("[1] Checking imports...")
try:
    import langgraph
    print(f"    langgraph: {langgraph.__version__}")
except Exception as e:
    print(f"    ERROR: {e}")

try:
    import langchain_google_genai
    print(f"    langchain_google_genai: {langchain_google_genai.__version__}")
except Exception as e:
    print(f"    ERROR: {e}")

try:
    from langgraph.prebuilt import create_react_agent
    print(f"    create_react_agent: OK")
    # Check what params it accepts
    import inspect
    sig = inspect.signature(create_react_agent)
    print(f"    Params: {list(sig.parameters.keys())}")
except Exception as e:
    print(f"    ERROR: {e}")

# Step 2: Build agent
print()
print("[2] Building agent...")
try:
    from agent.graph import build_agent
    agent = build_agent()
    print(f"    Agent built OK: {type(agent)}")
except Exception as e:
    print(f"    ERROR building agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Quick invoke
print()
print("[3] Testing agent invoke (short prompt)...")
try:
    from langchain_core.messages import HumanMessage
    result = agent.invoke(
        {"messages": [HumanMessage(content="Say hello in one sentence.")]},
        {"configurable": {"thread_id": "test-123"}},
    )
    msgs = result.get("messages", [])
    print(f"    Got {len(msgs)} messages")
    for i, m in enumerate(msgs):
        mtype = getattr(m, "type", "?")
        content = getattr(m, "content", "")
        if isinstance(content, str):
            preview = content[:150]
        elif isinstance(content, list):
            preview = str(content)[:150]
        else:
            preview = str(content)[:150]
        print(f"    [{i}] type={mtype} content={preview}")
    print()
    print("SUCCESS!")
except Exception as e:
    print(f"    ERROR invoking agent: {e}")
    import traceback
    traceback.print_exc()
