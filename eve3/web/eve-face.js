/* The kiosk, Expression Studio, Home and build guide share this display. */
(() => {
  'use strict';

  // Eye openings and mouth dimensions are percentages of the display.
  // Gaze is the pose's resting direction. Tracking can override it.
  const poses = {
    idle:          {eyes: [34, 34], mouth: ['smile', 15, 6]},
    listening:     {eyes: [38, 38], width: 18, mouth: ['open', 5, 7]},
    thinking:      {eyes: [28, 22], mouth: ['flat', 7, 2], gaze: [4, -2]},
    speaking:      {eyes: [34, 34], mouth: ['talk', 11, 11]},
    happy:         {eyes: [18, 18], lids: 'arch', mouth: ['smile', 22, 10]},
    sleepy:        {eyes: [3, 3], mouth: ['flat', 6, 2], opacity: .56},
    alert:         {eyes: [28, 28], lids: 'square', mouth: ['flat', 12, 2]},
    sad:           {eyes: [21, 21], lids: 'droop', tilt: [-11, 11], mouth: ['frown', 13, 8]},
    angry:         {eyes: [24, 24], tilt: [17, -17], mouth: ['frown', 15, 6]},
    surprised:     {eyes: [40, 40], width: 19, mouth: ['open', 7, 10]},
    excited:       {eyes: [31, 31], lids: 'arch', width: 19, mouth: ['open', 17, 12]},
    curious:       {eyes: [37, 24], mouth: ['open', 5, 6], gaze: [4, -1]},
    proud:         {eyes: [22, 22], lids: 'arch', mouth: ['smile', 18, 6], gaze: [0, -2]},
    confused:      {eyes: [29, 18], tilt: [-9, 15], mouth: ['pout', 10, 4]},
    love:          {eyes: [23, 23], lids: 'arch', tilt: [-7, 7], mouth: ['smile', 20, 9]},
    laughing:      {eyes: [8, 8], lids: 'arch', mouth: ['open', 20, 16]},
    scared:        {eyes: [41, 41], width: 14, mouth: ['open', 7, 10], gaze: [0, -2]},
    bored:         {eyes: [11, 11], lids: 'droop', mouth: ['flat', 10, 2], gaze: [-5, 1]},
    shy:           {eyes: [21, 14], lids: 'arch', mouth: ['smile', 9, 5], gaze: [-4, 3]},
    determined:    {eyes: [25, 25], tilt: [12, -12], mouth: ['flat', 13, 2]},
    namaste:       {eyes: [6, 6], lids: 'arch', mouth: ['smile', 15, 7], gaze: [0, 3]},
    diwali:        {eyes: [29, 29], lids: 'arch', width: 18, mouth: ['smile', 23, 11]},
    woozy:         {eyes: [26, 16], tilt: [-18, -15], mouth: ['pout', 11, 5], gaze: [-3, 2]},
    shocked:       {eyes: [45, 45], width: 17, mouth: ['open', 9, 13]},
    mischievous:   {eyes: [23, 8], lids: 'arch', tilt: [0, -10], mouth: ['smirk', 16, 6], gaze: [4, 0]},
    starstruck:    {eyes: [41, 38], width: 19, mouth: ['smile', 20, 10], gaze: [0, -4]},
    dead:          {eyes: [3, 3], mouth: ['flat', 14, 2], opacity: .62},
    embarrassed:   {eyes: [25, 25], tilt: [-9, 9], mouth: ['pout', 7, 4], gaze: [-6, 3]},
    disgusted:     {eyes: [17, 25], tilt: [12, 4], mouth: ['frown', 13, 5], gaze: [-5, 0]},
    nervous:       {eyes: [33, 30], tilt: [-7, 6], mouth: ['flat', 8, 3], gaze: [4, 2]},
    grateful:      {eyes: [15, 15], lids: 'arch', mouth: ['smile', 17, 8], gaze: [0, 1]},
    calm:          {eyes: [24, 24], mouth: ['smile', 14, 6], opacity: .9},
    focused:       {eyes: [20, 20], width: 15, tilt: [8, -8], mouth: ['flat', 9, 2]},
    skeptical:     {eyes: [31, 14], tilt: [-4, 10], mouth: ['flat', 11, 2], gaze: [3, 0]},
    guilty:        {eyes: [18, 14], lids: 'droop', mouth: ['frown', 8, 5], gaze: [-4, 4]},
    relieved:      {eyes: [13, 13], lids: 'arch', mouth: ['smile', 19, 7], gaze: [0, 2]},
    amazed:        {eyes: [40, 40], width: 18, mouth: ['open', 8, 9], gaze: [0, -4]},
    hopeful:       {eyes: [30, 30], lids: 'arch', mouth: ['smile', 16, 7], gaze: [0, -3]},
    worried:       {eyes: [29, 29], tilt: [-13, 13], mouth: ['frown', 11, 7], gaze: [0, -1]},
    playful:       {eyes: [19, 7], lids: 'arch', mouth: ['smile', 21, 10], gaze: [4, -1]},
    offended:      {eyes: [20, 18], tilt: [10, -13], mouth: ['frown', 12, 5], gaze: [5, -1]},
    delighted:     {eyes: [20, 20], lids: 'arch', mouth: ['open', 18, 12]},
    tranquil:      {eyes: [10, 10], lids: 'arch', mouth: ['smile', 13, 5], opacity: .8},
    suspicious:    {eyes: [19, 12], tilt: [6, -13], mouth: ['flat', 12, 2], gaze: [6, 0]},
    dreamy:        {eyes: [17, 15], lids: 'droop', mouth: ['smile', 14, 6], gaze: [4, -4], opacity: .85},
    impatient:     {eyes: [18, 18], tilt: [10, -10], mouth: ['flat', 13, 2], gaze: [0, -2]},
    proud_tears:   {eyes: [25, 25], lids: 'droop', tilt: [-8, 8], mouth: ['smile', 18, 9], gaze: [0, -2]},
    empathetic:    {eyes: [23, 23], lids: 'droop', tilt: [-7, 7], mouth: ['smile', 13, 5]},
    jealous:       {eyes: [13, 23], tilt: [13, -8], mouth: ['frown', 12, 5], gaze: [5, 0]},
    awkward:       {eyes: [31, 23], tilt: [-4, 7], mouth: ['smirk', 10, 4], gaze: [-3, 1]},
    zen:           {eyes: [4, 4], lids: 'arch', mouth: ['smile', 12, 5], opacity: .82},
    glitch:        {eyes: [34, 10], lids: 'square', tilt: [0, 13], mouth: ['pout', 13, 3], gaze: [2, 1]},
    loading:       {eyes: [19, 19], width: 13, mouth: ['flat', 6, 2], gaze: [0, 0]},
    inspired:      {eyes: [35, 35], lids: 'arch', mouth: ['smile', 20, 10], gaze: [2, -4]},
    sleepy_happy:  {eyes: [6, 6], lids: 'arch', mouth: ['smile', 16, 7], opacity: .72},
    smug:          {eyes: [16, 11], lids: 'droop', tilt: [0, -5], mouth: ['smirk', 16, 5], gaze: [4, -1]},
    pleading:      {eyes: [37, 37], width: 18, lids: 'droop', tilt: [-8, 8], mouth: ['open', 5, 5], gaze: [0, -2]},
    touched:       {eyes: [24, 24], lids: 'droop', tilt: [-5, 5], mouth: ['smile', 15, 8]},
    victory:       {eyes: [10, 10], lids: 'arch', tilt: [-10, 10], mouth: ['open', 21, 15], gaze: [0, -3]},
    meltdown:      {eyes: [12, 20], lids: 'square', tilt: [17, -17], mouth: ['open', 12, 12], gaze: [0, 2]},
    ecstatic:      {eyes: [13, 13], lids: 'arch', width: 19, mouth: ['open', 23, 18]},
    frustrated:    {eyes: [19, 19], tilt: [17, -17], mouth: ['frown', 15, 8], gaze: [0, 1]},
    satisfied:     {eyes: [17, 17], lids: 'arch', mouth: ['smile', 16, 7]},
    anxious:       {eyes: [34, 31], tilt: [-11, 11], mouth: ['pout', 8, 5], gaze: [0, 2]},
    content:       {eyes: [20, 20], lids: 'arch', mouth: ['smile', 14, 7], opacity: .94},
    melancholy:    {eyes: [17, 17], lids: 'droop', tilt: [-7, 7], mouth: ['frown', 14, 5], gaze: [0, 4]},
    wonder:        {eyes: [37, 37], width: 17, mouth: ['open', 6, 8], gaze: [2, -3]},
    blissful:      {eyes: [9, 9], lids: 'arch', mouth: ['smile', 22, 9], gaze: [0, 2]},
    contemplative: {eyes: [23, 19], lids: 'droop', mouth: ['flat', 9, 2], gaze: [4, -2]},
    annoyed:       {eyes: [16, 20], tilt: [12, -11], mouth: ['flat', 13, 2], gaze: [-4, 0]},
    exhausted:     {eyes: [5, 5], lids: 'droop', mouth: ['frown', 10, 4], gaze: [0, 4], opacity: .63},
    compassionate: {eyes: [25, 25], lids: 'droop', tilt: [-10, 10], mouth: ['smile', 14, 6], gaze: [0, 1]},
    smitten:       {eyes: [18, 18], lids: 'arch', tilt: [-9, 9], mouth: ['smile', 22, 9], gaze: [2, -1]},
    heartbroken:   {eyes: [15, 15], lids: 'droop', tilt: [-15, 15], mouth: ['frown', 16, 9], gaze: [0, 3]},
    thrilled:      {eyes: [35, 35], lids: 'arch', width: 18, mouth: ['open', 15, 12], gaze: [0, -2]},
    intrigued:     {eyes: [33, 20], tilt: [-6, 8], mouth: ['smile', 10, 5], gaze: [5, -2]},
    yearning:      {eyes: [30, 30], lids: 'droop', tilt: [-9, 9], mouth: ['flat', 7, 2], gaze: [4, -2]},
    relaxed:       {eyes: [14, 14], lids: 'arch', mouth: ['smile', 15, 5], gaze: [0, 2], opacity: .85},
    snappy:        {eyes: [21, 17], tilt: [17, -13], mouth: ['pout', 11, 4], gaze: [4, 0]},
    apologetic:    {eyes: [20, 20], lids: 'droop', tilt: [-10, 10], mouth: ['frown', 9, 4], gaze: [0, 4]},
    proud_smile:   {eyes: [24, 24], lids: 'arch', mouth: ['smile', 22, 7], gaze: [0, -2]},
    grumpy:        {eyes: [13, 13], lids: 'droop', tilt: [13, -13], mouth: ['frown', 13, 7]},
    flirty:        {eyes: [22, 4], lids: 'arch', tilt: [-5, 5], mouth: ['smirk', 18, 8]},
    sympathetic:   {eyes: [19, 19], lids: 'droop', tilt: [-9, 9], mouth: ['smile', 12, 5], gaze: [0, 2]},
    confident:     {eyes: [26, 26], lids: 'arch', tilt: [5, -5], mouth: ['smirk', 18, 7]},
    flustered:     {eyes: [30, 19], tilt: [-12, 10], mouth: ['open', 5, 6], gaze: [-4, 3]},
    divine:        {eyes: [11, 11], lids: 'arch', mouth: ['smile', 20, 8], gaze: [0, -4]},
    snarky:        {eyes: [12, 24], tilt: [-5, 10], mouth: ['smirk', 15, 6], gaze: [5, 1]},
    haunted:       {eyes: [43, 40], width: 14, mouth: ['open', 6, 12], opacity: .84},
    victorious:    {eyes: [14, 14], lids: 'arch', tilt: [-8, 8], mouth: ['open', 23, 15], gaze: [0, -2]},
  };

  function title(name) {
    return name.replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase());
  }

  function mount(screen) {
    screen.classList.add('eve-face');
    screen.setAttribute('role', 'img');
    screen.innerHTML = '<div class="eve-face__eyes"><div class="eve-face__eye"></div>'
      + '<div class="eve-face__eye"></div></div><div class="eve-face__mouth"></div>';
    const eyes = screen.querySelector('.eve-face__eyes');
    const lids = Array.from(eyes.children);
    const mouth = screen.querySelector('.eve-face__mouth');
    let expression, blinkTimer;
    let lookX, lookY;

    function updateGaze() {
      const [poseX, poseY] = poses[expression].gaze ?? [0, 0];
      eyes.style.setProperty('--look-x', (lookX ?? poseX) + '%');
      eyes.style.setProperty('--look-y', (lookY ?? poseY) + '%');
    }

    function show(name) {
      const next = Object.hasOwn(poses, name) ? name : 'idle';
      if (next === expression) return;
      expression = next;
      const pose = poses[next];
      screen.dataset.expression = next;
      screen.dataset.lids = pose.lids ?? 'oval';
      screen.style.setProperty('--face-opacity', pose.opacity ?? 1);
      screen.setAttribute('aria-label', 'EVE expression: ' + title(next));
      clearTimeout(blinkTimer);
      screen.classList.remove('is-blinking');
      for (const [index, lid] of lids.entries()) {
        lid.style.setProperty('--eye-width', (pose.width ?? 17) + '%');
        lid.style.setProperty('--eye-height', pose.eyes[index] + '%');
        lid.style.setProperty('--eye-tilt', (pose.tilt?.[index] ?? 0) + 'deg');
      }
      const [shape, width, height] = pose.mouth;
      mouth.dataset.shape = shape;
      mouth.style.setProperty('--mouth-width', width + '%');
      mouth.style.setProperty('--mouth-height', height + '%');
      updateGaze();
    }

    function look(x, y) {
      if (x === lookX && y === lookY) return;
      lookX = x;
      lookY = y;
      updateGaze();
    }

    function blink() {
      screen.classList.add('is-blinking');
      clearTimeout(blinkTimer);
      blinkTimer = setTimeout(() => screen.classList.remove('is-blinking'), 150);
    }

    show('idle');
    return {show, look, blink};
  }

  window.EveFace = Object.freeze({mount, title, names: Object.freeze(Object.keys(poses))});
})();
