import { MotionConfig } from 'motion/react'
import { Footer } from './components/layout/Footer'
import { Nav } from './components/layout/Nav'
import { Anatomy } from './components/sections/Anatomy'
import { Assertions } from './components/sections/Assertions'
import { Hero } from './components/sections/Hero'
import { Install } from './components/sections/Install'
import { LiveDemo } from './components/sections/LiveDemo'
import { Recorder } from './components/sections/Recorder'
import { Untested } from './components/sections/Untested'
import { GrainOverlay } from './components/ui/GrainOverlay'
import { DocsPage } from './pages/DocsPage'

/** Selects the landing and live demo or documentation surface from the current path. */
export function App() {
  if (window.location.pathname.startsWith('/docs')) return <MotionConfig reducedMotion="user"><DocsPage /></MotionConfig>

  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-[100dvh] overflow-x-hidden bg-[var(--bg-primary)]">
        <Nav />
        <main data-modal-background>
          <Hero />
          <LiveDemo />
          <Untested />
          <Recorder />
          <Assertions />
          <Anatomy />
          <Install />
        </main>
        <Footer />
        <GrainOverlay />
      </div>
    </MotionConfig>
  )
}
