import { useEffect, useRef, useState } from 'react'

const API_URL = 'https://deepquery-backend.onrender.com'

function App() {
  const [question, setQuestion] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | error
  const [errorMsg, setErrorMsg] = useState('')
  const [messages, setMessages] = useState([]) // { role: 'user'|'assistant', text, sources? }
  const [conversationId, setConversationId] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!question.trim() || status === 'loading') return

    const userText = question.trim()
    setMessages((prev) => [...prev, { role: 'user', text: userText }])
    setQuestion('')
    setStatus('loading')
    setErrorMsg('')

    try {
      const res = await fetch(API_URL + '/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userText,
          conversation_id: conversationId,
        }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Request failed (' + res.status + ')')
      }

      const data = await res.json()
      setConversationId(data.conversation_id)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: data.answer, sources: data.sources_fetched || [] },
      ])
      setStatus('idle')
    } catch (err) {
      setErrorMsg(err.message || 'Something went wrong reaching the agent.')
      setStatus('error')
    }
  }

  function startNewChat() {
    setMessages([])
    setConversationId(null)
    setErrorMsg('')
    setStatus('idle')
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
        <div className="flex items-center gap-4">
          {messages.length > 0 && (
            <button
              onClick={startNewChat}
              className="text-xs uppercase tracking-widest text-[#EFE9DD]/50 hover:text-[#C98A2C] border border-[#EFE9DD]/20 rounded px-3 py-1.5 transition-colors"
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              New Chat
            </button>
          )}
          <span
            className="text-xs uppercase tracking-widest text-[#EFE9DD]/50"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            {status === 'loading' ? 'transmitting' : 'standing by'}
          </span>
        </div>
      </header>

      {/* Main column */}
      <main className="flex-1 max-w-2xl w-full mx-auto px-6 py-8 flex flex-col gap-6 overflow-y-auto">
        {messages.length === 0 && (
          <div
            className="text-sm text-[#EFE9DD]/40 text-center mt-16"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            Ask a question below to open the wire.
          </div>
        )}

        {messages.map((msg, i) =>
          msg.role === 'user' ? (
            <div key={i} className="self-end max-w-[85%]">
              <div
                className="text-xs uppercase tracking-widest text-[#EFE9DD]/40 mb-1 text-right"
                style={{ fontFamily: 'var(--font-mono)' }}
              >
                You
              </div>
              <div
                className="bg-[#1E262A] border border-[#EFE9DD]/15 rounded-lg px-4 py-3 text-[#EFE9DD]"
                style={{ fontFamily: 'var(--font-body)' }}
              >
                {msg.text}
              </div>
            </div>
          ) : (
            <div key={i} className="self-start max-w-[90%] w-full">
              <div
                className="text-xs uppercase tracking-widest text-[#12181B]/50 mb-1"
                style={{ fontFamily: 'var(--font-mono)' }}
              >
                Dispatch
              </div>
              <article className="bg-[#EFE9DD] text-[#12181B] rounded-lg p-5 flex flex-col gap-3">
                <p
                  className="text-[1.02rem] leading-relaxed whitespace-pre-wrap"
                  style={{ fontFamily: 'var(--font-body)' }}
                >
                  {msg.text}
                </p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="border-t border-[#12181B]/15 pt-2">
                    <span
                      className="text-xs uppercase tracking-widest text-[#12181B]/50"
                      style={{ fontFamily: 'var(--font-mono)' }}
                    >
                      Sources
                    </span>
                    <ol
                      className="mt-1 flex flex-col gap-1 text-sm text-[#12181B]/70"
                      style={{ fontFamily: 'var(--font-mono)' }}
                    >
                      {msg.sources.map((url, j) => (
                        <li key={url} className="truncate">
                          [{j + 1}]{' '}
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
            </div>
          )
        )}

        {status === 'loading' && (
          <div
            className="self-start text-sm text-[#EFE9DD]/60 animate-pulse border border-[#EFE9DD]/15 rounded px-4 py-3"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            Agent is searching, reading sources, and cross-checking facts...
          </div>
        )}

        {status === 'error' && (
          <div
            className="border border-[#A8453A]/50 bg-[#A8453A]/10 rounded px-4 py-3 text-sm text-[#EFE9DD]"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            Error: {errorMsg}
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      {/* Input bar (sticky at bottom) */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-[#EFE9DD]/15 px-6 py-4"
      >
        <div className="max-w-2xl w-full mx-auto flex gap-3">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
            placeholder="Ask a follow-up or start a new inquiry..."
            rows={1}
            className="flex-1 bg-transparent border border-[#EFE9DD]/25 rounded px-4 py-3 text-[#EFE9DD] placeholder-[#EFE9DD]/30 focus:outline-none focus:border-[#C98A2C] resize-none"
            style={{ fontFamily: 'var(--font-body)' }}
          />
          <button
            type="submit"
            disabled={status === 'loading' || !question.trim()}
            className="px-5 py-2 rounded bg-[#C98A2C] text-[#12181B] font-semibold tracking-wide disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#dba24a] transition-colors"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            {status === 'loading' ? 'SENDING...' : 'SEND'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default App
