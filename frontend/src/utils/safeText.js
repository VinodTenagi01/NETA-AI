export function safeText(value) {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (value?.message && typeof value.message === 'string') return value.message;
  if (value?.title && typeof value.title === 'string') return value.title;
  if (value?.text && typeof value.text === 'string') return value.text;
  try { return JSON.stringify(value); } catch { return '[object]'; }
}
