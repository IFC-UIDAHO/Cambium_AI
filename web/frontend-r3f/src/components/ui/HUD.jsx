import { useEffect } from 'react'
import { useScene } from '../../state/sceneStore.js'
import { probe, enter, decide, restart } from '../../lib/bridge.js'
import { listen, speak } from '../../lib/voice.js'

const EX = ['Write an NSF proposal on post-wildfire forest recovery', 'Design a camera-trap study for a wildlife corridor', 'Verify the results in this analysis', 'Write the quarterly progress report']
const gold = '#e7c878'

export default function HUD() {
  const S = useScene()
  useEffect(() => { probe() }, [])
  const go = () => { const v = (document.getElementById('req')?.value || EX[0]).trim(); enter(v) }
  const mic = () => listen((text, err) => { if (text) { document.getElementById('req').value = text; setTimeout(go, 300) } })

  return (
    <div style={{ position:'fixed', inset:0, zIndex:5, pointerEvents:'none', userSelect:'none', fontFamily:'Inter,system-ui,sans-serif', color:'#f4f7f2' }}>

      {/* GREETER (alien speech bubble + input) */}
      {S.act === 'greeter' && (
        <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'flex-end', paddingBottom:'10vh', textAlign:'center', pointerEvents:'auto' }}>
          <div style={{ maxWidth:560, marginBottom:18, padding:'16px 22px', borderRadius:18, border:`1px solid ${gold}`, background:'rgba(6,24,16,.7)', backdropFilter:'blur(10px)', fontSize:17, lineHeight:1.5, color:'#f1e6c9' }}>
            👽 {S.alienSays || 'Welcome to the Cambium Institute!'}
          </div>
          <div style={{ width:'min(660px,92vw)' }}>
            <div style={{ display:'flex', border:`1px solid rgba(231,200,120,.55)`, borderRadius:16, overflow:'hidden', background:'rgba(4,16,10,.6)', backdropFilter:'blur(10px)', boxShadow:'0 0 60px rgba(22,192,121,.18)' }}>
              <button onClick={mic} title="speak" style={{ border:'none', cursor:'pointer', background:'transparent', color:gold, fontSize:18, padding:'0 14px' }}>🎤</button>
              <input id="req" placeholder="Tell the aliens what you need… (or tap the mic)" onKeyDown={e => e.key==='Enter' && go()}
                style={{ flex:1, background:'transparent', border:'none', outline:'none', color:'#f4f7f2', fontSize:16, padding:'16px 12px', fontFamily:'inherit' }} />
              <button onClick={go} style={{ border:'none', cursor:'pointer', fontWeight:800, fontSize:14, padding:'0 24px', background:'linear-gradient(180deg,#e7c878,#caa24e)', color:'#1c3326' }}>ENTER ▸</button>
            </div>
            <div style={{ marginTop:12, display:'flex', gap:8, flexWrap:'wrap', justifyContent:'center' }}>
              {EX.map(x => <span key={x} onClick={() => document.getElementById('req').value = x} style={{ cursor:'pointer', fontSize:12, color:'#9fc2ac', border:'1px solid #1f4d3b', borderRadius:20, padding:'7px 13px' }}>{x}</span>)}
            </div>
            <div style={{ marginTop:10, fontSize:11, color: S.mode==='live'?'#16c079':gold }}>{S.mode==='live'?'● live engine':S.mode==='offline'?'● local preview':'● connected (simulation)'}</div>
          </div>
        </div>
      )}

      {/* CAMPUS top bar + ticker */}
      {S.act === 'campus' && <>
        <div style={{ position:'absolute', top:0, left:0, right:0, display:'flex', gap:14, alignItems:'center', padding:'14px 20px', pointerEvents:'auto' }}>
          <div style={{ fontWeight:800, color:gold, letterSpacing:1 }}>⬢ CAMBIUM</div>
          <div style={{ flex:1, color:'#9fc2ac', fontSize:13, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{S.request}</div>
          <div style={{ fontSize:11, color:'#b7f36a', border:'1px solid #1f4d3b', borderRadius:20, padding:'5px 12px' }}>{S.phaseLabel || 'Phase 0'}</div>
          <button onClick={restart} style={{ cursor:'pointer', fontSize:11, color:'#9fc2ac', border:'1px solid #1f4d3b', borderRadius:8, padding:'6px 11px', background:'transparent' }}>↺ new</button>
        </div>
        <div style={{ position:'absolute', right:18, top:64, bottom:18, width:300, display:'flex', flexDirection:'column', gap:9, overflow:'auto', pointerEvents:'auto' }}>
          {S.ticker.map((t, i) => <div key={i} style={{ fontSize:12, lineHeight:1.45, padding:'10px 12px', borderRadius:12, border:'1px solid #1f4d3b', background:'rgba(6,24,16,.66)', backdropFilter:'blur(8px)' }}>
            <div style={{ color: t.g ? '#e58a8a' : gold, fontWeight:700, fontSize:11 }}>{t.who}</div>{t.fd && <div style={{ color:'#d7e6db', marginTop:3 }}>{t.fd}</div>}</div>)}
        </div>
      </>}

      {/* GATE — the alien asks "yes, bro?" */}
      {S.gate && (
        <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', background:'radial-gradient(60% 60% at 50% 45%,rgba(4,16,10,.35),rgba(2,8,5,.8))', backdropFilter:'blur(3px)', pointerEvents:'auto' }}>
          <div style={{ width:'min(560px,92vw)', border:`1px solid ${gold}`, borderRadius:20, overflow:'hidden', background:'linear-gradient(180deg,rgba(22,58,42,.97),rgba(7,26,18,.98))', boxShadow:'0 30px 100px rgba(0,0,0,.65),0 0 80px rgba(231,200,120,.3)' }}>
            <div style={{ padding:'16px 24px', borderBottom:'1px solid rgba(231,200,120,.3)', color:gold, fontWeight:800, fontSize:13 }}>👽 ⛩ {S.gate.id} — the alien needs your call</div>
            <div style={{ padding:'20px 24px' }}><div style={{ fontSize:19, fontWeight:600, marginBottom:8 }}>“{S.gate.q}”</div><div style={{ fontSize:12.5, color:'#9fc2ac' }}>{S.gate.d}</div></div>
            <div style={{ display:'flex', gap:11, padding:'0 24px 22px', flexWrap:'wrap' }}>
              {[['APPROVE',`linear-gradient(180deg,#e7c878,#caa24e)`,'#1c3326',''],['REVISE','transparent','#f4f7f2','#9fc2ac'],['REJECT','transparent','#e58a8a','#7a3b3b']].map(([d,bg,col,bd]) =>
                <button key={d} onClick={() => { speak(d==='APPROVE'?'On it, bro!':d==='REVISE'?'Okay, we will fix it.':'Understood, stopping.'); decide(d) }} style={{ cursor:'pointer', fontWeight:800, fontSize:13, padding:'12px 24px', borderRadius:12, background:bg, color:col, border:bd?`1px solid ${bd}`:'1px solid transparent' }}>{d}</button>)}
            </div>
          </div>
        </div>
      )}

      {/* DONE */}
      {S.act === 'done' && S.summary && (
        <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', textAlign:'center', padding:24, pointerEvents:'auto' }}>
          <div style={{ fontSize:'clamp(28px,5vw,46px)', fontWeight:800, background:'linear-gradient(180deg,#fbeec2,#caa24e)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent' }}>{S.summary.rejected ? 'Stopped at your gate.' : (S.mode==='offline'?"That's the plan.":'Delivered.')}</div>
          <div style={{ marginTop:14, width:'min(600px,92vw)', border:'1px solid #1f4d3b', borderRadius:16, background:'rgba(8,30,21,.5)', backdropFilter:'blur(8px)', padding:'18px 20px', textAlign:'left' }}>
            {[['Request', S.summary.task?.slice(0,44)], ['Track', S.summary.kind], ['Councils mobilized', (S.summary.councils)+' of 11'], ['Gates', (S.summary.gates||[]).map(g=>g.gate+': '+g.decision).join(' · ')||'—']].map(([k,v]) =>
              <div key={k} style={{ display:'flex', justifyContent:'space-between', gap:14, padding:'8px 0', borderBottom:'1px solid rgba(31,77,59,.5)', fontSize:13 }}><span style={{ color:'#9fc2ac' }}>{k}</span><b style={{ color:'#b7f36a' }}>{v}</b></div>)}
          </div>
          <button onClick={restart} style={{ marginTop:18, border:'none', cursor:'pointer', fontWeight:800, fontSize:14, padding:'13px 26px', borderRadius:14, background:'linear-gradient(180deg,#e7c878,#caa24e)', color:'#1c3326' }}>↺ Run another</button>
        </div>
      )}
    </div>
  )
}
