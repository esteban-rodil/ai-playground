export function extractDomain(url: string): string | null {
  try {
    const parsed = new URL(url);

    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return null;
    }

    return parsed.hostname.toLowerCase();
  } catch {
    return null;
  }
}
