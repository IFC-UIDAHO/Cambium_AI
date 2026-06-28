// Free, browser-built-in voice. Graceful no-ops where unsupported. Swap for ElevenLabs for a custom voice.
export function speak(text, { rate = 1, pitch = 1.25 } = {}) {
  try {
    const ss = window.speechSynthesis; if (!ss) return
    ss.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.rate = rate; u.pitch = pitch   // a slightly high pitch reads "little cute alien"
    ss.speak(u)
  } catch {}
}
export function listen(onResult) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) { onResult(null, 'unsupported'); return null }
  const r = new SR(); r.lang = 'en-US'; r.interimResults = false; r.maxAlternatives = 1
  r.onresult = (e) => onResult(e.results[0][0].transcript)
  r.onerror = () => onResult(null, 'error')
  r.start(); return r
}
