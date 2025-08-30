document.addEventListener('DOMContentLoaded', async () => {
  const body=document.querySelector('.chat-body'), form=document.querySelector('.entry'), input=form.querySelector('input');
  let last=null, CASE_ID=null;

  const add=(h,w='ai')=>{const d=document.createElement('div');d.className='msg '+w;d.innerHTML=h;body.appendChild(d);body.scrollTop=body.scrollHeight;};

  add("I’ll only ask what’s missing — no repeats.");
  try{const r=await fetch('/api/case/new',{method:'POST'});const d=await r.json();if(d.ok)CASE_ID=d.case_id;}catch(_){}

  form.addEventListener('submit', async e=>{
    e.preventDefault(); const text=input.value.trim(); if(!text)return;
    add(text,'user'); input.value='';
    try{
      const res=await fetch('/api/chat?case_id='+(CASE_ID||''),{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({message:text})
      });
      const data=await res.json();
      if(data.reply) add(data.reply,'ai');
    }catch(_){ add('Network hiccup.','ai'); }
  });
});
