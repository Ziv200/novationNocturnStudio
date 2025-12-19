// Cubase 12+ MIDI Remote Script for Novation Nocturn (via Nocturn Studio)
// Vendor: Novation
// Device: NocturnStudio

var midiremote_api = require('midiremote_api_v1')

var deviceDriver = midiremote_api.makeDeviceDriver('Novation', 'NocturnStudio', 'Nocturn Studio Developer')

// We define the ports but don't force automatic detection.
// This allows the user to manually select "Nocturn Studio Out" and "In" 
// in the MIDI Remote Manager if detection fails.
var midiInput = deviceDriver.mPorts.makeMidiInput("Nocturn Studio Out")
var midiOutput = deviceDriver.mPorts.makeMidiOutput("Nocturn Studio In")

var surface = deviceDriver.mSurface

// --- SURFACE ELEMENTS ---

// Encoders 1-8
for (var i = 0; i < 8; ++i) {
    var knob = surface.makeKnob(i % 4, Math.floor(i / 4), 1, 1)
    knob.mSurfaceValue.mMidiBinding
        .setInputPort(midiInput)
        .bindToControlChange(0, 10 + i)
    knob.mSurfaceValue.mMidiBinding
        .setOutputPort(midiOutput)
        .bindToControlChange(0, 10 + i)
}

// Speed Dial (CC 18)
var speedDial = surface.makeKnob(4, 0, 1, 1)
speedDial.mSurfaceValue.mMidiBinding
    .setInputPort(midiInput)
    .bindToControlChange(0, 18)
speedDial.mSurfaceValue.mMidiBinding
    .setOutputPort(midiOutput)
    .bindToControlChange(0, 18)

// Crossfader (CC 19)
var fader = surface.makeFader(0, 2, 8, 1)
fader.mSurfaceValue.mMidiBinding
    .setInputPort(midiInput)
    .bindToControlChange(0, 19)

// Buttons 1-16
for (var i = 0; i < 16; ++i) {
    var btn = surface.makeButton(i % 8, 3 + Math.floor(i / 8), 1, 1)
    btn.mSurfaceValue.mMidiBinding
        .setInputPort(midiInput)
        .bindToNote(0, 40 + i)
    btn.mSurfaceValue.mMidiBinding
        .setOutputPort(midiOutput)
        .bindToNote(0, 40 + i)
}

// NOTE: We do NOT define host mappings here. 
// This allows the user to use them as standard MIDI CCs for per-plugin mapping 
// in our Python app, or manually map them in Cubase if desired.
