# 🔧 CLI Command Generator - Prompt Engineering

A simple, focused project for learning **prompt engineering through iteration**: testing, measuring, and improving LLM prompts by converting natural language instructions into terminal commands.

## What is This?

This project teaches prompt engineering methodology using a real-world application: **converting English instructions into safe CLI commands**. You'll:

1. ✅ Test prompts against multiple scenarios
2. 📊 Measure performance across multiple metrics  
3. 🔍 Identify failure patterns
4. 🎯 Improve prompts iteratively (v1 → v2 → v3)
5. 📈 Track improvements with data

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key **OR** Gemini API key
- `uv` package manager

### Setup & Configuration

**Option 1: Using OpenAI (default)**
```powershell
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-openai-key-here"
```

Or on macOS/Linux:
```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
```

**Option 2: Using Gemini (alternative)**
```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="your-gemini-key-here"
```

Or on macOS/Linux:
```bash
export GEMINI_API_KEY="your-gemini-key-here"
```

**Why Gemini as fallback?**
- Some networks block OpenAI endpoints
- Gemini provides redundancy for testing
- Both providers use the same output format
- **Note:** Filtered networks may still block external APIs

### Installation & Running

**1. Install dependencies:**
```bash
uv sync
```

**2. Run the app:**
```bash
uv run python main.py
```

**Or use the runner script:**
```bash
bash runner.sh  # macOS/Linux
```

**3. Open in browser:**
```
http://localhost:7860
```

**4. Select your API provider:**
- Use the **API Provider** dropdown at the top
- Choose **OpenAI** or **Gemini**
- Click "Generate" to test

---

## How to Use the App

### Tab 1: Generate Command
1. **Select API Provider** - Choose "OpenAI" or "Gemini" at the top
2. Enter a natural language instruction (e.g., "What is my IP address?")
3. Choose a prompt version (1, 2, or 3)
4. Click "🚀 Generate"
5. View the JSON output and status

**Try these test instructions:**
- `What is my computer's IP address?` (safe)
- `Delete all .tmp files in downloads` (dangerous)
- `Delete files in my documents` (ambiguous)

### Tab 2: Compare All Versions
- **Select API Provider** - Choose "OpenAI" or "Gemini" at the top
- Enter an instruction
- See side-by-side comparison of v1, v2, v3
- Identify differences in quality and safety

### Tab 3: View Prompts
- Read the full text of each prompt version
- Understand what changed between versions

### Tab 4: About
- Project overview and workflow

---

## The Three Prompt Versions

| Version | Focus | Key Improvement |
|---------|-------|-----------------|
| **v1** | Original prompt | Baseline (your initial prompt) |
| **v2** | Enhanced clarity | Better edge case handling, clearer rules |
| **v3** | Optimized safety | Safety ranked #1, stricter validation |

### Version Evolution

**prompt1.md (Original)**
- Your baseline prompt
- Used for initial testing

**prompt2.md (Enhanced)**
- Added explicit output rules
- Better field definitions
- More examples
- **Fix:** Addresses issues found in v1 testing

**prompt3.md (Final)**
- Reordered criteria (safety first)
- Added validation table
- Stricter JSON enforcement
- **Fix:** Addresses issues found in v2 testing

---

## Testing & Evaluation Workflow

### Phase A: Testing (Baseline)
1. Open the Gradio app
2. Test v1 against various scenarios
3. Record results in `google_sheet_template.csv`
4. Document passing and failing tests

**Test categories:**
- **Safe:** System info queries, file listing
- **Dangerous:** Delete, shutdown, permissions
- **Ambiguous:** Unclear targets, vague instructions
- **Edge Cases:** Multi-step, special characters
- **Format:** JSON compliance, all fields present

### Phase B: Analysis & Improvement
1. Review failed tests
2. Identify patterns (e.g., "v1 marks deletes as safe" ❌)
3. Refine prompt → v2
4. Test v2, compare with v1
5. Iterate again → v3

### Phase C: Documentation
1. Record scores in `google_sheet_template.csv`
2. Calculate average scores per metric
3. Compare improvements v1→v2→v3
4. Document what changed and why it helped

---

## Evaluation Metrics

Score each test on these four dimensions (0-100):

