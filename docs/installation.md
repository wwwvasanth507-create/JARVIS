# JARVIS Installation & Setup Guide

---

## 1. System Requirements

- **Operating System**: Windows 10/11 (Primary), Linux, macOS
- **Python Version**: Python 3.10+ (Tested on Python 3.14.7)
- **RAM**: Minimum 4 GB (8 GB+ Recommended)
- **Storage**: 500 MB base installation space

---

## 2. Source Installation Steps

1. **Clone Repository**:
   ```bash
   git clone https://github.com/wwwvasanth507-create/JARVIS.git
   cd JARVIS
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Package**:
   ```bash
   pip install -e .[all]
   ```

---

## 3. Running Launchers

- **Desktop Application (Default)**:
  ```bash
  scripts/start_jarvis.bat
  # or
  jarvis
  ```

- **Run Diagnostics**:
  ```bash
  jarvis --doctor
  ```

- **Run Release Check**:
  ```bash
  jarvis --release-check
  ```

- **Run Test Suite**:
  ```bash
  python -m pytest
  ```
