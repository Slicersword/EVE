/* Approved EVA glossy/vector face library; shared with the 90-expression demo. */
(()=>{'use strict';

const NAMES=["idle", "listening", "thinking", "speaking", "happy", "sleepy", "alert", "sad", "angry", "surprised", "excited", "curious", "proud", "confused", "love", "laughing", "scared", "bored", "shy", "determined", "namaste", "diwali", "woozy", "shocked", "mischievous", "starstruck", "dead", "embarrassed", "disgusted", "nervous", "grateful", "calm", "focused", "skeptical", "guilty", "relieved", "amazed", "hopeful", "worried", "playful", "offended", "delighted", "tranquil", "suspicious", "dreamy", "impatient", "proud_tears", "empathetic", "jealous", "awkward", "zen", "glitch", "loading", "inspired", "sleepy_happy", "smug", "pleading", "touched", "victory", "meltdown", "ecstatic", "frustrated", "satisfied", "anxious", "content", "melancholy", "wonder", "blissful", "contemplative", "annoyed", "exhausted", "compassionate", "smitten", "heartbroken", "thrilled", "intrigued", "yearning", "relaxed", "snappy", "apologetic", "proud_smile", "grumpy", "flirty", "sympathetic", "confident", "flustered", "divine", "snarky", "haunted", "victorious"];
const params=new URLSearchParams(location.search);if(params.has('sheet'))document.body.classList.add('sheet');if(params.has('still'))document.body.classList.add('still');
const pos=new Set('happy excited proud grateful relieved delighted inspired ecstatic satisfied content blissful thrilled victory victorious proud_smile smitten love starstruck sleepy_happy playful hopeful amused grateful laughing touched compassionate empathetic sympathetic confident calm tranquil zen relaxed dreamy amazed wonder'.split(' '));
const neg=new Set('sad angry scared shocked worried anxious annoyed exhausted frustrated melancholy grumpy offended meltdown jealous heartbroken guilty disgusted nervous impatient haunted snappy awkward embarrassed flustered bored skeptical suspicious annoyed apologetic'.split(' '));
const basic=new Set('idle listening thinking speaking sleepy alert curious confused surprised happy laughing angry sad focused loading'.split(' '));
const special=new Set('namaste diwali glitch dead divine flirty starstruck woozy mischievous snarky haunted pleading victory proud_tears'.split(' '));
const groups={
happy:'happy laughing delighted ecstatic thrilled blissful victory victorious pleased satisfied content cheerful inspired excited playful proud proud_smile grateful hopeful relieved touched',
sad:'sad melancholy heartbroken sympathetic compassionate empathetic apologetic guilty touched worried',
angry:'angry annoyed frustrated grumpy snappy offended impatient meltdown disgusted',
wide:'alert surprised shocked amazed wonder starstruck scared haunted ecstatic amazed thrilled',
narrow:'skeptical suspicious determined focused confident snarky smug mischievous jealous',
sleep:'sleepy exhausted dreamy tranquil zen relaxed sleepy_happy blissful calm bored',
love:'love smitten flirty yearning pleading',
think:'thinking curious intrigued contemplative confused loading',
shy:'shy embarrassed awkward flustered nervous anxious',
calm:'content calm tranquil zen grateful relieved satisfied relaxed empathetic compassionate',
};
const groupSets=Object.fromEntries(Object.entries(groups).map(([a,b])=>[a,new Set(b.split(' '))]));
function partOf(n,k){return groupSets[k].has(n)}
const desc={idle:'Friendly default face with wide blue eyes and a soft smile.',listening:'Bright focused eyes with animated sound-wave indicators.',thinking:'Thoughtful eyes looking aside with a small pondering mark.',speaking:'Animated open mouth while EVA replies.',happy:'Bright smiling eyes and an upbeat expression.',sleepy:'Heavy violet eyelids and a glowing floating Z.',laughing:'Joyfully closed crescent eyes, rosy cheeks and a laughing mouth.',namaste:'Respectful closed eyes and a gentle welcoming smile.',diwali:'Festive stars and warm golden sparkle accents.',glitch:'Digital distortion effect and mismatched eye accents.',dead:'Cartoon X-shaped eyes and a flat mouth.',loading:'Processing spinner between the eyes.',love:'Heart-shaped pupils and a warm smile.',scared:'Wide fearful pupils with a trembling mouth.'};
function look(n,i){
 let C={mood:'neutral',eye:'open',open:1.0,pupil:1,look:0,brow:'arch',mouth:'smile',accent:'#37dcff',icon:'',cheek:'',tear:false,sparks:false,waves:false};
 if(partOf(n,'happy'))Object.assign(C,{mood:'happy',mouth:'grin',open:.96,cheek:'pink'});
 if(partOf(n,'sad'))Object.assign(C,{mood:'sad',brow:'sad',mouth:'sad',open:.78,look:-3});
 if(partOf(n,'angry'))Object.assign(C,{mood:'angry',brow:'angry',mouth:'frown',open:.72,accent:'#36dcff'});
 if(partOf(n,'wide'))Object.assign(C,{mood:'wide',eye:'open',open:1.12,pupil:.72,brow:'high',mouth:'oh'});
 if(partOf(n,'narrow'))Object.assign(C,{mood:'narrow',open:.68,brow:'squint',mouth:'flat'});
 if(partOf(n,'sleep'))Object.assign(C,{mood:'sleep',eye:'half',open:.66,brow:'soft',mouth:'flat',accent:'#5bd9ff'});
 if(partOf(n,'love'))Object.assign(C,{mood:'love',pupil:1,eye:'heart',mouth:'grin',cheek:'pink',accent:'#62dfff'});
 if(partOf(n,'think'))Object.assign(C,{mood:'think',look:9,open:.9,mouth:'tiny',brow:'quizzical',icon:'?'});
 if(partOf(n,'shy'))Object.assign(C,{mood:'shy',look:-5,mouth:'tiny',cheek:'pink',brow:'sad'});
 if(partOf(n,'calm'))Object.assign(C,{brow:'soft',mouth:'smile',open:.85});
 if(n==='idle')Object.assign(C,{eye:'open',mouth:'smile',brow:'arch',open:1.0});
 if(n==='listening')Object.assign(C,{eye:'open',open:1.07,mouth:'oh',waves:true,look:0});
 if(n==='speaking')Object.assign(C,{eye:'open',mouth:'speaking',open:1.03});
 if(n==='laughing'||n==='ecstatic'||n==='delighted'||n==='happy')Object.assign(C,{eye:'crescent',mouth:'laugh',cheek:'pink',sparks:true});
 if(n==='sleepy'||n==='exhausted')Object.assign(C,{eye:'half',mouth:'flat',icon:'Z',accent:'#69bbff'});
 if(n==='sleepy_happy')Object.assign(C,{eye:'half',mouth:'smile',icon:'Z'});
 if(n==='dead')Object.assign(C,{eye:'dead',brow:'none',mouth:'flat',accent:'#ef5b77'});
 if(n==='glitch')Object.assign(C,{eye:'glitch',mouth:'flat',icon:'⚡'});
 if(n==='namaste')Object.assign(C,{eye:'closed',mouth:'smile',brow:'soft'});
 if(n==='diwali')Object.assign(C,{eye:'open',mouth:'grin',sparks:true,icon:'✦'});
 if(n==='woozy')Object.assign(C,{eye:'swirl',brow:'quizzical',mouth:'wavy'});
 if(n==='shocked')Object.assign(C,{eye:'open',mouth:'oh',brow:'high',icon:'!'});
 if(n==='starstruck')Object.assign(C,{eye:'star',mouth:'laugh',sparks:true});
 if(n==='embarrassed'||n==='flustered')Object.assign(C,{cheek:'pink',look:-5,eye:'open',mouth:'tiny'});
 if(n==='smitten'||n==='flirty')Object.assign(C,{eye:'heart',mouth:'smile',cheek:'pink'});
 if(n==='scared'||n==='haunted')Object.assign(C,{pupil:.45,mouth:'oh',waves:true});
 if(n==='confused')Object.assign(C,{brow:'quizzical',mouth:'wavy',icon:'??'});
 if(n==='nervous'||n==='anxious')Object.assign(C,{mouth:'wavy',cheek:'pink'});
 if(n==='curious'||n==='intrigued')Object.assign(C,{brow:'quizzical',look:11,mouth:'oh',icon:'?'});
 if(n==='loading')Object.assign(C,{icon:'loading',mouth:'flat',look:0});
 if(n==='proud_tears'||n==='touched'||n==='heartbroken'||n==='sad'||n==='melancholy') C.tear=true;
 if(n==='proud_tears')Object.assign(C,{mouth:'grin',brow:'sad'});
 if(n==='determined'||n==='focused')Object.assign(C,{brow:'angry',mouth:'flat'});
 if(n==='guilty'||n==='apologetic')Object.assign(C,{brow:'sad',mouth:'tiny',look:-7});
 if(n==='mischievous'||n==='smug'||n==='snarky')Object.assign(C,{eye:'wink',mouth:'smirk',brow:'squint'});
 if(n==='playful')Object.assign(C,{eye:'wink',mouth:'grin',cheek:'pink'});
 if(n==='bored')Object.assign(C,{eye:'half',mouth:'flat'});
 if(n==='grumpy'||n==='annoyed')Object.assign(C,{eye:'half',mouth:'frown',brow:'angry'});
 if(n==='inspired'||n==='divine')Object.assign(C,{sparks:true,icon:'✦',mouth:'grin'});
 if(n==='victory'||n==='victorious')Object.assign(C,{sparks:true,mouth:'laugh',icon:'★'});
 if(n==='meltdown')Object.assign(C,{eye:'squint',mouth:'wavy',accent:'#ff9d5d',icon:'!!'});
 if(n==='skeptical'||n==='suspicious')Object.assign(C,{eye:'half',brow:'quizzical',mouth:'flat',look:7});
 if(n==='zen')Object.assign(C,{eye:'closed',mouth:'smile',brow:'soft'});
 if(n==='calm'||n==='tranquil')Object.assign(C,{eye:'half',mouth:'smile',brow:'soft'});
 if(n==='jealous')Object.assign(C,{eye:'half',brow:'angry',mouth:'frown',look:6});
 if(n==='flirty')Object.assign(C,{eye:'wink',cheek:'pink'});
 if(n==='pleading')Object.assign(C,{eye:'open',open:1.12,pupil:1.16,brow:'sad',mouth:'tiny'});
 if(n==='offended')Object.assign(C,{eye:'half',mouth:'frown',brow:'angry'});
 if(n==='amazed')Object.assign(C,{sparks:true,mouth:'oh'});
 if(n==='happy'||n==='laughing')Object.assign(C,{accent:'#38e9ff'});
 if(n==='content'||n==='satisfied'||n==='relieved')Object.assign(C,{eye:'half',mouth:'smile'});
 if(n==='yearning')Object.assign(C,{brow:'sad',mouth:'tiny',look:6,cheek:'pink'});
 // Tiny consistent personality differences for states sharing an emotion family
 if(i%7===0 && !['dead','glitch','sleepy'].includes(n))C.sparks=C.sparks||partOf(n,'happy');
 return C;
}
function eyebrow(i,c){let x=i===0?122:258,y=70;let path;
 switch(c.brow){
 case 'none':return '';
 case 'high':path=`M${x-29} ${y-8} Q${x} ${y-45} ${x+29} ${y-8}`;break;
 case 'angry':path=`M${x-30} ${y+(i===0?-8:12)} Q${x} ${y-7} ${x+30} ${y+(i===0?12:-8)}`;break;
 case 'sad':path=`M${x-30} ${y+(i===0?14:-12)} Q${x} ${y-18} ${x+30} ${y+(i===0?-10:14)}`;break;
 case 'squint':path=`M${x-30} ${y+7} Q${x} ${y-9} ${x+30} ${y+1}`;break;
 case 'quizzical':path=i===0?`M${x-29} ${y+4} Q${x} ${y-25} ${x+30} ${y-3}`:`M${x-28} ${y-1} Q${x} ${y-8} ${x+29} ${y+8}`;break;
 case 'soft':path=`M${x-26} ${y} Q${x} ${y-18} ${x+26} ${y-3}`;break;
 default:path=`M${x-28} ${y+5} Q${x} ${y-29} ${x+28} ${y+2}`;
 }
 return `<path d="${path}" fill="none" stroke="${c.accent}" stroke-width="5.5" stroke-linecap="round" opacity=".96" filter="url(#sh)"/>`;
}
function eye(i,c){let x=i===0?122:258,y=122,rx=36,ry=43*c.open,z=c.look,shade=c.eye;
 if(shade==='dead')return `<g stroke="#ff476d" stroke-width="9" stroke-linecap="round" filter="url(#sh)"><path d="M${x-21} ${y-21}L${x+21} ${y+21}M${x+21} ${y-21}L${x-21} ${y+21}"/></g>`;
 if(shade==='closed'||shade==='crescent')return `<path d="M${x-35} ${y+5} Q${x} ${y-(shade==='crescent'?46:11)} ${x+35} ${y+5}" stroke="${c.accent}" stroke-width="${shade==='crescent'?15:9}" stroke-linecap="round" fill="none" filter="url(#sh)"/>`;
 if(shade==='swirl')return `<path d="M${x-28} ${y} a28 28 0 1 1 54 0 a18 18 0 1 1 -35 0 a8 8 0 1 1 16 0" fill="none" stroke="${c.accent}" stroke-width="7" filter="url(#sh)"/>`;
 if(shade==='glitch')return `<path d="M${x-35} ${y-30}h70v25h-70zM${x-34} ${y+10}h70v20h-70z" fill="#21d9f4" filter="url(#sh)" opacity=".85"/><path d="M${x-28} ${y+1}h60" stroke="#ef4fff" stroke-width="6"/>`;
 let lid=shade==='half'||shade==='wink'||shade==='squint';if(shade==='wink'&&i===1)return `<path d="M${x-30} ${y+8}Q${x} ${y-15} ${x+30} ${y+8}" fill="none" stroke="${c.accent}" stroke-width="10" stroke-linecap="round" filter="url(#sh)"/>`;
 let iriscx=x+z,iriscy=y+4,pr=19*c.pupil,iris='';
 if(shade==='heart')iris=`<path d="M${iriscx} ${iriscy+14} C${iriscx-39} ${iriscy-10} ${iriscx-13} ${iriscy-23} ${iriscx} ${iriscy-10} C${iriscx+13} ${iriscy-23} ${iriscx+39} ${iriscy-10} ${iriscx} ${iriscy+14}Z" fill="#0e1430"/>`;
 else if(shade==='star')iris=`<path d="${starPath(iriscx,iriscy,22,10,5)}" fill="#081321"/>`;
 else iris=`<ellipse cx="${iriscx}" cy="${iriscy}" rx="${pr*.86}" ry="${pr*1.2}" fill="#06101b"/>`;
 return `<g class="eye" filter="url(#sh)"><ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="url(#eyeG)"/><ellipse cx="${x}" cy="${y+5}" rx="${rx-7}" ry="${Math.max(10,ry-9)}" fill="none" stroke="#b4fcff" stroke-opacity=".6" stroke-width="2"/>${iris}<circle cx="${iriscx-11}" cy="${iriscy-18}" r="7.2" fill="#fff"/><circle cx="${iriscx+10}" cy="${iriscy-5}" r="2.6" fill="#edffff"/></g>${lid?`<path d="M${x-38} ${y-10}Q${x} ${y-37} ${x+38} ${y-10}V${y-53}H${x-38}Z" fill="#03070b"/><path d="M${x-37} ${y-10}Q${x} ${y-32} ${x+37} ${y-10}" fill="none" stroke="#606afa" stroke-width="3"/>`:''}`;
}
function starPath(x,y,outer,inner,n){let p=[];for(let i=0;i<n*2;i++){let a=-Math.PI/2+i*Math.PI/n,r=i%2?inner:outer;p.push((i?'L':'M')+(x+Math.cos(a)*r).toFixed(1)+' '+(y+Math.sin(a)*r).toFixed(1))}return p.join(' ')+'Z'}
function mouth(c){let y=185,colors=c.mood==='angry'?'#23deff':'#27e6fc';let p='',fill='none',extras='';switch(c.mouth){
case 'grin':p='M157 180 Q190 222 223 180 Q190 197 157 180Z';fill='#0de4fd';extras='<path d="M169 192 Q190 216 212 192" stroke="#ff83e9" stroke-width="9" fill="none"/>';break;
case 'laugh':p='M156 174 Q190 172 224 174 Q228 229 190 232 Q153 227 156 174Z';fill='#05081c';extras='<ellipse cx="190" cy="214" rx="24" ry="11" fill="#ff6bdc"/><path d="M164 178H216" stroke="#78f2ff" stroke-width="3"/>';break;
case 'speaking':p='M163 177 Q190 158 217 177 Q229 208 190 220 Q151 207 163 177Z';fill='#061625';extras='<ellipse cx="190" cy="209" rx="17" ry="6" fill="#f585dc"/>';break;
case 'oh':p='M190 173 C164 173 164 212 190 215 C215 213 215 174 190 173Z';fill='#081929';break;
case 'sad':p='M165 206 Q190 172 215 206';break;
case 'frown':p='M168 201 Q190 181 212 201';break;
case 'flat':p='M175 195 Q190 193 205 195';break;
case 'tiny':p='M181 193 Q190 190 199 193';break;
case 'smirk':p='M169 190 Q189 208 215 181';break;
case 'wavy':p='M166 193 Q178 176 190 193 Q202 208 214 193';break;
default:p='M164 185 Q190 207 216 185';}
return `<g class="${c.mouth==='speaking'?'speakingMouth':''}" stroke="${colors}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="${fill}" filter="url(#sh)"><path d="${p}"/></g>${extras}`;
}
function extra(c,n){let a='';if(c.cheek==='pink')for(let x of [75,302])a+=`<g stroke="#ff7cdf" stroke-width="4" stroke-linecap="round" filter="url(#sh)"><path d="M${x-8} 169l-5 9M${x+2} 168l-5 9M${x+12} 169l-5 9"/></g>`;
 if(c.tear)a+='<path d="M292 151 Q275 172 286 181 Q302 183 292 151Z" fill="#68daff" filter="url(#sh)"/>';
 if(c.sparks)a+=`<g stroke="#ffd05b" fill="none" stroke-width="3" stroke-linecap="round" filter="url(#sh)"><path d="M61 114v-14m-7 7h14M324 114v-14m-7 7h14"/><path d="M59 143l-8 6m270-6l8 6"/></g>`;
 if(c.waves)a+=`<g class="soundWave" fill="none" stroke="${c.accent}" stroke-width="4" stroke-linecap="round" filter="url(#sh)"><path d="M57 99Q40 121 57 143M47 85Q26 121 47 155M323 99Q340 121 323 143M333 85Q354 121 333 155"/></g>`;
 if(c.icon==='loading')a+='<g stroke="#3ceaff" stroke-width="5" stroke-linecap="round" fill="none" filter="url(#sh)"><circle cx="190" cy="184" r="11" stroke-dasharray="8 7"/></g>';
 else if(c.icon)a+=`<text x="335" y="93" text-anchor="middle" font-family="system-ui,sans-serif" font-size="${c.icon.length>1?24:33}" font-weight="800" fill="${n==='sleepy'?'#8b83ff':'#59e8ff'}" filter="url(#sh)">${c.icon==='Z'?'Zᶻ':c.icon}</text>`;
 return a;}
function svg(n,idx,main=false){let c=look(n,idx);
 return `<svg class="robot face-subtle" viewBox="0 0 380 255" role="img" aria-label="EVA face: ${n.replaceAll('_',' ')}" xmlns="http://www.w3.org/2000/svg"><defs>
 <radialGradient id="eyeG"><stop stop-color="#b3ffff"/><stop offset=".45" stop-color="#66eefe"/><stop offset=".85" stop-color="#18b5ea"/><stop offset="1" stop-color="#06388b"/></radialGradient><filter id="sh" x="-75%" y="-75%" width="250%" height="250%"><feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="a"/><feMerge><feMergeNode in="a"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
 <g>${eyebrow(0,c)}${eyebrow(1,c)}${eye(0,c)}${eye(1,c)}${mouth(c)}${extra(c,n)}</g></svg>`.replaceAll('url(#sh)','url(#sh)');
}

function title(n){return n.replaceAll('_',' ').replace(/\b\w/g,ch=>ch.toUpperCase())}
window.EvaFaceArt=Object.freeze({names:Object.freeze([...NAMES]),svg:(name)=>{const i=NAMES.indexOf(name);return svg(i<0?'idle':name,Math.max(0,i),true)},title});
})();
