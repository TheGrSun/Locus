export function finiteBounds(values, fallback = [-6, 6]) {
  const finite = (values || []).filter((value) => value != null && Number.isFinite(value));
  if (!finite.length) return fallback.slice();
  let low = finite[0];
  let high = finite[0];
  for (const value of finite) {
    if (value < low) low = value;
    if (value > high) high = value;
  }
  return low === high ? [low - 1, high + 1] : [low, high];
}

/** Keep a blown-up function inside a window comparable to the x/y box. */
export function viewSpan(values, limit = 8) {
  const finite = (values || []).filter((value) => value != null && Number.isFinite(value)).sort((a, b) => a - b);
  const cap = Math.max(Number.isFinite(limit) ? limit : 8, 4);
  if (!finite.length) return [-cap, cap];
  const at = (fraction) => finite[Math.min(finite.length - 1, Math.round(fraction * (finite.length - 1)))];
  let low = at(0.1);
  let high = at(0.9);
  const mid = at(0.5);
  if (!(high > low) || high - low > cap * 2) {
    low = mid - cap;
    high = mid + cap;
  }
  if (low === high) return [low - 1, high + 1];
  const pad = 0.06 * (high - low);
  return [low - pad, high + pad];
}
