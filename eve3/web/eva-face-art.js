/* Lumen expression poses, ordered to match the expression sound catalog. */
(() => {
  'use strict';
  const profiles = Object.create(null);

  function pose(name, changes, from = 'idle') {
    profiles[name] = Object.freeze({...profiles[from], ...changes});
  }

  pose('idle', {
    left: 1, right: 1, tiltL: 0, tiltR: 0, x: 0, y: 0, pupil: .54,
    hue: 177, brow: 0, furrow: 0, smile: .22, jaw: 0, blush: 0, tear: 0,
    mark: '', accent: '',
  });
  pose('listening', {left: 1.07, right: 1.07, y: -.13, pupil: .58, hue: 173, brow: .29, smile: .1, accent: 'listen'});
  pose('thinking', {left: .65, right: .85, x: .25, y: -.28, pupil: .43, hue: 210, brow: .35, smile: 0, accent: 'dots'});
  pose('speaking', {left: .95, right: .95, hue: 165, smile: .38, jaw: .32});
  pose('happy', {left: .82, right: .82, pupil: .61, hue: 169, smile: .86, jaw: .22, blush: .7});
  pose('sleepy', {left: .22, right: .25, y: .14, pupil: .44, hue: 218, smile: .05, jaw: .12});
  pose('alert', {left: .62, right: .62, tiltL: .1, tiltR: -.1, pupil: .36, hue: 7, brow: -.36, furrow: .7, smile: -.14});
  pose('sad', {left: .71, right: .71, tiltL: -.12, tiltR: .12, y: .25, hue: 211, brow: .28, furrow: -.72, smile: -.7, tear: .85});
  pose('angry', {left: .66, right: .66, tiltL: .16, tiltR: -.16, pupil: .41, hue: 22, brow: -.55, furrow: 1, smile: -.7});
  pose('surprised', {left: 1.16, right: 1.16, pupil: .4, hue: 48, brow: .78, smile: 0, jaw: .93});
  pose('excited', {left: 1.06, right: 1.06, y: -.18, pupil: .58, hue: 155, brow: .48, smile: .98, jaw: .66, blush: .85});
  pose('curious', {left: 1.12, right: .8, tiltL: -.055, tiltR: .05, x: .18, y: -.12, brow: .4, smile: .13});
  pose('proud', {left: .72, right: .72, tiltL: -.03, tiltR: .03, y: -.13, hue: 41, smile: .65});
  pose('confused', {left: .62, right: 1.12, tiltL: .11, tiltR: -.065, x: -.15, hue: 51, brow: .5, furrow: -.46, smile: -.24});
  pose('love', {left: .87, right: .87, pupil: .66, hue: 333, smile: .74, blush: .96, mark: 'heart'});
  pose('laughing', {left: .08, right: .08, tiltL: -.12, tiltR: .12, hue: 159, smile: 1, jaw: 1, blush: 1});
  pose('scared', {left: 1.04, right: 1.04, tiltL: -.11, tiltR: .11, y: -.11, pupil: .31, hue: 268, brow: .85, furrow: -.68, smile: -.34, jaw: .49});
  pose('bored', {left: .4, right: .47, x: -.29, y: -.1, pupil: .46, hue: 203, smile: -.09});
  pose('shy', {left: .74, right: .8, tiltL: .06, tiltR: -.035, x: -.15, y: .2, hue: 323, smile: .48, blush: 1});
  pose('determined', {left: .76, right: .76, tiltL: .1, tiltR: -.1, pupil: .43, hue: 181, brow: -.4, furrow: .59, smile: .15});
  pose('namaste', {left: .085, right: .085, y: .1, hue: 34, smile: .55, blush: .3});
  pose('diwali', {left: .96, right: .96, pupil: .62, hue: 43, smile: .92, jaw: .44, blush: .65, accent: 'sparkles'});
  pose('woozy', {left: .82, right: .61, tiltL: -.16, tiltR: .19, x: .15, y: .1, hue: 254, brow: .35, smile: -.18, jaw: .21, mark: 'spiral'});
  pose('shocked', {left: 1.23, right: 1.23, pupil: .31, hue: 33, brow: 1, jaw: 1.1}, 'surprised');
  pose('mischievous', {left: .56, right: .87, tiltL: .1, tiltR: -.13, x: .24, hue: 160, brow: .31, smile: .61});
  pose('starstruck', {left: 1.1, right: 1.1, y: -.13, pupil: .68, hue: 46, smile: .68, jaw: .65, mark: 'star'});
  pose('dead', {left: .76, right: .76, hue: 234, smile: 0, mark: 'cross'});
  pose('embarrassed', {left: .9, right: .9, x: -.23, y: .29, hue: 348, smile: .06}, 'shy');
  pose('disgusted', {left: .52, right: .73, tiltL: .14, tiltR: .04, x: -.2, hue: 88, brow: -.24, furrow: .5, smile: -.56});
  pose('nervous', {left: .94, right: .86, x: .24, pupil: .39, hue: 281, brow: .4, furrow: -.59, smile: .15, jaw: .21, blush: .4});
  pose('grateful', {left: .73, right: .73, y: .09, hue: 45, smile: .61, blush: .42});
  pose('calm', {left: .55, right: .55, pupil: .49, hue: 189, smile: .36});
  pose('focused', {left: .67, right: .67, tiltL: .045, tiltR: -.045, pupil: .4, hue: 188, brow: -.18, furrow: .4, smile: 0});
  pose('skeptical', {left: .51, right: .94, tiltL: .1, tiltR: -.07, x: .19, hue: 201, brow: .37, furrow: .62, smile: -.08});
  pose('guilty', {left: .64, right: .73, x: -.22, y: .29, hue: 240, brow: .23, smile: -.29, tear: 0}, 'sad');
  pose('relieved', {left: .43, right: .43, y: .08, hue: 171, smile: .53, jaw: .11}, 'calm');
  pose('amazed', {left: 1.13, right: 1.13, y: -.28, pupil: .47, hue: 50, brow: .65, smile: .29, jaw: .77}, 'surprised');
  pose('hopeful', {left: .84, right: .84, y: -.28, pupil: .63, hue: 148, brow: .25, smile: .48, blush: .3});
  pose('worried', {left: .84, right: .84, tiltL: -.09, tiltR: .09, x: .08, y: .19, hue: 216, brow: .48, smile: -.49, tear: 0}, 'sad');
  pose('playful', {left: .72, right: 1.02, tiltL: -.08, tiltR: -.05, x: .22, hue: 166, smile: .8, blush: .5});
  pose('offended', {left: .56, right: .69, x: .26, y: -.18, hue: 298, brow: -.27, smile: -.49}, 'angry');
  pose('delighted', {left: .66, right: .66, hue: 157, smile: .9, jaw: .4, blush: 1}, 'happy');
  pose('tranquil', {left: .39, right: .39, hue: 190, smile: .29}, 'calm');
  pose('suspicious', {left: .58, right: .7, x: -.31, hue: 208, brow: -.11, smile: -.22}, 'skeptical');
  pose('dreamy', {left: .51, right: .6, x: -.05, y: -.23, pupil: .59, hue: 256, smile: .49, blush: .49});
  pose('impatient', {left: .61, right: .51, x: .3, y: -.2, hue: 31, brow: -.25, smile: -.47}, 'angry');
  pose('proud_tears', {left: .76, right: .76, y: -.19, brow: .35, furrow: -.39, smile: .77, tear: 1}, 'proud');
  pose('empathetic', {left: .73, right: .77, y: .13, pupil: .6, hue: 187, brow: .42, furrow: -.54, smile: .3});
  pose('jealous', {left: .68, right: .56, x: -.29, hue: 112, smile: -.56}, 'angry');
  pose('awkward', {left: .96, right: .78, x: .3, y: .02, hue: 54, brow: .29, smile: .21, blush: .53});
  pose('zen', {left: .075, right: .075, tiltL: -.02, tiltR: .02, hue: 188, smile: .31});
  pose('glitch', {left: .64, right: 1.07, tiltL: -.13, tiltR: .16, x: -.18, pupil: .39, hue: 283, smile: -.07, mark: 'scan'});
  pose('loading', {left: .66, right: .66, hue: 194, pupil: .5, smile: 0, accent: 'dots'});
  pose('inspired', {left: 1, right: 1.04, y: -.28, pupil: .57, hue: 48, brow: .52, smile: .73, accent: 'sparkles'});
  pose('sleepy_happy', {left: .18, right: .2, hue: 212, smile: .59, jaw: 0, blush: .35}, 'sleepy');
  pose('smug', {left: .53, right: .68, x: .19, y: -.1, hue: 193, brow: .19, smile: .58}, 'mischievous');
  pose('pleading', {left: 1.1, right: 1.1, y: -.18, pupil: .69, hue: 224, brow: .59, furrow: -.8, smile: -.32, tear: .29});
  pose('touched', {left: .72, right: .73, hue: 173, brow: .26, smile: .61, tear: .82, blush: .43}, 'empathetic');
  pose('victory', {left: .45, right: .45, y: -.1, hue: 44, smile: 1, jaw: .79, blush: .9, accent: 'sparkles'});
  pose('meltdown', {left: .34, right: .35, tiltL: .2, tiltR: -.2, hue: 16, jaw: .64, tear: .55}, 'angry');
  pose('ecstatic', {left: .32, right: .32, hue: 151, smile: 1, jaw: .85, blush: 1, accent: 'sparkles'});
  pose('frustrated', {left: .52, right: .61, x: .1, y: .08, hue: 27, brow: -.57, smile: -.55, jaw: .12}, 'angry');
  pose('satisfied', {left: .54, right: .54, y: -.04, hue: 162, smile: .62, blush: .2}, 'calm');
  pose('anxious', {left: 1.02, right: .96, x: -.2, hue: 263, brow: .62, smile: -.28, jaw: .32}, 'nervous');
  pose('content', {left: .65, right: .65, hue: 174, smile: .5, blush: .24}, 'calm');
  pose('melancholy', {left: .51, right: .51, x: -.18, y: .22, hue: 226, smile: -.49, tear: .17}, 'sad');
  pose('wonder', {left: 1.09, right: 1.09, y: -.25, pupil: .65, hue: 196, brow: .51, smile: .17, jaw: .48});
  pose('blissful', {left: .095, right: .095, tiltL: -.08, tiltR: .08, hue: 164, smile: .77, blush: .57});
  pose('contemplative', {left: .55, right: .7, x: -.22, y: -.25, hue: 217, brow: .14, smile: .12, accent: ''}, 'thinking');
  pose('annoyed', {left: .47, right: .59, x: -.27, hue: 36, brow: -.46, smile: -.43}, 'angry');
  pose('exhausted', {left: .16, right: .21, y: .21, hue: 231, smile: -.16, jaw: .22}, 'sleepy');
  pose('compassionate', {left: .62, right: .66, y: .12, hue: 155, smile: .38, blush: .43}, 'empathetic');
  pose('smitten', {left: .72, right: .81, x: .17, y: -.13, hue: 319, smile: .8, jaw: .18}, 'love');
  pose('heartbroken', {left: .61, right: .67, y: .28, hue: 285, smile: -.8, jaw: .22, tear: 1}, 'sad');
  pose('thrilled', {left: .86, right: .93, hue: 54, smile: 1, jaw: .71, accent: 'sparkles'}, 'excited');
  pose('intrigued', {left: .87, right: 1.01, x: -.22, y: -.15, hue: 202, brow: .5, smile: .24}, 'curious');
  pose('yearning', {left: .8, right: .8, x: .17, y: -.19, hue: 308, smile: -.28, tear: .38}, 'pleading');
  pose('relaxed', {left: .4, right: .46, x: -.08, hue: 179, smile: .41}, 'calm');
  pose('snappy', {left: .69, right: .74, x: .26, hue: 12, jaw: .27}, 'angry');
  pose('apologetic', {left: .62, right: .62, x: -.12, y: .23, hue: 207, smile: -.31, tear: 0}, 'sad');
  pose('proud_smile', {left: .69, right: .69, hue: 39, smile: .9, jaw: .21, blush: .49}, 'proud');
  pose('grumpy', {left: .38, right: .38, tiltL: .08, tiltR: -.08, x: -.1, hue: 36, brow: -.43, smile: -.58}, 'angry');
  pose('flirty', {left: .075, right: .89, tiltL: -.06, tiltR: -.09, x: .15, hue: 336, smile: .84, blush: .8});
  pose('sympathetic', {left: .58, right: .62, y: .2, hue: 200, smile: .12, tear: .3}, 'empathetic');
  pose('confident', {left: .76, right: .76, tiltL: .04, tiltR: -.04, hue: 177, brow: -.07, smile: .6}, 'proud');
  pose('flustered', {left: 1.02, right: .87, tiltL: -.12, tiltR: .08, x: -.07, y: .15, hue: 350, brow: .35, smile: -.04, jaw: .3}, 'embarrassed');
  pose('divine', {left: .74, right: .74, hue: 48, pupil: .59, smile: .54, mark: 'star', accent: 'sparkles'});
  pose('snarky', {left: .92, right: .47, tiltL: -.11, tiltR: .08, hue: 276, x: -.27, smile: .51}, 'mischievous');
  pose('haunted', {left: 1.19, right: 1.04, hue: 244, pupil: .25, brow: .67, jaw: .62}, 'scared');
  pose('victorious', {left: .73, right: 1.01, y: -.2, hue: 50, brow: .4, jaw: .66, mark: 'star'}, 'victory');

  const title = name => name.replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase());
  window.EvaFaceArt = Object.freeze({
    profiles: Object.freeze(profiles), names: Object.freeze(Object.keys(profiles)), title,
  });
})();
