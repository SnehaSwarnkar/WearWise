import { createContext, useContext, useState, useEffect, useRef } from "react";

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    // Read saved preference without triggering a transition on mount
    return localStorage.getItem("ww-theme") || "light";
  });

  // Suppress transitions during the very first paint so the initial
  // theme applies instantly (no flash / animation on page load).
  const isMounted = useRef(false);

  useEffect(() => {
    const html = document.documentElement;

    if (!isMounted.current) {
      // First mount: apply theme silently, then remove the suppressor
      // after one frame so subsequent toggles animate normally.
      html.classList.add("no-transitions");
      html.setAttribute("data-theme", theme);

      // Two rAFs ensure the browser has painted before we re-enable transitions
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          html.classList.remove("no-transitions");
          isMounted.current = true;
        });
      });
    } else {
      // Subsequent changes: let the global transition play
      html.setAttribute("data-theme", theme);
    }

    localStorage.setItem("ww-theme", theme);
  }, [theme]);

  const toggle = () =>
    setTheme((t) => (t === "negative" ? "light" : "negative"));

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
