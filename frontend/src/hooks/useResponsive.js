import { useState, useEffect } from 'react';

const BREAKPOINTS = { mobile: 680, tablet: 1024 };

function snapshot(width) {
  return {
    isMobile:  width < BREAKPOINTS.mobile,
    isTablet:  width >= BREAKPOINTS.mobile && width < BREAKPOINTS.tablet,
    isDesktop: width >= BREAKPOINTS.tablet,
    width,
  };
}

// SSR-safe initial value — falls back to desktop if window unavailable
const initial = typeof window !== 'undefined'
  ? snapshot(window.innerWidth)
  : snapshot(BREAKPOINTS.tablet);

export function useResponsive() {
  const [state, setState] = useState(initial);

  useEffect(() => {
    let raf;
    const handler = () => {
      // Use rAF to batch rapid resize events (no setTimeout needed)
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => setState(snapshot(window.innerWidth)));
    };
    window.addEventListener('resize', handler, { passive: true });
    // Sync immediately in case mount happened at a different size
    handler();
    return () => {
      window.removeEventListener('resize', handler);
      cancelAnimationFrame(raf);
    };
  }, []);

  return state;
}
