/** Adds one fixed inline-SVG noise texture across the application. */
export function GrainOverlay() {
  return <div aria-hidden="true" className="grain-overlay pointer-events-none fixed inset-0 z-[var(--z-grain)] opacity-[0.035]" />
}
