# Preview EVE’s eyes and controls

Try the touchscreen face in your browser and see the control panel you’ll use on the Pi.

## Touchscreen face

The preview uses the same Lumen renderer as EVE’s 1024 × 600 touchscreen.
Try Happy for the wider smile, Speaking for the animated mouth, Love for the heart
pupils and Alert for the red stop face. All 90 expressions share the same eye
design and lighting. The preview follows your system’s reduced-motion preference.

On the Pi, eSpeak NG turns EVE's replies into audio in English, Hindi or Marathi.
The Speaking expression animates the mouth while EVE talks. **Play cue** plays a
short expression sound from the bundled WAV pack. See [voice setup at M13](SETUP_GUIDE.md#m13).

<link rel="stylesheet" href="assets/ui-preview/eve-face.css">
<div id="eve-display-preview" class="eve-display-preview"></div>

<div class="eve-preview-controls">
  <label for="eve-preview-expression">Expression</label>
  <select id="eve-preview-expression" disabled></select>
  <button id="eve-preview-blink" type="button" disabled>Blink</button>
  <div class="eve-preview-gaze" role="group" aria-label="Eye direction">
    <button type="button" data-eve-preview-direction="-6" disabled>Look left</button>
    <button type="button" data-eve-preview-direction="0" disabled>Centre</button>
    <button type="button" data-eve-preview-direction="6" disabled>Look right</button>
  </div>
</div>
<div class="eve-preview-controls">
  <button id="eve-preview-play" type="button" disabled>Play cue</button>
  <button id="eve-preview-stop" type="button" disabled>Stop cue</button>
  <span id="eve-preview-status" role="status"></span>
</div>
<noscript>Enable JavaScript to try the expressions and sound samples.</noscript>
<script defer src="assets/ui-preview/kiosk-data.js"></script>
<script defer src="assets/ui-preview/preview.js"></script>

[Check the real touchscreen at M01](SETUP_GUIDE.md#m01).

## Control panel

Explore the status table, speech controls, session controls, and wheel and head tests. This is a read-only sample from before calibration.

<iframe class="eve-control-preview" src="assets/ui-preview/control.html" title="Read-only EVE control panel with sample status" loading="lazy" sandbox></iframe>

[Open the control preview in a full page](assets/ui-preview/control.html).

[Set up the live control panel at M16](SETUP_GUIDE.md#m16).
