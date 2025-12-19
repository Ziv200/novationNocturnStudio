// Cubase 12+ MIDI Remote Script for Novation Nocturn (via Nocturn Studio)
// Vendor: Novation
// Device: Nocturn Studio

var midiremote_api = require('midiremote_api_v1')

var deviceDriver = midiremote_api.makeDeviceDriver('Novation', 'Nocturn Studio', 'Nocturn Studio Developer')

var midiInput = deviceDriver.mPorts.makeMidiInput("Nocturn Studio Out")
var midiOutput = deviceDriver.mPorts.makeMidiOutput("Nocturn Studio In")

deviceDriver.makeDetectionUnit().detectPortPair(midiInput, midiOutput)
    .expectInputNameEquals('Nocturn Studio Out')
    .expectOutputNameEquals('Nocturn Studio In')

var surface = deviceDriver.mSurface
var hostMapping = deviceDriver.mMapping

// --- SURFACE ELEMENTS ---

var surfaceKnobs = []
var surfaceButtons = []

// Encoders 1-8
for (var i = 0; i < 8; ++i) {
    var knob = surface.makeKnob(i % 4, Math.floor(i / 4), 1, 1)
    knob.mSurfaceValue.mMidiBinding
        .setInputPort(midiInput)
        .bindToControlChange(0, 10 + i)
    knob.mSurfaceValue.mMidiBinding
        .setOutputPort(midiOutput)
        .bindToControlChange(0, 10 + i)
    surfaceKnobs.push(knob)
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
var fader = surface.makeFader(4, 1, 1, 3)
fader.mSurfaceValue.mMidiBinding
    .setInputPort(midiInput)
    .bindToControlChange(0, 19)

// Buttons 1-16
for (var i = 0; i < 16; ++i) {
    var btn = surface.makeButton(i % 8, 4 + Math.floor(i / 8), 1, 1)
    btn.mSurfaceValue.mMidiBinding
        .setInputPort(midiInput)
        .bindToNote(0, 40 + i)
    btn.mSurfaceValue.mMidiBinding
        .setOutputPort(midiOutput)
        .bindToNote(0, 40 + i)
    surfaceButtons.push(btn)
}

// --- HOST MAPPING ---

var mainPage = hostMapping.makePage('Nocturn Studio Page')
var focusQuickControls = mainPage.mHostAccess.mFocusQuickControls

// Map knobs to Focus Quick Controls
for (var i = 0; i < 8; ++i) {
    mainPage.makeValueBinding(surfaceKnobs[i].mSurfaceValue, focusQuickControls.getByIndex(i))
}

// Map some buttons to transport for example
var transport = mainPage.mHostAccess.mTransportPanel
mainPage.makeValueBinding(surfaceButtons[0].mSurfaceValue, transport.mAction.mPlay)
mainPage.makeValueBinding(surfaceButtons[1].mSurfaceValue, transport.mAction.mStop)
mainPage.makeValueBinding(surfaceButtons[2].mSurfaceValue, transport.mAction.mCycle)
mainPage.makeValueBinding(surfaceButtons[3].mSurfaceValue, transport.mAction.mRecord)
