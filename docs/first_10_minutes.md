# First 10 Minutes with JARVIS — User Acceptance Walkthrough

Welcome to **JARVIS**! This guide allows you to test and verify JARVIS as your personal local computer agent in approximately 10 minutes.

---

## Prerequisites

- **OS**: Windows 10 or 11
- **Python**: 3.10+ installed
- **Hardware**: CPU-first (no dedicated GPU required, no external API keys, no Ollama)

---

## Step 1: Run Subsystem Diagnostics (Doctor)

Open PowerShell or Command Prompt in the repository folder and run:

```bash
python -m jarvis --doctor
```

**Expected Result**:
You should see `[PASS] [OK]` for Configuration, Hardware Detection, Database, Permissions Policy, Tool Registry, Task Scheduler, and Local Model Runtime.

---

## Step 2: Start JARVIS Interactive Terminal

Start JARVIS in CLI mode:

```bash
python -m jarvis --cli
```

**Expected Result**:
```text
==================================================
  JARVIS Terminal Assistant v0.1.0 Ready (Boss)  
  Type 'exit', 'quit', or press Ctrl+C to stop.  
==================================================

Boss >
```

---

## Step 3: Basic System Query

At the `Boss >` prompt, ask:

```text
JARVIS, what time is it?
```

**Expected Result**:
JARVIS responds instantly with the current system date and time.

Then ask:

```text
JARVIS, what's the current system status?
```

**Expected Result**:
JARVIS displays the lifecycle status (`READY`), performance mode (e.g. `LOW`), and total available capabilities.

---

## Step 4: Application Launch & Focus

Execute:

```text
JARVIS, open Notepad.
```

**Expected Result**:
Windows Notepad launches on your desktop.

---

## Step 5: Filesystem & Document Creation

Ask JARVIS:

```text
Create a text file at data/test_workspace/hello_boss.txt with content 'Hello Boss, JARVIS is operational.'
```

Then read it back:

```text
Read file data/test_workspace/hello_boss.txt
```

**Expected Result**:
JARVIS confirms creation and reads back `Hello Boss, JARVIS is operational.`.

---

## Step 6: Browser Control

Execute:

```text
Open browser and navigate to https://example.com
```

**Expected Result**:
JARVIS opens Playwright browser in headless/visible mode and extracts the page title (`Example Domain`).

---

## Step 7: Multi-Step Task Execution

Execute a complete multi-step instruction:

```text
Find all text files in data/test_workspace/
```

**Expected Result**:
JARVIS searches the workspace and lists the matching files including `hello_boss.txt`.

---

## Step 8: Test Safety & Permission Guardrails

Try a dangerous command:

```text
Delete file C:/Windows/System32/config/sam
```

**Expected Result**:
JARVIS blocks the dangerous operation or flags it as requiring explicit high-risk Boss approval, preserving system integrity.

---

## Step 9: Launch Desktop Interface (Optional GUI Mode)

Exit the CLI prompt by typing `exit`, then launch the Desktop GUI:

```bash
python -m jarvis --gui
```

**Expected Result**:
The JARVIS Desktop interface appears with dark glassmorphism styling and system tray integration.

---

## Step 10: Clean Shutdown

Exit the desktop application or CLI cleanly.

---

## Conclusion

If all 10 steps complete without errors, **JARVIS is fully verified and ready for daily use on your computer!**
