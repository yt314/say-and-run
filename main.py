"""
CLI Command Generator - Prompt Engineering Project
Simple Gradio interface for testing prompt iterations with OpenAI or Gemini.
"""

import html
import json
import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

try:
    from google import genai
except ImportError:
    genai = None


# Load environment variables from .env file
load_dotenv()

# Model constants
MODEL_NAME_OPENAI = "gpt-4o-mini"
MODEL_NAME_GEMINI = "gemini-2.5-flash-lite"

# Prompt versions directory
PROMPTS_DIR = Path(__file__).parent / "prompts"

# API keys
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Clients
openai_client = None
gemini_client = None

if openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        print("✓ OpenAI client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize OpenAI client: {type(e).__name__}")
else:
    print("⚠ OPENAI_API_KEY not found in environment")

if gemini_api_key:
    if genai is None:
        print("✗ google-genai package is not installed. Run: uv sync")
    else:
        try:
            gemini_client = genai.Client(api_key=gemini_api_key)
            print("✓ Gemini client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Gemini client: {type(e).__name__}")
else:
    print("⚠ GEMINI_API_KEY not found in environment")


def load_prompt(version: str) -> str:
    """Load prompt from file."""
    prompt_file = PROMPTS_DIR / f"prompt{version}.md"
    if not prompt_file.exists():
        return f"Error: {prompt_file} not found"
    return prompt_file.read_text(encoding="utf-8")


def clean_model_output(output: str) -> str:
    """Remove Markdown fences and keep the JSON object returned by the model."""
    if not output:
        return ""

    text = output.strip()

    # Gemini sometimes wraps JSON with Markdown fences: ```json ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # If extra text exists, keep only the JSON object.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1].strip()

    return text


def extract_command(output: str) -> str:
    """Extract only the CLI command from the model JSON output."""
    cleaned = clean_model_output(output)
    try:
        data = json.loads(cleaned)
        return str(data.get("command", "")).strip()
    except Exception:
        return ""


def validate_output(output: str) -> str:
    """Validate the JSON response structure expected by the assignment."""
    cleaned = clean_model_output(output)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return "⚠️ Not valid JSON"

    required = {
        "command",
        "shell",
        "os",
        "explanation",
        "risk_level",
        "needs_confirmation",
        "assumptions",
    }

    if not required.issubset(data.keys()):
        missing = required - set(data.keys())
        return f"⚠️ Missing fields: {', '.join(sorted(missing))}"

    if data.get("risk_level") not in {"safe", "medium", "dangerous"}:
        return "⚠️ Invalid risk_level"

    return "✅ Valid"


def call_openai(system_prompt: str, instruction: str) -> str:
    """Call OpenAI using the current Python SDK."""
    if openai_client is None:
        return "❌ Missing OPENAI_API_KEY. Set it before generating commands."

    response = openai_client.chat.completions.create(
        model=MODEL_NAME_OPENAI,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
        ],
        temperature=0.3,
        max_tokens=500,
    )

    return response.choices[0].message.content.strip()


def call_gemini(system_prompt: str, instruction: str) -> str:
    """Call Gemini using the official Google GenAI SDK."""
    if genai is None:
        return "❌ google-genai is not installed. Run: uv sync"

    if gemini_client is None:
        return "❌ Missing GEMINI_API_KEY. Set it before generating commands."

    full_prompt = f"""
{system_prompt}

User instruction:
{instruction}

Return raw JSON only.
Do not wrap the JSON in Markdown.
Do not use ```json.
Do not use code fences.
The response must start with {{ and end with }}.
""".strip()

    response = gemini_client.models.generate_content(
        model=MODEL_NAME_GEMINI,
        contents=full_prompt,
    )

    return (response.text or "").strip()


