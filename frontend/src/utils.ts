/** Format a number with commas: 12345 → "12,345" */
export function fmt(n: number): string {
  return n.toLocaleString('en-US');
}

/** Format a float to 2 decimal places with commas */
export function fmtDec(n: number): string {
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** Format a percentage (0-1) → "49.0%" */
export function fmtPct(n: number): string {
  return (n * 100).toFixed(1) + '%';
}

/** Format a unix timestamp to a readable date */
export function fmtDate(ts: number): string {
  return new Date(ts * 1000).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

/** Format ISO date string to readable */
export function fmtISODate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

/** Classname helper - join truthy strings */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}
