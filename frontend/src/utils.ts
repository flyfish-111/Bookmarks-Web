export function getHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

export function formatDate(iso: string): string {
  if (!iso) return ''
  return iso.slice(0, 10)
}
