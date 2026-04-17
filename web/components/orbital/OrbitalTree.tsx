'use client'

import { useEffect, useRef } from 'react'
import { TREE, type Module, type Group } from '@/lib/tree-data'

interface OrbitalTreeProps {
  onOpenModule: (module: Module, group: Group) => void
  onStateChange?: (inGroup: boolean) => void
}

const SZ = { center: 80, group: 72, child: 52 } as const
const HW = { center: 40, group: 36, child: 26 } as const
const FS = { center: 30, group: 26, child: 18 } as const
const FADE = 320

type NodeType = keyof typeof SZ

export function OrbitalTree({ onOpenModule, onStateChange }: OrbitalTreeProps) {
  const universeRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const universe = universeRef.current!
    if (!universe) return

    // ── State ──────────────────────────────────────────────
    let raf = 0
    let angle = 0
    type OrbitItem = { el: HTMLDivElement; hw: number; baseAngle: number; radius: number }
    let orbitItems: OrbitItem[] = []
    let sceneEls: HTMLDivElement[] = []
    let rings: HTMLDivElement[] = []
    let pulseRings: HTMLDivElement[] = []
    let busy = false
    let activeGroup: Group | null = null
    let destroyed = false

    // ── Helpers ─────────────────────────────────────────────
    function setPos(el: HTMLDivElement, x: number, y: number, hw: number) {
      el.style.transform = `translate(${x - hw}px,${y - hw}px)`
      ;(el as any)._x = x
      ;(el as any)._y = y
    }

    function fadeIn(el: HTMLElement, dur = FADE, delay = 0) {
      el.style.transition = `opacity ${dur}ms ease ${delay}ms`
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          el.style.opacity = '1'
        })
      )
    }

    function fadeOut(el: HTMLElement, dur = FADE) {
      el.style.transition = `opacity ${dur}ms ease`
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          el.style.opacity = '0'
        })
      )
    }

    function makeNode(
      data: { id: string; emoji: string; label: string; color: string },
      type: NodeType
    ): HTMLDivElement {
      const size = SZ[type]
      const hw = HW[type]
      const fs = FS[type]
      const isCenter = type === 'center'

      const el = document.createElement('div')
      el.style.cssText = `
        position:absolute; left:0; top:0;
        display:flex; flex-direction:column; align-items:center;
        opacity:0; user-select:none; pointer-events:auto;
        cursor:${isCenter ? 'default' : 'pointer'};
      `
      el.style.setProperty('--glow', data.color + '66')
      el.style.setProperty('--glow-dim', data.color + '22')
      ;(el as any)._hw = hw
      ;(el as any)._type = type

      const circle = document.createElement('div')
      circle.style.cssText = `
        border-radius:50%; display:flex; align-items:center; justify-content:center;
        width:${size}px; height:${size}px; font-size:${fs}px;
        border:2px solid ${isCenter ? data.color : 'rgba(255,255,255,0.18)'};
        background:${isCenter ? data.color + '22' : '#0c0c0c'};
        transition:border-color .3s, transform .25s;
        ${isCenter ? `box-shadow:0 0 25px ${data.color}66,0 0 50px ${data.color}22; animation:breathe 3s ease-in-out infinite;` : ''}
      `
      circle.textContent = data.emoji

      const label = document.createElement('div')
      label.style.cssText = `
        margin-top:8px; font-size:10px; font-weight:600; letter-spacing:.5px;
        color:rgba(255,255,255,.45); white-space:nowrap; font-family:-apple-system,sans-serif;
        transition:color .3s;
      `
      label.textContent = data.label

      if (!isCenter) {
        el.addEventListener('mouseenter', () => {
          circle.style.borderColor = 'rgba(255,255,255,0.55)'
          circle.style.transform = 'scale(1.12)'
          label.style.color = '#fff'
        })
        el.addEventListener('mouseleave', () => {
          circle.style.borderColor = 'rgba(255,255,255,0.18)'
          circle.style.transform = 'scale(1)'
          label.style.color = 'rgba(255,255,255,.45)'
        })
      }

      el.appendChild(circle)
      el.appendChild(label)
      universe.appendChild(el)
      setPos(el, 0, 0, hw)
      return el
    }

    function makeRings(radii: number[]) {
      rings.forEach((r) => r.remove())
      rings = []
      radii.forEach((r) => {
        const el = document.createElement('div')
        el.style.cssText = `
          position:absolute; border-radius:50%;
          border:1px solid rgba(255,255,255,0.05);
          pointer-events:none;
          width:${r * 2}px; height:${r * 2}px;
          transform:translate(-50%,-50%);
        `
        universe.appendChild(el)
        rings.push(el)
      })
    }

    function makePulse(color: string) {
      pulseRings.forEach((r) => r.remove())
      pulseRings = []
      ;[0, 1].forEach((i) => {
        const el = document.createElement('div')
        el.style.cssText = `
          position:absolute; border-radius:50%; border:1px solid ${color}44;
          pointer-events:none; width:160px; height:160px;
          animation:pulse-out 2s ease-out ${i * 0.7}s infinite;
        `
        universe.appendChild(el)
        pulseRings.push(el)
      })
    }

    // ── Orbit rAF ───────────────────────────────────────────
    function startOrbit() {
      cancelAnimationFrame(raf)
      const tick = () => {
        if (destroyed) return
        angle += 0.004
        orbitItems.forEach((item) => {
          const a = item.baseAngle + angle
          const x = Math.cos(a) * item.radius
          const y = Math.sin(a) * item.radius
          item.el.style.transform = `translate(${x - item.hw}px,${y - item.hw}px)`
          ;(item.el as any)._x = x
          ;(item.el as any)._y = y
          const d = (Math.sin(a) + 1) / 2
          item.el.style.opacity = String(0.35 + 0.65 * d)
          item.el.style.zIndex = String(Math.round(10 + 40 * d))
        })
        raf = requestAnimationFrame(tick)
      }
      tick()
    }

    function stopOrbit() {
      cancelAnimationFrame(raf)
      raf = 0
    }

    function handoffToRAF() {
      orbitItems.forEach((item) => {
        item.el.style.transition = ''
      })
    }

    // ── Home ────────────────────────────────────────────────
    function renderHome() {
      stopOrbit()
      activeGroup = null
      orbitItems = []
      sceneEls = []
      busy = false

      makeRings([180, 280])
      makePulse('#16a34a')

      const root = makeNode(TREE.root, 'center')
      setPos(root, 0, 0, HW.center)
      sceneEls.push(root)
      fadeIn(root, FADE)

      TREE.groups.forEach((g, i) => {
        const theta = (i / TREE.groups.length) * 2 * Math.PI - Math.PI / 2
        const el = makeNode(g, 'group')
        const rx = Math.cos(theta) * 200
        const ry = Math.sin(theta) * 200
        setPos(el, rx, ry, HW.group)
        sceneEls.push(el)
        fadeIn(el, FADE, i * 60)
        el.addEventListener('click', () => {
          if (!busy) drillInto(g, el)
        })
        orbitItems.push({ el, hw: HW.group, baseAngle: theta, radius: 200 })
      })

      startOrbit()
      setTimeout(handoffToRAF, FADE + 200)
    }

    // ── Drill in ────────────────────────────────────────────
    function drillInto(group: Group, clickedEl: HTMLDivElement) {
      busy = true
      stopOrbit()

      const circ = clickedEl.querySelector('div') as HTMLDivElement
      if (circ) {
        circ.style.transition = 'transform .38s cubic-bezier(.2,0,0,1)'
        requestAnimationFrame(() =>
          requestAnimationFrame(() => {
            circ.style.transform = 'scale(2.6)'
          })
        )
      }

      sceneEls.filter((e) => e !== clickedEl).forEach((e) => fadeOut(e, FADE * 0.8))

      setTimeout(() => {
        const oldEls = [...sceneEls]
        sceneEls = []
        orbitItems = []
        activeGroup = group
        onStateChange?.(true)

        makeRings([140, 220])
        makePulse(group.color)

        const center = makeNode(group, 'center')
        setPos(center, 0, 0, HW.center)
        sceneEls.push(center)
        fadeIn(center, FADE)

        group.children.forEach((child, i) => {
          const theta = (i / group.children.length) * 2 * Math.PI - Math.PI / 2
          const el = makeNode(child, 'child')
          const rx = Math.cos(theta) * 170
          const ry = Math.sin(theta) * 170
          setPos(el, rx, ry, HW.child)
          sceneEls.push(el)
          fadeIn(el, FADE, 60 + i * 55)
          el.addEventListener('click', (e) => {
            e.stopPropagation()
            if (!busy) onOpenModule(child, group)
          })
          orbitItems.push({ el, hw: HW.child, baseAngle: theta, radius: 170 })
        })

        setTimeout(() => {
          oldEls.forEach((e) => {
            if (e.parentNode) e.remove()
          })
        }, FADE + 50)

        startOrbit()
        setTimeout(handoffToRAF, FADE + 250)
        setTimeout(() => {
          busy = false
        }, FADE + 300)
      }, 380)
    }

    // ── Go back ─────────────────────────────────────────────
    ;(universe as any).__goBack = () => {
      if (busy) return
      busy = true
      stopOrbit()

      const oldEls = [...sceneEls]
      sceneEls = []
      orbitItems = []
      oldEls.forEach((e) => fadeOut(e, FADE))

      setTimeout(() => {
        oldEls.forEach((e) => {
          if (e.parentNode) e.remove()
        })
        rings.forEach((r) => r.remove())
        pulseRings.forEach((r) => r.remove())
        rings = []
        pulseRings = []
        onStateChange?.(false)
        renderHome()
      }, FADE + 60)
    }

    ;(universe as any).__getActiveGroup = () => activeGroup

    renderHome()

    return () => {
      destroyed = true
      cancelAnimationFrame(raf)
      universe.innerHTML = ''
    }
  }, [onOpenModule])

  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: 0,
        height: 0,
        pointerEvents: 'none',
      }}
      ref={universeRef}
    />
  )
}