def generate_command(instruction: str, prompt_version: str, provider: str) -> tuple:
    """Generate CLI command using the selected prompt version and provider."""
    if not instruction.strip():
        return "", "", "❌ Please enter an instruction"

    system_prompt = load_prompt(prompt_version)
    print(f"\n🔄 Generating command for: {instruction[:60]}...")
    print(f"📝 Prompt version: {prompt_version}")
    print(f"🤖 Provider: {provider}")

    try:
        if provider == "OpenAI":
            print(f"🤖 Calling OpenAI API (model={MODEL_NAME_OPENAI})")
            output = call_openai(system_prompt, instruction)
            if output.startswith("❌"):
                return "", output, output

        elif provider == "Gemini":
            print(f"🤖 Calling Gemini API (model={MODEL_NAME_GEMINI})")
            output = call_gemini(system_prompt, instruction)
            if output.startswith("❌"):
                return "", output, output

        else:
            return "", "", "❌ Unknown provider selected"

        cleaned_output = clean_model_output(output)
        command = extract_command(cleaned_output)
        status = validate_output(cleaned_output)
        print(f"✓ Response received ({len(output)} chars)")
        print(f"Status: {status}")
        return command, cleaned_output, status

    except AuthenticationError as e:
        print(f"✗ OpenAI authentication error: {str(e)[:150]}")
        return "", "", "❌ Invalid or expired OPENAI_API_KEY"

    except APIConnectionError as e:
        print(f"✗ OpenAI connection error: {str(e)[:150]}")
        return "", "", "❌ OpenAI connection/certificate problem. Check network filtering, proxy, firewall, or SSL inspection."

    except RateLimitError:
        return "", "", "❌ OpenAI rate limit exceeded"

    except APIError as e:
        print(f"✗ OpenAI API error: {str(e)[:150]}")
        return "", "", "❌ OpenAI API error"

    except Exception as e:
        provider_name = "Gemini" if provider == "Gemini" else "API"
        print(f"✗ {provider_name} error: {type(e).__name__}")
        print(f"   Details: {str(e)[:200]}")
        return "", "", f"❌ {provider_name} connection/API problem: {type(e).__name__}"


def compare_versions(instruction: str, provider: str) -> str:
    """Compare all three prompt versions with the selected provider."""
    if not instruction.strip():
        return "<p style='color: red;'>Enter an instruction to compare.</p>"

    print(f"\n📊 Comparing all versions with {provider}: {instruction[:60]}...")

    html_output = """
    <table style="width:100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr style="background: #f0f0f0;">
        <th style="border: 1px solid #ddd; padding: 8px;">Prompt 1</th>
        <th style="border: 1px solid #ddd; padding: 8px;">Prompt 2</th>
        <th style="border: 1px solid #ddd; padding: 8px;">Prompt 3</th>
      </tr>
      <tr style="vertical-align: top;">
    """

    for version in ["1", "2", "3"]:
        command, raw_output, status = generate_command(instruction, version, provider)
        safe_command = html.escape(command or "N/A")
        safe_status = html.escape(status)
        safe_output = html.escape(raw_output[:500] if raw_output else "")

        html_output += f"""
        <td style="border: 1px solid #ddd; padding: 10px;">
          <b>Command:</b><br>
          <code>{safe_command}</code><br><br>
          <b>Status:</b> {safe_status}<br><br>
          <details>
            <summary>Raw output</summary>
            <pre style="white-space: pre-wrap;">{safe_output}</pre>
          </details>
        </td>
        """

    html_output += "</tr></table>"
    return html_output


def show_prompt(version: str) -> str:
    """Display prompt documentation."""
    return load_prompt(version)


def startup_summary() -> None:
    """Print a safe startup summary without exposing API keys."""
    print("\n" + "=" * 60)
    print("CLI Command Generator - Startup Check")
    print("=" * 60)
    print(f"OpenAI key found: {bool(openai_api_key)}")
    print(f"OpenAI client initialized: {openai_client is not None}")
    print(f"Gemini key found: {bool(gemini_api_key)}")
    print(f"Gemini SDK installed: {genai is not None}")
    print(f"Gemini client initialized: {gemini_client is not None}")
    print(f"OpenAI model: {MODEL_NAME_OPENAI}")
    print(f"Gemini model: {MODEL_NAME_GEMINI}")

