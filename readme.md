# Nocturn Studio 💎

**Nocturn Studio** is a modern, Apple Silicon-native macOS application designed to bring the Novation Nocturn controller back to life. No Automap, no legacy drivers—just pure, reliable, and customizable control for your DAW.

## ✨ Features
- **Plug & Play**: Works with real Nocturn hardware via direct USB communication.
- **Visual Feedback**: Real-time LED ring and button feedback on the hardware, synchronized with a beautiful Dark UI.
- **DAW Agnostic**: Sends standard MIDI CC and Note messages.
- **High Resolution**: Smooth, high-fidelity encoder handling.
- **Thread-Safe**: Robust architecture preventing crashes during heavy interaction.

## 🚀 Getting Started

### Prerequisites
- macOS (Intel or Apple Silicon)
- Python 3.12+
- `libusb` (Installed via Homebrew: `brew install libusb`)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nocturn-studio.git
   cd nocturn-studio
   ```
2. Install dependencies:
   ```bash
   pip install -e .
   ```

### Running the App
Launch the application from your terminal:
```bash
nocturn-studio
```

## 🛠️ Project Structure
- `src/nocturn_studio/hardware`: Low-level USB/MIDI communication.
- `src/nocturn_studio/engine`: Mapping and logic engine.
- `src/nocturn_studio/ui`: PySide6-based graphical interface.
- `src/nocturn_studio/model`: Core data definitions and events.

## 📜 Technical Details
- **Language**: Python 3.12+
- **GUI Framework**: PySide6 (Qt)
- **Hardware Communication**: PyUSB (libusb)
- **MIDI Output**: python-rtmidi

## 📄 License
MIT License.
