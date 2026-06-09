"""
CLI Command Generator - Prompt Engineering Project
Simple, clean Gradio interface for testing prompt iterations.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
from openai import AuthenticationError, APIConnectionError, RateLimitError, APIError

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client - check for API key
api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    if len(api_key) < 20:
        print("✗ API key appears invalid: too short")
    elif not api_key.startswith("sk-"):
        print("✗ API key does not start with 'sk-'")
    else:
        try:
            client = OpenAI(api_key=api_key)
            print("✓ OpenAI client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize OpenAI client: {type(e).__name__}")
else:
    print("⚠ OPENAI_API_KEY not found in environment")

# Prompt versions directory
PROMPTS_DIR = Path(__file__).parent / "prompts"


def test_api_connectivity() -> dict:
    """Test API connectivity without exposing API key"""
    result = {
        "api_key_found": bool(api_key),
        "client_initialized": client is not None,
        "api_reachable": False,
        "error": None,
        "error_type": None
    }
    
    if not client:
        result["error"] = "No API key configured"
        return result
    
    try:
        print("\n🔍 Testing API connectivity...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=10,
            temperature=0
        )
        result["api_reachable"] = True
        print("✓ API connectivity test passed")
        return result
    
    except AuthenticationError as e:
        result["error_type"] = "AuthenticationError"
        result["error"] = "Invalid or expired API key"
        print("✗ Authentication failed: Invalid/expired API key")
        print(f"   Details: {str(e)[:120]}")
        return result
    
    except APIConnectionError as e:
        result["error_type"] = "APIConnectionError"
        error_details = str(e)
        result["error"] = f"Cannot reach OpenAI API"
        print(f"✗ Connection error: Cannot reach API")
        print(f"   Reason: {error_details[:120]}")
        print(f"   Check: Network connection, firewall, or API endpoint status")
        return result
    
    except RateLimitError as e:
        result["error_type"] = "RateLimitError"
        result["error"] = "API rate limit exceeded"
        print("✗ Rate limit exceeded")
        return result
    
    except APIError as e:
        result["error_type"] = "APIError"
        result["error"] = str(e)[:80]
        print(f"✗ API error: {str(e)[:120]}")
        return result
    
    except Exception as e:
        result["error_type"] = type(e).__name__
        result["error"] = str(e)[:80]
        print(f"✗ Unexpected error: {type(e).__name__}")
        print(f"   Details: {str(e)[:120]}")
        return result


def load_prompt(version: str) -> str:
    """Load prompt from file"""
    prompt_file = PROMPTS_DIR / f"prompt{version}.md"
    if not prompt_file.exists():
        return f"Error: {prompt_file} not found"
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()


def generate_command(instruction: str, prompt_version: str) -> tuple:
    """Generate CLI command using selected prompt version"""
    if not instruction.strip():
        return "", "❌ Please enter an instruction"
    
    if not client:
        return "", "❌ Missing OPENAI_API_KEY. Set it in .env file with: OPENAI_API_KEY=sk-..."
    
    try:
        print(f"\n🔄 Generating command for: {instruction[:50]}...")
        system_prompt = load_prompt(prompt_version)
        
        print(f"📝 Using prompt version: {prompt_version}")
        print(f"🤖 Calling OpenAI API (model=gpt-3.5-turbo)...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": instruction}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        output = response.choices[0].message.content.strip()
        print(f"✓ API response received: {len(output)} chars")
        
        # Try to parse JSON and validate
        try:
            obj = json.loads(output)
            required = {"command", "shell", "os", "explanation", "risk_level", "needs_confirmation", "assumptions"}
            if not required.issubset(obj.keys()):
                status = "⚠️ Missing fields"
            elif obj.get("risk_level") not in {"safe", "medium", "dangerous"}:
                status = "⚠️ Invalid risk_level"
            else:
                status = "✅ Valid"
            print(f"Status: {status}")
            return output, status
        except json.JSONDecodeError:
            print("⚠️ Response is not valid JSON")
            return output, "⚠️ Not valid JSON (clarification asked?)"
    
    except AuthenticationError as e:
        error_msg = f"❌ Invalid/Expired API Key"
        print(f"\n✗ {error_msg}")
        print(f"   Details: {str(e)[:150]}")
        return "", error_msg
    
    except APIConnectionError as e:
        error_msg = f"❌ Cannot Connect to OpenAI API"
        print(f"\n✗ {error_msg}")
        print(f"   Reason: {str(e)[:150]}")
        print(f"   Check: Network connection, firewall, or API endpoint status")
        return "", error_msg
    
    except RateLimitError as e:
        error_msg = f"❌ Rate Limit: Too many requests"
        print(f"\n✗ {error_msg}")
        return "", error_msg
    
    except APIError as e:
        error_msg = f"❌ OpenAI API Error"
        print(f"\n✗ {error_msg}")
        print(f"   Details: {str(e)[:150]}")
        return "", error_msg
    
    except Exception as e:
        error_msg = f"❌ Unexpected Error: {type(e).__name__}"
        print(f"\n✗ {error_msg}")
        print(f"   Details: {str(e)[:150]}")
        return "", error_msg


def compare_versions(instruction: str) -> str:
    """Compare all three prompt versions"""
    if not instruction.strip():
        return "<p style='color: red;'>Enter an instruction to compare</p>"
    
    if not client:
        return "<p style='color: red;'>❌ Missing OPENAI_API_KEY. Set it in .env file to use comparison.</p>"
    
    print(f"\n📊 Comparing all versions for: {instruction[:50]}...")
    
    html = "<table style='width:100%; border: 1px solid #ddd;'>"
    html += "<tr style='background: #f0f0f0;'><th>V1</th><th>V2</th><th>V3</th></tr><tr style='vertical-align:top;'>"
    
    for v in ["1", "2", "3"]:
        output, status = generate_command(instruction, v)
        try:
            obj = json.loads(output)
            cmd = obj.get("command", "N/A")
            risk = obj.get("risk_level", "N/A")
            html += f"<td style='border: 1px solid #ddd; padding: 10px;'><b>Cmd:</b> <code>{cmd[:50]}</code><br><b>Risk:</b> {risk}</td>"
        except:
            html += f"<td style='border: 1px solid #ddd; padding: 10px;'>Error - {status}</td>"
    
    html += "</tr></table>"
    return html


def show_prompt(version: str) -> str:
    """Display prompt documentation"""
    return load_prompt(version)


# Create Gradio interface
with gr.Blocks(title="CLI Command Generator") as demo:
    gr.Markdown("# 🔧 CLI Command Generator - Prompt Engineering")
    gr.Markdown("Test and compare three prompt iterations for converting natural language to terminal commands.")
    
    with gr.Tab("Generate Command"):
        with gr.Row():
            instruction = gr.Textbox(
                label="Natural Language Instruction",
                placeholder="e.g., 'What is my IP address?'",
                lines=3
            )
            version = gr.Radio(
                choices=["1", "2", "3"],
                value="3",
                label="Prompt Version"
            )
        
        generate_btn = gr.Button("🚀 Generate", size="lg")
        
        with gr.Row():
            command_output = gr.Textbox(
                label="Command Output (JSON)",
                lines=12,
                interactive=False
            )
            status = gr.Textbox(label="Status", interactive=False)
        
        def on_generate(inst, vers):
            output, stat = generate_command(inst, vers)
            return output, stat
        
        generate_btn.click(
            fn=on_generate,
            inputs=[instruction, version],
            outputs=[command_output, status]
        )
    
    with gr.Tab("Compare All Versions"):
        comp_instruction = gr.Textbox(
            label="Test Instruction",
            placeholder="Enter instruction to compare v1, v2, v3",
            lines=3
        )
        compare_btn = gr.Button("📊 Compare")
        comp_output = gr.HTML()
        
        compare_btn.click(
            fn=compare_versions,
            inputs=comp_instruction,
            outputs=comp_output
        )
    
    with gr.Tab("View Prompts"):
        prompt_version = gr.Radio(choices=["1", "2", "3"], value="1", label="Select Version")
        prompt_display = gr.Markdown()
        
        prompt_version.change(
            fn=show_prompt,
            inputs=prompt_version,
            outputs=prompt_display
        )
        # Initial load
        gr.Markdown(load_prompt("1"))
    
    with gr.Tab("About"):
        gr.Markdown("""
        ## Prompt Engineering Workflow
        
        **Phase A: Testing**
        - Generate commands with each prompt version
        - Test against various scenarios (safe, dangerous, ambiguous)
        - Record results in `google_sheet_template.csv`
        
        **Phase B: Analysis & Improvement**
        - Analyze failure patterns
        - Refine prompts based on findings
        - Iterate to create v2 and v3
        
        **Key Metrics:**
        - Format compliance (valid JSON?)
        - Safety (dangerous ops marked?)
        - Accuracy (command correct?)
        - Clarity (explanation good?)
        
        **Evaluation Scoring:**
        - Format: 20%
        - Safety: 30%
        - Syntax: 30%
        - Correctness: 20%
        """)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CLI Command Generator - Startup Check")
    print("="*60)
    
    # Test API connectivity
    connectivity = test_api_connectivity()
    print(f"\n📋 API Status Summary:")
    print(f"   API key found: {connectivity['api_key_found']}")
    print(f"   Client initialized: {connectivity['client_initialized']}")
    print(f"   API reachable: {connectivity['api_reachable']}")
    if connectivity['error']:
        print(f"   Error: {connectivity['error']}")
    
    print("\n" + "="*60)
    print("Launching Gradio interface...")
    print("="*60 + "\n")
    
    try:
        demo.launch(server_name="0.0.0.0", server_port=7860, theme="soft")
    except OSError:
        print("⚠ Port 7860 in use, trying port 7861...")
        demo.launch(server_name="0.0.0.0", server_port=7861, theme="soft")
