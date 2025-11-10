/**
 * Advanced Search System Types
 * 
 * This module defines the type system for the advanced search functionality,
 * supporting complex queries with nested groups and multiple operators.
 */

/**
 * Supported operators for different field types
 */
export type TextOperator = 'contains' | 'equals' | 'startsWith' | 'endsWith' | 'isEmpty' | 'isNotEmpty';
export type NumberOperator = 'equals' | 'gt' | 'gte' | 'lt' | 'lte' | 'between' | 'isEmpty' | 'isNotEmpty';
export type DateOperator = 'before' | 'after' | 'between' | 'inLastDays' | 'inNextDays' | 'isEmpty' | 'isNotEmpty';
export type BooleanOperator = 'is' | 'isNot';
export type SelectOperator = 'equals' | 'in' | 'notIn' | 'isEmpty' | 'isNotEmpty';

export type SearchOperator = TextOperator | NumberOperator | DateOperator | BooleanOperator | SelectOperator;

/**
 * Field types supported by the search system
 */
export type FieldType = 'text' | 'number' | 'date' | 'boolean' | 'select' | 'multiselect';

/**
 * Logical operators for combining rules and groups
 */
export type LogicOperator = 'AND' | 'OR';

/**
 * Definition of a searchable field
 */
export interface SearchField {
  /** Unique identifier for the field */
  name: string;
  
  /** Human-readable label */
  label: string;
  
  /** Field data type */
  type: FieldType;
  
  /** Available operators for this field type */
  operators: SearchOperator[];
  
  /** Options for select/multiselect fields */
  options?: Array<{ value: string; label: string }>;
  
  /** Placeholder text for value input */
  placeholder?: string;
  
  /** Help text explaining the field */
  helpText?: string;
  
  /** Whether this field is required */
  required?: boolean;
  
  /** Default operator for this field */
  defaultOperator?: SearchOperator;
}

/**
 * A single search rule (condition)
 */
export interface SearchRule {
  /** Unique identifier for this rule */
  id: string;
  
  /** Field name being searched */
  field: string;
  
  /** Comparison operator */
  operator: SearchOperator;
  
  /** Value(s) to compare against */
  value: any;
  
  /** Optional second value for 'between' operators */
  value2?: any;
}

/**
 * A group of search rules combined with a logical operator
 * Groups can be nested to create complex queries
 */
export interface SearchGroup {
  /** Unique identifier for this group */
  id: string;
  
  /** Logical operator combining rules/groups (AND/OR) */
  logic: LogicOperator;
  
  /** Rules in this group */
  rules: SearchRule[];
  
  /** Nested groups for complex queries */
  groups?: SearchGroup[];
}

/**
 * Complete search query structure
 */
export interface SearchQuery {
  /** Root search group */
  root: SearchGroup;
  
  /** Optional name for saved searches */
  name?: string;
  
  /** Optional description */
  description?: string;
  
  /** Timestamp when created */
  createdAt?: Date;
  
  /** Timestamp when last modified */
  updatedAt?: Date;
}

/**
 * Saved search with metadata
 */
export interface SavedSearch {
  /** Unique identifier */
  id: string;
  
  /** User-provided name */
  name: string;
  
  /** Optional description */
  description?: string;
  
  /** The search query */
  query: SearchGroup;
  
  /** When this search was created */
  createdAt: Date;
  
  /** When this search was last used */
  lastUsedAt?: Date;
  
  /** Number of times this search has been used */
  useCount?: number;
  
  /** Estimated result count (cached) */
  resultCount?: number;
  
  /** Whether this search is shared (future feature) */
  shared?: boolean;
  
  /** Tags for organizing searches */
  tags?: string[];
}

/**
 * Recent search history entry
 */
export interface RecentSearch {
  /** Unique identifier */
  id: string;
  
  /** The search query */
  query: SearchGroup;
  
  /** When this search was performed */
  timestamp: Date;
  
  /** Number of results returned */
  resultCount?: number;
  
  /** Optional label for the search */
  label?: string;
}

/**
 * Search context for different entities
 */
export type SearchContext = 'jobs' | 'applications' | 'companies' | 'contacts';

/**
 * Filter chip representation for active filters
 */
export interface FilterChip {
  /** Unique identifier */
  id: string;
  
  /** Display label */
  label: string;
  
  /** Field name */
  field: string;
  
  /** Operator used */
  operator: SearchOperator;
  
  /** Value(s) */
  value: any;
  
  /** Optional second value for between operators */
  value2?: any;
  
  /** Whether this chip can be removed */
  removable?: boolean;
  
  /** Whether this chip can be edited */
  editable?: boolean;
}

/**
 * Search validation result
 */
export interface SearchValidation {
  /** Whether the search is valid */
  valid: boolean;
  
  /** Validation errors by rule/group ID */
  errors: Record<string, string>;
  
  /** Warnings that don't prevent search */
  warnings?: Record<string, string>;
}

/**
 * Search result metadata
 */
export interface SearchResultMeta {
  /** Total number of results */
  total: number;
  
  /** Number of results on current page */
  count: number;
  
  /** Current page number */
  page: number;
  
  /** Results per page */
  pageSize: number;
  
  /** Total number of pages */
  totalPages: number;
  
  /** Time taken to execute search (ms) */
  executionTime?: number;
  
  /** Applied filters summary */
  appliedFilters?: FilterChip[];
}

/**
 * Export format options
 */
export type ExportFormat = 'json' | 'csv' | 'url';

/**
 * Serialized search query for URL or storage
 */
export interface SerializedSearch {
  /** Serialized query string */
  query: string;
  
  /** Format used for serialization */
  format: ExportFormat;
  
  /** Version for backward compatibility */
  version: string;
}
