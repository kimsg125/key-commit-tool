# Automated Key Committing Attack Analysis Tool

This tool automates the analysis of key committing attacks for AES-based AEAD (Authenticated Encryption with Associated Data) schemes, specifically designed to evaluate attack complexity. The tool is built to align with the most restrictive key commitment framework, FROB, and provides accurate complexity calculations by identifying fixed values in state block equations. 

### Requirements
- Python 3.x
- PyQt5
- PyInstaller (for generating standalone executables, if needed)

### Run the tool directly using Python:
```bash
python key_committing_tool_gui.py
```

### To create an executable file for the tool:
```
pyinstaller key_committing_tool_gui.spec
```
