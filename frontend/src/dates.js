// Date helpers — all display logic lives here so pages stay declarative.

export const DAY_MS = 86400000;

export function startOfDay(d) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

// Calendar-day arithmetic via date parts, not ms — adding 24h lands an hour
// off (and on the wrong day) in the week a DST transition falls.
export const addDays = (d, n) =>
  new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);

export function mondayOf(d) {
  const x = startOfDay(d);
  const dow = (x.getDay() + 6) % 7; // Mon=0
  return addDays(x, -dow);
}

export const sameDay = (a, b) =>
  a.getFullYear() === b.getFullYear() &&
  a.getMonth() === b.getMonth() &&
  a.getDate() === b.getDate();

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export const fmtDayShort = (d) => `${DAYS[d.getDay()]} ${d.getDate()}`;
export const fmtDayLong = (d) =>
  `${DAYS[d.getDay()]}, ${MONTHS[d.getMonth()]} ${d.getDate()}`;
export const fmtMonth = (d) => `${MONTHS[d.getMonth()]} ${d.getFullYear()}`;

export function fmtKicker(d) {
  const full = [
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
  ];
  const months = [
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
  ];
  return `${full[d.getDay()]}, ${months[d.getMonth()]} ${d.getDate()}`;
}

export function fmtTime(d) {
  let h = d.getHours();
  const m = d.getMinutes();
  const ap = h >= 12 ? "pm" : "am";
  h = h % 12 || 12;
  return m ? `${h}:${String(m).padStart(2, "0")}${ap}` : `${h}${ap}`;
}

export const fmtRange = (a, b) => `${fmtTime(a)}–${fmtTime(b)}`;

export function fmtWeekLabel(monday) {
  const sun = addDays(monday, 6);
  if (monday.getMonth() === sun.getMonth())
    return `${MONTHS[monday.getMonth()]} ${monday.getDate()}–${sun.getDate()}`;
  return `${MONTHS[monday.getMonth()]} ${monday.getDate()} – ${MONTHS[sun.getMonth()]} ${sun.getDate()}`;
}

export function relTime(ts) {
  const s = Math.max(0, (Date.now() - ts) / 1000);
  if (s < 60) return "now";
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  if (s < 86400) return `${Math.floor(s / 3600)}h`;
  return `${Math.floor(s / 86400)}d`;
}

// Full weeks covering the month, starting the Monday on/before the 1st.
// 5 weeks usually, 6 when the month spills into one (e.g. a 31-day month
// starting on a weekend) — a fixed 35 would drop the last day(s).
export function monthCells(anchor) {
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const start = mondayOf(first);
  const daysInMonth = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0).getDate();
  const lead = Math.round((first - start) / DAY_MS);
  const weeks = Math.ceil((lead + daysInMonth) / 7);
  return Array.from({ length: weeks * 7 }, (_, i) => {
    const d = addDays(start, i);
    return { date: d, dim: d.getMonth() !== anchor.getMonth() };
  });
}
