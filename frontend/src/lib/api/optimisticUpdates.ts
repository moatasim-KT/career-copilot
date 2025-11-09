
import { get, set } from './cache';

interface Update<T> {
  id: string;
  apply: (data: T) => T;
  rollback: (data: T) => T;
}

class OptimisticUpdateManager<T> {
  private updates: Map<string, Update<T>> = new Map();

  constructor(private key: string) {}

  async apply(update: Update<T>) {
    this.updates.set(update.id, update);
    const currentData = await get<T>(this.key);
    if (currentData) {
      const optimisticData = update.apply(currentData);
      await set(this.key, optimisticData, 60000); // 1 minute TTL for optimistic update
    }
  }

  async rollback(updateId: string) {
    const update = this.updates.get(updateId);
    if (update) {
      const currentData = await get<T>(this.key);
      if (currentData) {
        const rolledBackData = update.rollback(currentData);
        await set(this.key, rolledBackData, 60000); // 1 minute TTL
      }
      this.updates.delete(updateId);
    }
  }
}

export function createOptimisticUpdateManager<T>(key: string) {
  return new OptimisticUpdateManager<T>(key);
}
