/**
 * Search Utilities
 * 
 * Functions to apply search queries to data and serialize/deserialize queries.
 */

import { logger } from '@/lib/logger';
import type { SearchGroup, SearchRule } from '@/types/search';


/**
 * Apply a search rule to a single item
 */
function applyRule<T extends Record<string, any>>(item: T, rule: SearchRule): boolean {
  const fieldValue = item[rule.field];
  const { operator, value, value2 } = rule;

  // Handle empty/not empty operators
  if (operator === 'isEmpty') {
    return fieldValue === null || fieldValue === undefined || fieldValue === '';
  }
  if (operator === 'isNotEmpty') {
    return fieldValue !== null && fieldValue !== undefined && fieldValue !== '';
  }

  // If field is empty and operator requires a value, return false
  if (fieldValue === null || fieldValue === undefined) {
    return false;
  }

  // Apply operator-specific logic
  switch (operator) {
    // Text operators
    case 'contains':
      return String(fieldValue).toLowerCase().includes(String(value).toLowerCase());

    case 'equals':
      return String(fieldValue).toLowerCase() === String(value).toLowerCase();

    case 'startsWith':
      return String(fieldValue).toLowerCase().startsWith(String(value).toLowerCase());

    case 'endsWith':
      return String(fieldValue).toLowerCase().endsWith(String(value).toLowerCase());

    // Number operators
    case 'gt':
      return Number(fieldValue) > Number(value);

    case 'gte':
      return Number(fieldValue) >= Number(value);

    case 'lt':
      return Number(fieldValue) < Number(value);

    case 'lte':
      return Number(fieldValue) <= Number(value);

    case 'between':
      return Number(fieldValue) >= Number(value) && Number(fieldValue) <= Number(value2);

    // Date operators
    case 'before':
      return new Date(fieldValue) < new Date(value);

    case 'after':
      return new Date(fieldValue) > new Date(value);

    case 'inLastDays': {
      const daysAgo = new Date();
      daysAgo.setDate(daysAgo.getDate() - Number(value));
      return new Date(fieldValue) >= daysAgo;
    }

    case 'inNextDays': {
      const daysFromNow = new Date();
      daysFromNow.setDate(daysFromNow.getDate() + Number(value));
      return new Date(fieldValue) <= daysFromNow && new Date(fieldValue) >= new Date();
    }

    // Boolean operators
    case 'is':
      return Boolean(fieldValue) === Boolean(value);

    case 'isNot':
      return Boolean(fieldValue) !== Boolean(value);

    // Array/Select operators
    case 'in':
      if (Array.isArray(value)) {
        return value.includes(fieldValue);
      }
      return String(fieldValue) === String(value);

    case 'notIn':
      if (Array.isArray(value)) {
        return !value.includes(fieldValue);
      }
      return String(fieldValue) !== String(value);

    default:
      logger.warn(`Unknown operator: ${operator}`);
      return true;
  }
}

/**
 * Apply a search group to a single item
 */
function applyGroup<T extends Record<string, any>>(item: T, group: SearchGroup): boolean {
  const ruleResults = group.rules.map(rule => applyRule(item, rule));
  const groupResults = (group.groups || []).map(nestedGroup => applyGroup(item, nestedGroup));

  const allResults = [...ruleResults, ...groupResults];

  if (allResults.length === 0) {
    return true; // Empty group matches everything
  }

  if (group.logic === 'AND') {
    return allResults.every(result => result);
  } else {
    return allResults.some(result => result);
  }
}

/**
 * Filter an array of items using a search query
 */
export function applySearchQuery<T extends Record<string, any>>(
  items: T[],
  query: SearchGroup,
): T[] {
  // If query has no criteria, return all items
  if (query.rules.length === 0 && (!query.groups || query.groups.length === 0)) {
    return items;
  }

  return items.filter(item => applyGroup(item, query));
}

/**
 * Count how many items match a search query
 */
export function countSearchResults<T extends Record<string, any>>(
  items: T[],
  query: SearchGroup,
): number {
  return applySearchQuery(items, query).length;
}

/**
 * Serialize a search query to a URL-safe string
 */
export function serializeQuery(query: SearchGroup): string {
  try {
    const json = JSON.stringify(query);
    return btoa(encodeURIComponent(json));
  } catch (error) {
    logger.error('Failed to serialize query:', error);
    return '';
  }
}

/**
 * Deserialize a search query from a URL-safe string
 */
export function deserializeQuery(serialized: string): SearchGroup | null {
  try {
    const json = decodeURIComponent(atob(serialized));
    return JSON.parse(json);
  } catch (error) {
    logger.error('Failed to deserialize query:', error);
    return null;
  }
}

/**
 * Convert a search query to URL search params
 */
export function queryToSearchParams(query: SearchGroup): URLSearchParams {
  const params = new URLSearchParams();
  const serialized = serializeQuery(query);
  if (serialized) {
    params.set('q', serialized);
  }
  return params;
}

/**
 * Extract a search query from URL search params
 */
export function searchParamsToQuery(params: URLSearchParams): SearchGroup | null {
  const serialized = params.get('q');
  if (!serialized) return null;
  return deserializeQuery(serialized);
}

/**
 * Check if a query has any search criteria
 */
export function hasSearchCriteria(query: SearchGroup): boolean {
  return query.rules.length > 0 || (query.groups?.length || 0) > 0;
}

/**
 * Create an empty search query
 */
export function createEmptyQuery(): SearchGroup {
  return {
    id: `root-${Date.now()}`,
    logic: 'AND',
    rules: [],
    groups: [],
  };
}
