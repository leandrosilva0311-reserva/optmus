import { ReactNode } from 'react'

type ShellProps = {
  title: string
  children: ReactNode
}

export function Shell({ title, children }: ShellProps) {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-3xl font-bold text-white">{title}</h1>
      <section className="mt-6 rounded-xl border border-slate-700 bg-slate-900 p-6">{children}</section>
    </main>
  )
}
