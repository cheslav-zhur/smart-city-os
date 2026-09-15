/** Shared fetch for orval-generated React Query hooks. Prefix is /api (Vite rewrite). */

export type OrvalResponse<T> = {
  data: T
  status: number
  headers: Headers
}

export async function customFetch<T extends { data: unknown; status: number; headers: Headers }>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    throw new Error(`${options?.method ?? 'GET'} ${url} ${response.status}`)
  }

  const contentType = response.headers.get('content-type') ?? ''
  const data =
    response.status === 204 || !contentType.includes('application/json')
      ? undefined
      : await response.json()

  return {
    data,
    status: response.status,
    headers: response.headers,
  } as T
}
