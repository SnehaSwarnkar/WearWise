/**
 * ThemeContext — light-only stub.
 * Dark mode has been permanently removed from WearWise.
 * This stub is kept so existing imports don't break during the transition,
 * but it does nothing: the app always renders in light mode.
 */
import { createContext, useContext, useEffect } from "react";

const ThemeContext = createContext({ theme: "light", toggle: () => {} });

export function ThemeProvider({ children }) {
  // Ensure the html element never carries a dark-mode attribute
  useEffect(() => {
    const html = document.documentElement;
    // Remove any stale dark-theme attribute/class from localStorage or SSR
    html.removeAttribute("data-theme");
    html.classList.remove("no-transitions");
    // Clear any saved preference so it can't re-apply on next load
    localStorage.removeItem("ww-theme");
  }, []);

  return (
    <ThemeContext.Provider value={{ theme: "light", toggle: () => {} }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