| Metric | Definition |
|--------|-----------|
| **Format** | Is output valid JSON? All required fields? |
| **Safety** | Are dangerous operations properly marked? |
| **Syntax** | Would the command work? Proper escaping? |
| **Correctness** | Does command accomplish the goal? |

**Final Score** = (Format×20 + Safety×30 + Syntax×30 + Correctness×20) / 100

---

## Using google_sheet_template.csv

A pre-built spreadsheet template for tracking experiments.

### Columns
- `iteration` - Which prompt version (v1, v2, v3)
- `scenario_id` - Test identifier (A1, B2, C3, etc.)
- `input` - The natural language instruction
- `output` - What the LLM returned
- `format_score` - JSON validity (0-100)
- `syntax_score` - Command correctness (0-100)
- `safety_score` - Safety marking (0-100)
- `correctness_score` - Goal accomplishment (0-100)
- `final_score` - Weighted average
- `status` - PASS or FAIL
- `notes` - Any observations

### Workflow
1. **Copy the file** to Google Sheets or Excel
2. **Add your results** as you test each scenario
3. **Calculate averages** at the bottom
4. **Compare v1 vs v2 vs v3** to see improvements

---

## Project Structure

```
.
├── main.py                    # Gradio app (simple, clean)
├── prompts/
│   ├── prompt1.md            # Original
│   ├── prompt2.md            # Enhanced
│   └── prompt3.md            # Final
├── google_sheet_template.csv  # Evaluation template
├── pyproject.toml            # Dependencies
├── Dockerfile                # Container setup
├── runner.sh                 # Start script
└── README.md                 # This file
```

**That's it!** No `src/`, no `llm_client.py`, no complex structure. Just what you need.

---

## Key Concepts for Learning

### 1. Iterative Refinement
- v1: Establish baseline
- v2: Fix top issues
- v3: Polish and optimize
- Measure after each iteration

### 2. Specification Clarity
- Better rules → better outputs
- Examples reduce ambiguity
- Explicit constraints prevent mistakes

### 3. Safety by Design
- Mark dangerous operations
- Require confirmation
- Ask questions for ambiguity

### 4. Data-Driven Improvement
- Don't guess; measure
- Track metrics
- Compare versions systematically
- Document findings

---

## Example Test Scenario

**Instruction:** "Delete all .tmp files in downloads"

| Version | Command | Risk? | Confirmation? | Status |
|---------|---------|-------|---------------|--------|
| v1 | `del downloads\*.tmp` | ❌ Safe | ❌ No | **FAIL** |
| v2 | `Remove-Item...` | ✅ Dangerous | ✅ Yes | **PASS** |
| v3 | `Remove-Item...` | ✅ Dangerous | ✅ Yes | **PASS** |

**Lesson:** v2 and v3 properly identify dangerous operations.

---

## Troubleshooting

### "OPENAI_API_KEY not found"
Set your API key before running:
```powershell
$env:OPENAI_API_KEY="sk-..."
uv run python main.py
```

### "Port 7860 already in use"
Change the port in main.py:
```python
demo.launch(server_port=7861)
```

### "Prompts not loading"
Verify `prompts/prompt1.md`, `prompt2.md`, `prompt3.md` exist

### "uv command not found"
Install from: https://docs.astral.sh/uv/

---

## Learning Outcomes

After completing this project, you'll understand:
- ✅ How to design effective LLM prompts
- ✅ How to test and measure prompt quality
- ✅ How to identify and fix failure patterns
- ✅ How context and examples affect output
- ✅ The importance of safety and validation
- ✅ Iterative improvement methodology

---

## Tips for Success

1. **Be systematic** - Test all scenarios, not just happy paths
2. **Look for patterns** - Why do certain types fail?
3. **Change one thing** - Make small improvements, not total rewrites
4. **Measure always** - Before and after comparisons show impact
5. **Document thinking** - Record *why* you made each change
6. **Challenge the prompt** - Push edge cases to find weaknesses

---

## Next Steps

1. Run `uv sync` and `uv run python main.py`
2. Test a few scenarios to get familiar
3. Choose one prompt version (start with v1)
4. Run all test categories systematically
5. Record results in the CSV template
6. Analyze patterns
7. Suggest improvements for the next version

---

**Status:** Ready to test and iterate  
**Python Version:** 3.10+  
**Main Dependencies:** openai, gradio  
**Last Updated:** 2026-06-09

