# 🎛️ Channel Strip Integration Guide

Nocturn Studio is designed to turn your hardware into a **Fixed physical console**. This means Knob 1 is always your high frequency, Knob 2 is always high gain, etc., across all your mixing plugins.

## 🚀 Quick Start: SSL Native
We have already pre-mapped the **SSL Native Channel Strip**. 
1. Open the SSL Native plugin window in Cubase.
2. The Nocturn UI will turn **Green** and show `Focus: SSLChannel`.
3. Your 8 knobs are now instantly linked:
    - **Knob 1-2**: EQ High (Freq / Gain)
    - **Knob 3-4**: EQ Hi-Mid (Freq / Gain)
    - **Knob 5-6**: EQ Lo-Mid (Freq / Gain)
    - **Knob 7-8**: EQ Low (Freq / Gain)
    - **Crossfader**: Output Gain

---

## 🌊 How to add Waves SSL (and others)

To make a new plugin behave like a physical console, you have two options:

### Option 1: The "Standard Layout" (Recommended)
By default, any new plugin (like Waves SSL) will use our **Standard CC Layout** (Knobs = CC 10-17).
1. Open your plugin (e.g., Waves SSL E-Channel).
2. Right-click the **High Freq** knob in the plugin and select **MIDI Learn**.
3. Turn **Knob 1** on the Nocturn. 
4. Repeat for the other 7 knobs.
5. **Done!** Because the app saves this profile, Knob 1 will now *always* be High Freq for that plugin forever.

### Option 2: Create a Functional Profile (Advanced)
If you want the UI to show specific names like "SSL Comp" and have it pre-mapped without internal MIDI Learn:
1. Go to `~/Library/Application Support/NocturnStudio/presets/`.
2. Duplicate `SSLChannel.json`.
3. Rename it to match your plugin's focus name (e.g., `Waves SSL.json`).
4. Edit the CC numbers in the file to match the plugin's default MIDI implementation.

---

## 📋 The "Standard Console" Layout
Follow this reference to keep your plugins consistent:

| Hardware | Function | Default CC |
| :--- | :--- | :--- |
| **Knob 1** | EQ High Freq | 10 |
| **Knob 2** | EQ High Gain | 11 |
| **Knob 3** | EQ Hi-Mid Freq | 12 |
| **Knob 4** | EQ Hi-Mid Gain | 13 |
| **Knob 5** | EQ Lo-Mid Freq | 14 |
| **Knob 6** | EQ Lo-Mid Gain | 15 |
| **Knob 7** | EQ Low Freq | 16 |
| **Knob 8** | EQ Low Gain | 17 |
| **Crossfader** | Output Gain | 19 |

> [!TIP]
> Use the **MIDI LEARN** button in the Nocturn UI if you want to quickly re-assign a knob to a different CC without editing files.
