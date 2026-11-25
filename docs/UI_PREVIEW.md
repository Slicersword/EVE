# Preview EVE’s eyes and controls

Try the touchscreen face in your browser and see the control panel you’ll use on the Pi.

## Touchscreen face

The preview uses EVE’s 1024 × 600 display proportions and the original artwork
for all 90 expressions. Try Idle, Happy, Love and Alert. Alert shows the red stop
signal in the same style.

<iframe id="eve-display-preview" class="eve-display-preview" title="EVE touchscreen preview" sandbox="allow-same-origin" tabindex="-1"></iframe>

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
