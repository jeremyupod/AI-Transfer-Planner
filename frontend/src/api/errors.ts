export function formatApiError(body: unknown, status: number): string {
  const fallback = `Request failed (${status}). Please try again.`
  if (!body || typeof body !== 'object' || !('detail' in body)) return fallback
  const detail = body.detail
  if (typeof detail === 'string') return detail
  if (!Array.isArray(detail)) return fallback
  const messages = detail.flatMap((item: unknown) => {
    if (!item || typeof item !== 'object' || !('msg' in item) || typeof item.msg !== 'string') return []
    const location = 'loc' in item && Array.isArray(item.loc)
      ? item.loc.filter((part: unknown) => part !== 'body').join('.')
      : ''
    return [`${location ? `${location}: ` : ''}${item.msg}`]
  })
  return messages.length ? messages.join('; ') : fallback
}
