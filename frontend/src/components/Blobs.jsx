// Large blurred color blobs floating behind the glass — every page gets the
// same four blob "slots", but each page nudges their color, position, size and
// opacity. Because the slots persist across pages, CSS transitions morph one
// page's ambience into the next instead of snapping.

// [color, size, x%, y%, opacity] per slot — faint and spread out on purpose.
const SETS = {
  signin: [
    ["#2A9D8F", 520, 8, 4, 0.4],
    ["#BCA9C9", 400, 88, 10, 0.32],
    ["#D95D39", 440, 84, 88, 0.3],
    ["#DCA744", 360, 18, 92, 0.28],
  ],
  connect: [
    ["#2B5B84", 500, 6, 14, 0.34],
    ["#2A9D8F", 400, 90, 6, 0.3],
    ["#CBA39C", 340, 78, 90, 0.24],
    ["#DCA744", 300, 24, 96, 0.2],
  ],
  home: [
    ["#2A9D8F", 500, 6, 6, 0.4],
    ["#D95D39", 360, 92, 20, 0.3],
    ["#BCA9C9", 280, 80, 88, 0.26],
    ["#DCA744", 400, 34, 96, 0.3],
  ],
  calendar: [
    ["#2A9D8F", 430, 28, 2, 0.32],
    ["#D95D39", 320, 94, 74, 0.28],
    ["#BCA9C9", 260, 8, 66, 0.24],
    ["#DCA744", 300, 68, 98, 0.2],
  ],
  activity: [
    ["#CBA39C", 420, 30, 8, 0.28],
    ["#2B5B84", 340, 88, 84, 0.24],
    ["#2A9D8F", 260, 6, 80, 0.2],
    ["#BCA9C9", 300, 70, 4, 0.18],
  ],
  polls: [
    ["#DCA744", 430, 6, 26, 0.3],
    ["#2A9D8F", 320, 90, 78, 0.26],
    ["#D95D39", 260, 82, 8, 0.22],
    ["#BCA9C9", 300, 30, 96, 0.2],
  ],
  settings: [
    ["#E68E36", 440, 16, 12, 0.28],
    ["#2A9D8F", 340, 90, 82, 0.24],
    ["#2B5B84", 280, 6, 88, 0.2],
    ["#CBA39C", 300, 76, 4, 0.18],
  ],
};

export default function Blobs({ page }) {
  const set = SETS[page] || SETS.home;
  return set.map(([c, size, x, y, op], i) => (
    <div
      key={i}
      style={{
        position: "absolute",
        borderRadius: "50%",
        filter: "blur(80px)",
        pointerEvents: "none",
        width: size,
        height: size,
        left: `${x}%`,
        top: `${y}%`,
        transform: "translate(-50%, -50%)",
        background: `color-mix(in srgb, ${c} 34%, #F7F1E6)`,
        opacity: op,
        transition:
          "left 1.1s cubic-bezier(.4,0,.2,1), top 1.1s cubic-bezier(.4,0,.2,1), width 1.1s cubic-bezier(.4,0,.2,1), height 1.1s cubic-bezier(.4,0,.2,1), background 1.1s linear, opacity 1.1s linear",
      }}
    />
  ));
}
