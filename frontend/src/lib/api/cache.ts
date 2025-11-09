interface CacheEntry<T> {
  value: T;
  expiry: number;
}

const cache = new Map<string, CacheEntry<any>>();

export async function set<T>(key: string, value: T, ttl: number) {
  const now = Date.now();
  cache.set(key, { value, expiry: now + ttl });
}

export async function get<T>(key: string): Promise<T | null> {
  const now = Date.now();
  const existing = cache.get(key);

  if (existing && now < existing.expiry) {
    return existing.value;
  }

  return null;
}

export async function cacheFn<T>(
  key: string,
  fn: () => Promise<T>,
  ttl: number,
): Promise<T> {
  const cachedValue = await get<T>(key);
  if (cachedValue) {
    return cachedValue;
  }

  const result = await fn();
  await set(key, result, ttl);
  return result;
}