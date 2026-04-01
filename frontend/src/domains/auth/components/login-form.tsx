import { FormEvent, useState } from 'react'

type LoginFormProps = {
  onLogin: (email: string, password: string) => Promise<void>
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [email, setEmail] = useState('admin@optimus.local')
  const [password, setPassword] = useState('admin12345')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    try {
      setError(null)
      await onLogin(email, password)
    } catch {
      setError('Credenciais inválidas ou backend indisponível.')
    }
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <input className="w-full rounded bg-slate-800 p-2" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input
        className="w-full rounded bg-slate-800 p-2"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && <p className="text-sm text-rose-300">{error}</p>}
      <button className="rounded bg-cyan-600 px-4 py-2 text-white" type="submit">
        Entrar
      </button>
    </form>
  )
}
