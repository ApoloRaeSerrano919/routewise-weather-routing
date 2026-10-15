
import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

import { formatLocation } from "../utils/location";

type Suggestion = {
  label: string;
  lat: number | null;
  lon: number | null;
};

type Props = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

export default function LocationAutocomplete({
  id,
  label,
  value,
  onChange,
  disabled = false,
}: Props) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [focused, setFocused] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);

  const selectedValue = useRef<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!focused || value.trim().length < 3 ||
        selectedValue.current === value) {
      setSuggestions([]);
      setOpen(false);
      setBusy(false);
      return;
    }

    const controller = new AbortController();

    const timer = window.setTimeout(async () => {
      setBusy(true);
      setError("");

      try {
        const response = await fetch(
          `/api/locations/?q=${encodeURIComponent(value.trim())}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error("Search unavailable");
        }

        const data: { suggestions: Suggestion[] } =
          await response.json();

        setSuggestions(data.suggestions);
        setOpen(true);
        setActiveIndex(-1);
      } catch (err) {
        if (!controller.signal.aborted) {
          setSuggestions([]);
          setOpen(false);
          setError("Location suggestions unavailable.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setBusy(false);
        }
      }
    }, 450);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [value, focused]);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setFocused(false);
        setOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () =>
      document.removeEventListener("pointerdown", handlePointerDown);
  }, []);

  function choose(item: Suggestion) {
    const formattedLocation = formatLocation(item.label);

    selectedValue.current = formattedLocation;
    onChange(formattedLocation);

    setSuggestions([]);
    setOpen(false);
    setActiveIndex(-1);
    }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      setOpen(false);
      return;
    }

    if (!open || suggestions.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) =>
        Math.min(index + 1, suggestions.length - 1)
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      choose(suggestions[activeIndex]);
    }
  }

  return (
    <div className="locationAutocomplete" ref={rootRef}>
      <label htmlFor={id}>{label}</label>

      <input
        id={id}
        type="text"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={open && suggestions.length > 0}
        aria-controls={`${id}-suggestions`}
        aria-activedescendant={
          open && activeIndex >= 0
            ? `${id}-option-${activeIndex}`
            : undefined
        }
        autoComplete="off"
        placeholder="Enter city or street address"
        value={value}
        disabled={disabled}
        required
        onFocus={() => setFocused(true)}
        onChange={(event) => {
          selectedValue.current = null;
          onChange(event.target.value);
          setActiveIndex(-1);
        }}
        onKeyDown={handleKeyDown}
      />

      {busy && (
        <div className="locationHint" role="status">
          Searching locations…
        </div>
      )}

      {error && <div className="locationHint">{error}</div>}

      {open && suggestions.length > 0 && (
        <ul
          className="locationSuggestions"
          id={`${id}-suggestions`}
          role="listbox"
        >
          {suggestions.map((item, index) => (
            <li
              key={`${item.label}-${index}`}
              id={`${id}-option-${index}`}
              role="option"
              aria-selected={activeIndex === index}
            >
              <button
                type="button"
                className={
                  "locationSuggestion" +
                  (activeIndex === index ? " active" : "")
                }
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(item)}
              >
                <span aria-hidden="true">⌖</span>
                <span>{formatLocation(item.label)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
