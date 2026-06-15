import type { Toast } from '../state/useGame'
import { cx } from '../lib/format'

const ICON: Record<Toast['tone'], string> = {
  info: 'ℹ️',
  success: '✅',
  warn: '⚠️',
  error: '⛔',
}

export function Toasts(props: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div className="toasts">
      {props.toasts.map(t => (
        <button key={t.id} className={cx('toast', `toast--${t.tone}`)} onClick={() => props.onDismiss(t.id)}>
          <span className="toast__icon">{ICON[t.tone]}</span>
          <span className="toast__text">{t.text}</span>
        </button>
      ))}
    </div>
  )
}
