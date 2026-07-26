/**
 * Three redacted lines, the last one unredacted and in flag colour — the
 * product's whole thesis in 14 pixels. Replaces the letter tile left over from
 * the LeakScan name.
 */
export function Mark({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      aria-hidden
      className={`h-[1.15rem] w-[1.15rem] shrink-0 ${className}`}
    >
      <rect y="1.8" width="16" height="3.1" fill="currentColor" />
      <rect y="6.45" width="11" height="3.1" fill="currentColor" />
      <rect
        y="11.1"
        width="6.5"
        height="3.1"
        className="origin-left fill-flag transition-transform duration-300 group-hover:scale-x-150"
      />
    </svg>
  );
}
