export function formatLocation(label: string): string {
  return label
    .replace(/,\s*(?:United States of America|United States|USA)\s*$/i, "")
    .trim();
}