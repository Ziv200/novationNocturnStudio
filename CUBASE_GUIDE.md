# 🎹 Using Nocturn Studio with Cubase

Follow this guide to get your Novation Nocturn perfectly integrated with Cubase plugins.

## 1. Cubase MIDI Setup
Before anything else, Cubase needs to see the virtual MIDI ports created by Nocturn Studio.

1.  Launch **Nocturn Studio**.
2.  In Cubase, go to **Studio > Studio Setup...**
3.  Navigate to **MIDI Port Setup**.
4.  Ensure both `Nocturn Studio Out` and `Nocturn Studio In` are visible and marked as **Active**.
5.  *(Optional but Recommended)*: Create a **Generic Remote** or **Quick Controls** setup if you want deep integration with Cubase's own mixer, but for VSTs, standard MIDI Learn is easiest.

## 2. The "Automap" Experience (Auto-Focus)
Nocturn Studio watches your screen to know which plugin you're touching.

1.  Open any VST (e.g., Serum, FabFilter).
2.  Click on the VST window to focus it.
3.  Look at Nocturn Studio—it should now say **"Focus: [Plugin Name]"**.
4.  The hardware will immediately switch to the mappings you've saved for that specific plugin.

## 3. How to Map a New VST (MIDI Learn)
If you have a fresh plugin with no mappings, follow these steps:

1.  **Open the Plugin** window in Cubase.
2.  In Nocturn Studio, click the red **MIDI LEARN** button (it will stay red/lit).
3.  **Hardware Step**: Touch the physical knob or button on your Nocturn that you want to use.
4.  **Software Step**: Move the parameter inside the VST window using your mouse.
5.  **Done!** Nocturn Studio will capture the link.
6.  Click **MIDI LEARN** again to exit and save your profile.

## 4. Pro Tips
- **The Speed Dial**: The Speed Dial is always ready. Hover your mouse over any parameter in Cubase and turn it!
- **Global Fallback**: If no plugin is focused, the app returns to your "Global" mapping (perfect for generic CC control).
- **Multiple VSTs**: If you have two plugins open, the mappings will swap instantly as you click between their windows.

---

## 🚀 Advanced Setup: MIDI Remote (Cubase 12+)
If you are using Cubase 12 or 13, you can use the **MIDI Remote Manager** for the ultimate experience. This allows Cubase to "see" your Nocturn as a native controller.

### 1. I've already installed the script for you!
I have placed a custom `nocturn_studio.js` driver in your Cubase user directory:
`~/Documents/Steinberg/Cubase/MIDI Remote/Driver Scripts/Local/Novation/Nocturn`

### 2. Activation
1.  Open Cubase.
2.  Go to the **Lower Zone** and click the **MIDI Remote** tab.
3.  Click the **+** (plus) icon to add a new surface.
4.  Select **Novation** as the vendor and **Nocturn Studio** as the model.
5.  Set the MIDI ports to:
    -   **Input**: `Nocturn Studio Out`
    -   **Output**: `Nocturn Studio In`

### 3. Benefits
Once active, you can:
-   **Auto-Map to Selected Track**: Knobs will automatically control the EQ, Pan, or Inserts of whichever track you click in Cubase.
-   **Focus Quick Controls**: Cubase will handle the "Focus" logic natively, perfectly synced with your hardware LEDs.

---

## 🛠️ Troubleshooting

### 1. "Focus" state not changing? (Accessibility Permissions)
macOS requires explicit permission for Nocturn Studio to see your window titles.
1.  Go to **System Settings > Privacy & Security > Accessibility**.
2.  Ensure **Terminal** (or your IDE) and **Nocturn Studio** are toggled **ON**.
3.  If they are already on, try toggling them OFF and back ON again.

### 2. Can't see MIDI Ports in Cubase?
If `Nocturn Studio Out` or `In` are missing from the dropdowns:
1.  Close Cubase.
2.  Make sure **Nocturn Studio** is running *first*.
3.  Open Cubase. The virtual ports are created dynamically; Cubase needs to be open *after* the ports exist.

### 3. Prefer our mapping over Cubase's MIDI Remote?
If you'd rather our Python app handle all the plugin switching:
-   You don't *need* the MIDI Remote script. You can simply use the `Nocturn Studio Out` port as a standard MIDI Input on your Instrument Tracks.
-   However, keeping the script active provides a nice visual layout in Cubase's Lower Zone.
