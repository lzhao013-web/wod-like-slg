// Small pure helpers for parsing and presenting game data.

export function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n))
}

/** Parses a "42/120" snapshot string (from reports) into a numeric fraction. */
export function parseHpFraction(raw: string | number | undefined): number {
  if (typeof raw === 'number') return raw
  if (!raw || typeof raw !== 'string') return 0
  const [num, den] = raw.split('/').map(s => parseInt(s, 10))
  if (!Number.isFinite(den) || den <= 0) return 0
  return clamp01((Number.isFinite(num) ? num : 0) / den)
}

export function parseHpParts(raw: string | number | undefined): { cur: number; max: number } {
  if (typeof raw === 'number') return { cur: raw, max: raw }
  if (!raw || typeof raw !== 'string') return { cur: 0, max: 0 }
  const [num, den] = raw.split('/').map(s => parseInt(s, 10))
  return { cur: Number.isFinite(num) ? num : 0, max: Number.isFinite(den) ? den : 0 }
}

/** Color stop for a health bar based on fraction remaining. */
export function hpColor(frac: number): string {
  if (frac > 0.6) return '#4caf50'
  if (frac > 0.3) return '#ffb300'
  return '#ef5350'
}

export function range(n: number): number[] {
  return Array.from({ length: n }, (_, i) => i)
}

/** Converts a stat dict {attack: 16, defense: 10} into a sorted, render-ready list. */
export function statEntries(stats: Record<string, number>, keys: string[]): Array<{ key: string; value: number }> {
  return keys.map(k => ({ key: k, value: stats[k] ?? 0 }))
}

/** Formats gold/materials numbers with thousands separators. */
export function num(n: number): string {
  return n.toLocaleString('zh-CN')
}

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}
