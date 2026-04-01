type TopNavProps = {
  section: string
  onNavigate: (section: string) => void
  isAuthenticated: boolean
  onLogout: () => void
}

const sections = ['landing', 'dashboard', 'workspace', 'logs']

export function TopNav({ section, onNavigate, isAuthenticated, onLogout }: TopNavProps) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <button className="text-lg font-semibold text-white" onClick={() => onNavigate('landing')}>
          Optimus
        </button>
        <nav className="flex items-center gap-4">
          {sections.map((item) => (
            <button
              key={item}
              onClick={() => onNavigate(item)}
              className={`text-sm ${section === item ? 'text-cyan-300' : 'text-slate-300'}`}
            >
              {item}
            </button>
          ))}
          {isAuthenticated && (
            <button className="rounded bg-rose-500 px-3 py-1 text-sm text-white" onClick={onLogout}>
              logout
            </button>
          )}
        </nav>
      </div>
    </header>
  )
}
