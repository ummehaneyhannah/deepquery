import { useState } from 'react'

const API_URL = 'https://deepquery-backend.onrender.com'

function App() {
  const [question, setQuestion] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!question.trim() || status === 'loading') return

    setStatus('loading')
    setErrorMsg('')
    setResult(null)

    try {
      const res = await fetch(API_URL + '/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Request failed (' + res.status + ')')
      }

      const data = await res.json()
      setResult(data)
      setStatus('done')
    } catch (err) {
      setErrorMsg(err.message || 'Something went wrong reaching the agent.')
      setStatus('error')
    }
  }

  return (
    <div className="min-h-screen bg-[#12181B] text-[#EFE9DD] flex flex-col">
      {/* Wire header */}
      <header className="border-b border-[#EFE9DD]/15 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span
            className={
              'h-2.5 w-2.5 rounded-full ' +
              (status === 'loading' ? 'bg-[#A8453A] animate-pulse' : 'bg-[#C98A2C]')
            }
          />
         <div className="flex flex-col leading-tight">
            <h1
              className="text-xl tracking-wide"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              DEEPQUERY
            </h1>
            <span
              className="text-[10px] uppercase tracking-widest text-[#EFE9DD]/40"
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              Research Wire
            </span>
          </div>
        </div>
        <span
          className="text-xs uppercase tracking-widest text-[#EFE9DD]/50"
          style={{ fontFamily: 'var(--font-mono)' }}
        >
          {status === 'loading' ? 'transmitting' : 'standing by'}
        </span>
      </header>

      {/* Main column */}
      <main className="flex-1 max-w-2xl w-full mx-auto px-6 py-10 flex flex-col gap-8">
        {/* Input */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label
            className="text-xs uppercase tracking-widest text-[#EFE9DD]/50"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            Submit inquiry
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What do you want the wire to investigate?"
            rows={3}
            className="w-full bg-transparent border border-[#EFE9DD]/25 rounded px-4 py-3 text-[#EFE9DD] placeholder-[#EFE9DD]/30 focus:outline-none focus:border-[#C98A2C] resize-none"
            style={{ fontFamily: 'var(--font-body)' }}
          />
          <button
            type="submit"
            disabled={status === 'loading' || !question.trim()}
            className="self-end px-5 py-2 rounded bg-[#C98A2C] text-[#12181B] font-semibold tracking-wide disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#dba24a] transition-colors"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            {status === 'loading' ? 'DISPATCHING...' : 'SEND'}
          </button>
        </form>

        {/* Loading ticker */}
        {status === 'loading' && (
          <div
            className="border border-[#EFE9DD]/15 rounded px-4 py-3 text-sm text-[#EFE9DD]/60 animate-pulse"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            Agent is searching, reading sources, and cross-checking facts...
          </div>
        )}

        {/* Error */}
        {status === 'error' && (
          <div
            className="border border-[#A8453A]/50 bg-[#A8453A]/10 rounded px-4 py-3 text-sm text-[#EFE9DD]"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            Error: {errorMsg}
          </div>
        )}

        {/* Dispatch result */}
        {status === 'done' && result && (
          <article className="bg-[#EFE9DD] text-[#12181B] rounded-lg p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-[#12181B]/15 pb-3">
              <span
                className="text-xs uppercase tracking-widest text-[#12181B]/50"
                style={{ fontFamily: 'var(--font-mono)' }}
              >
                Dispatch - {result.stopped_reason === 'completed' ? 'filed' : 'partial'}
              </span>
              <span
                className="text-xs text-[#12181B]/50"
                style={{ fontFamily: 'var(--font-mono)' }}
              >
                {result.iterations_used} step{result.iterations_used === 1 ? '' : 's'}
              </span>
            </div>

            <p
              className="text-[1.05rem] leading-relaxed whitespace-pre-wrap"
              style={{ fontFamily: 'var(--font-body)' }}
            >
              {result.answer}
            </p>

            {result.sources_fetched && result.sources_fetched.length > 0 && (
              <div className="border-t border-[#12181B]/15 pt-3">
                <span
                  className="text-xs uppercase tracking-widest text-[#12181B]/50"
                  style={{ fontFamily: 'var(--font-mono)' }}
                >
                  Sources
                </span>
                <ol
                  className="mt-2 flex flex-col gap-1 text-sm text-[#12181B]/70"
                  style={{ fontFamily: 'var(--font-mono)' }}
                >
                  {result.sources_fetched.map((url, i) => (
                    <li key={url} className="truncate">
                      [{i + 1}]{' '}
                      <a
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                        className="underline hover:text-[#C98A2C]"
                      >
                        {url}
                      </a>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </article>
        )}
      </main>
    </div>
  )
}

export default App
