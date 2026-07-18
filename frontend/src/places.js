// Place search: a small curated list of spots the group already knows, the
// user's own recents/reviews, and live OpenStreetMap (Nominatim) results.
// Everything degrades gracefully — free text is always allowed.

export const LOCAL_PLACES = [
  { name: "BHive Cafe", area: "Hamra, Beirut" },
  { name: "Kalei Coffee Co.", area: "Mar Mikhael, Beirut" },
  { name: "Socrate", area: "Hamra, Beirut" },
  { name: "Cheers Broumana", area: "Broumana" },
  { name: "ABC Verdun VOX", area: "Verdun, Beirut" },
  { name: "Lazy B", area: "Jiyeh" },
  { name: "AUB Jafet Library", area: "AUB, Beirut" },
  { name: "Tannourine Cedar Reserve", area: "Tannourine" },
  { name: "Em Sherif Cafe", area: "Downtown, Beirut" },
  { name: "Backburner Coffee", area: "Badaro, Beirut" },
];

const norm = (s) => (s || "").toLowerCase().trim();

// Prefix-and-substring match: "bhi" hits "BHive Cafe".
export function matchPlaces(list, q, limit = 5) {
  const n = norm(q);
  if (!n) return list.slice(0, limit);
  const starts = [], contains = [];
  for (const p of list) {
    const name = norm(typeof p === "string" ? p : p.name);
    if (name.startsWith(n)) starts.push(p);
    else if (name.includes(n)) contains.push(p);
  }
  return [...starts, ...contains].slice(0, limit);
}

// Live search on OpenStreetMap — no key needed, fails silently offline.
export async function searchOsm(q, signal) {
  if (norm(q).length < 3) return [];
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&limit=4&q=${encodeURIComponent(q)}`,
      { signal, headers: { Accept: "application/json" } }
    );
    if (!res.ok) return [];
    const rows = await res.json();
    return rows.map((r) => {
      const parts = (r.display_name || "").split(",");
      return {
        name: parts[0].trim(),
        area: parts.slice(1, 3).join(",").trim(),
        osm: true,
      };
    });
  } catch {
    return [];
  }
}
