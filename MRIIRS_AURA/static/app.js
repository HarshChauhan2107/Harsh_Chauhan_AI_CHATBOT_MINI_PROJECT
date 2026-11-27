const form=document.getElementById('chatForm'), input=document.getElementById('messageInput'), messages=document.getElementById('messages'), sendBtn=form.querySelector('.send-btn'), charCount=document.getElementById('charCount'), suggestionsWrap=document.getElementById('suggestionsWrap'), toast=document.getElementById('toast');
let busy=false;
function timeNow(){return new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}).toUpperCase()}
function scrollBottom(){messages.scrollTop=messages.scrollHeight}
function toastMsg(msg){toast.textContent=msg;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),2300)}
function appendTextWithLinks(node,text){
 const urlRegex=/(https?:\/\/[^\s]+)/g;let last=0;
 text.replace(urlRegex,(raw,index)=>{node.append(document.createTextNode(text.slice(last,index)));const clean=raw.replace(/[.,)]$/,'');const a=document.createElement('a');a.href=clean;a.textContent=clean;a.target='_blank';a.rel='noopener noreferrer';node.append(a);if(clean.length<raw.length)node.append(document.createTextNode(raw.slice(clean.length)));last=index+raw.length;return raw;});
 node.append(document.createTextNode(text.slice(last)));
}
function addMessage(text,who,meta=null){
 const row=document.createElement('div');row.className=`message-row ${who==='user'?'user-row':'bot-row'}`;
 const avatar=document.createElement('div');avatar.className='msg-avatar';avatar.textContent=who==='user'?'YOU':'✦';
 const content=document.createElement('div');content.className='message-content';
 const bubble=document.createElement('div');bubble.className=`message ${who==='user'?'user-message':'bot-message'}`;
 if(who==='bot')appendTextWithLinks(bubble,text);else bubble.textContent=text;
 content.append(bubble);
 const stamp=document.createElement('div');stamp.className='msg-time';stamp.textContent=`${timeNow()} · ${who==='user'?'YOU':'MRIIRS AURA'}`;content.append(stamp);
 if(meta){
  const line=document.createElement('div');line.className='answer-meta';
  const match=document.createElement('span');match.className='confidence';match.textContent=meta.match==='strong'?'● STRONG TOPIC MATCH':meta.match==='relevant'?'● RELEVANT MATCH':'● NOT IN KNOWLEDGE BASE';
  const cat=document.createElement('span');cat.textContent=meta.category||'General';line.append(match,cat);content.append(line);
  if(meta.source_url){const src=document.createElement('div');src.className='answer-source';src.append(document.createTextNode('Source: '));const a=document.createElement('a');a.href=meta.source_url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=meta.source_name||'Official MRIIRS page';src.append(a);if(meta.last_verified){const updated=document.createElement('span');updated.className='answer-updated';updated.textContent=`· reviewed ${meta.last_verified}`;src.append(updated)}content.append(src)}
  if(meta.match!=='none'){
   const fb=document.createElement('div');fb.className='feedback';
   const yes=document.createElement('button');yes.type='button';yes.textContent='👍 Helpful';yes.addEventListener('click',()=>sendFeedback('up'));
   const no=document.createElement('button');no.type='button';no.textContent='👎 Not helpful';no.addEventListener('click',()=>sendFeedback('down'));
   fb.append(yes,no);content.append(fb);
  }
 }
 row.append(avatar,content);messages.append(row);scrollBottom();
}
function showTyping(){const row=document.createElement('div');row.id='typingRow';row.className='message-row bot-row';row.innerHTML='<div class="msg-avatar">✦</div><div class="message-content"><div class="message bot-message typing"><span></span><span></span><span></span></div></div>';messages.append(row);scrollBottom()}
async function sendFeedback(vote){try{await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vote})});toastMsg('Thanks for your feedback!')}catch(e){toastMsg('Feedback could not be sent.')}}
function addSuggestions(items){if(!items||!items.length)return;const wrap=document.createElement('div');wrap.className='message-row bot-row';const spacer=document.createElement('div');spacer.className='msg-avatar';spacer.style.visibility='hidden';const list=document.createElement('div');list.className='message-content';const label=document.createElement('div');label.className='answer-source';label.textContent='Related questions';list.append(label);items.forEach(q=>{const b=document.createElement('button');b.className='feedback';b.style.display='inline-block';b.style.margin='5px 5px 0 0';b.style.padding='7px 9px';b.textContent=q;b.addEventListener('click',()=>ask(q));list.append(b)});wrap.append(spacer,list);messages.append(wrap);scrollBottom()}
async function ask(question){if(busy)return;const q=question.trim();if(!q)return;busy=true;sendBtn.disabled=true;addMessage(q,'user');input.value='';charCount.textContent='0/500';suggestionsWrap.style.display='none';showTyping();
 try{const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:q})});const data=await res.json();document.getElementById('typingRow')?.remove();if(!res.ok)throw new Error(data.error||'Request failed');addMessage(data.answer,'bot',data);addSuggestions(data.suggestions)}catch(err){document.getElementById('typingRow')?.remove();addMessage('I could not connect to the AURA service. Check that the Flask server is running, then refresh this page.','bot');}finally{busy=false;sendBtn.disabled=false;input.focus()}}
form.addEventListener('submit',e=>{e.preventDefault();ask(input.value)});
input.addEventListener('input',()=>charCount.textContent=`${input.value.length}/500`);
document.querySelectorAll('.suggestion').forEach(b=>b.addEventListener('click',()=>ask(b.dataset.question)));
document.getElementById('clearChat').addEventListener('click',resetChat);
document.getElementById('newChat').addEventListener('click',resetChat);
function resetChat(){messages.innerHTML='';addMessage('Hello! I am MRIIRS AURA — Artificial University Response Assistant. Ask a specific question about admissions, programmes, fees, academics, examinations, campus facilities, placements or student support. I will show the source for each matched answer and will not guess when information is missing.','bot');suggestionsWrap.style.display='';toastMsg('Conversation reset.')}
document.getElementById('topicNav').addEventListener('click',e=>{const btn=e.target.closest('.topic');if(!btn)return;document.querySelectorAll('.topic').forEach(x=>x.classList.remove('active'));btn.classList.add('active');const topic=btn.dataset.topic;if(topic==='All'){resetChat();return}ask(`Give me the main information about ${topic} at MRIIRS`) });
document.getElementById('menuBtn').addEventListener('click',()=>document.getElementById('sidebar').classList.add('open'));
document.getElementById('closeSidebar').addEventListener('click',()=>document.getElementById('sidebar').classList.remove('open'));
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.getElementById('sidebar').classList.remove('open')});
fetch('/api/health').then(r=>r.json()).then(d=>console.info(`${d.brand} (${d.full_form}) ready: ${d.faq_count} curated FAQs`)).catch(()=>{});