custom_css = """
#command-output textarea {
    font-size: 28px !important;
    font-weight: 700 !important;
    font-family: Consolas, 'Courier New', monospace !important;
    color: #111827 !important;
    background: #f8fafc !important;
    border: 2px solid #ff6b35 !important;
    border-radius: 10px !important;
    padding: 18px !important;
    text-align: center !important;
}

#command-output label {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #ff6b35 !important;
}

#footer {
    margin: 36px auto 12px auto;
    padding: 14px 22px;
    width: fit-content;
    max-width: 95%;
    text-align: center;
    background: #ffffff;
    border: 1px solid #fed7aa;
    border-radius: 999px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
    color: #1f2937;
    font-size: 16px;
    font-weight: 500;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

#footer strong {
    font-weight: 900;
    color: #111827;
}

#footer a {
    color: #ea580c !important;
    font-weight: 900;
    text-decoration: none !important;
}

#footer a:hover {
    color: #c2410c !important;
    text-decoration: underline !important;
}

.footer-separator {
    color: #fb923c;
    font-weight: 900;
}
"""

# Create Gradio interface
with gr.Blocks(title="CLI Command Generator", css=custom_css) as demo:
    gr.Markdown("# 🔧 CLI Command Generator - Prompt Engineering")
    gr.Markdown("Test and compare three prompt iterations for converting natural language to terminal commands.")

    with gr.Tab("Generate Command"):
        with gr.Row():
            instruction = gr.Textbox(
                label="Natural Language Instruction",
                placeholder="e.g., 'What is my IP address?'",
                lines=3,
            )
            provider = gr.Dropdown(
                choices=["OpenAI", "Gemini"],
                value="Gemini",
                label="API Provider",
            )
            version = gr.Radio(
                choices=["1", "2", "3"],
                value="3",
                label="Prompt Version",
            )

        generate_btn = gr.Button("🚀 Generate", size="lg")

        command_output = gr.Textbox(
            label="💻 Generated CLI Command",
            lines=2,
            interactive=False,
            elem_id="command-output",
        )

        with gr.Row():
            raw_output = gr.Textbox(
                label="Full Model Output",
                lines=12,
                interactive=False,
            )
            status = gr.Textbox(label="Status", interactive=False)

        generate_btn.click(
            fn=generate_command,
            inputs=[instruction, version, provider],
            outputs=[command_output, raw_output, status],
        )

    with gr.Tab("Compare All Versions"):
        with gr.Row():
            comp_instruction = gr.Textbox(
                label="Test Instruction",
                placeholder="Enter instruction to compare prompt1, prompt2, prompt3",
                lines=3,
            )
            comp_provider = gr.Dropdown(
                choices=["OpenAI", "Gemini"],
                value="Gemini",
                label="API Provider",
            )

        compare_btn = gr.Button("📊 Compare")
        comp_output = gr.HTML()

        compare_btn.click(
            fn=compare_versions,
            inputs=[comp_instruction, comp_provider],
            outputs=comp_output,
        )

    with gr.Tab("View Prompts"):
        prompt_version = gr.Radio(choices=["1", "2", "3"], value="1", label="Select Version")
        prompt_display = gr.Markdown(value=load_prompt("1"))

        prompt_version.change(
            fn=show_prompt,
            inputs=prompt_version,
            outputs=prompt_display,
        )

    with gr.Tab("About"):
        gr.Markdown(
            """
            ## Prompt Engineering Workflow

            **Phase A: Testing**
            - Generate commands with each prompt version.
            - Test safe, dangerous, ambiguous, and edge-case scenarios.
            - Record results in `google_sheet_template.csv`.

            **Phase B: Analysis & Improvement**
            - Analyze failure patterns.
            - Refine prompts based on findings.
            - Compare prompt1 → prompt2 → prompt3.

            **Providers**
            - OpenAI uses `OPENAI_API_KEY`.
            - Gemini uses `GEMINI_API_KEY`.
            - Gemini was added as a fallback for networks where OpenAI has certificate/filtering issues.
            """
        )

    gr.Markdown(
            """
            <div id="footer">
                <span>Created by <strong>Yehudit Pollock</strong></span>
                <span class="footer-separator">•</span>
                <a href="https://github.com/yt314" target="_blank">GitHub</a>
                <span class="footer-separator">•</span>
                <a href="mailto:y556780305@gmail.com">y556780305@gmail.com</a>
            </div>
            """
        )


if __name__ == "__main__":
    startup_summary()

    print("\n" + "=" * 60)
    print("Launching Gradio interface...")
    print("=" * 60 + "\n")

    try:
        demo.launch(server_name="0.0.0.0", server_port=7860)
    except OSError:
        print("⚠ Port 7860 in use, trying port 7861...")
        demo.launch(server_name="0.0.0.0", server_port=7861)
