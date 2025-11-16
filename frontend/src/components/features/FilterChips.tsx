/**
 * FilterChips Component
 * 
 * Displays active search filters as removable/editable chips.
 */

'use client';

import { X, Edit, Trash2 } from 'lucide-react';

import Button2 from '@/components/ui/Button2';
import { staggerContainer, staggerItem, springConfigs } from '@/lib/animations';
import { m, AnimatePresence } from '@/lib/motion';
import type { FilterChip, SearchGroup, SearchRule } from '@/types/search';

export interface FilterChipsProps {
  /** Current search query */
  query: SearchGroup;
  
  /** Callback when a filter should be removed */
  onRemoveFilter: (ruleId: string) => void;
  
  /** Callback when a filter should be edited */
  onEditFilter?: (ruleId: string) => void;
  
  /** Callback to clear all filters */
  onClearAll: () => void;
  
  /** Custom class name */
  className?: string;
}

/**
 * Get human-readable label for an operator
 */
function getOperatorLabel(operator: string): string {
  const labels: Record<string, string> = {
    contains: 'contains',
    equals: 'is',
    startsWith: 'starts with',
    endsWith: 'ends with',
    isEmpty: 'is empty',
    isNotEmpty: 'is not empty',
    gt: '>',
    gte: '≥',
    lt: '<',
    lte: '≤',
    between: 'between',
    before: 'before',
    after: 'after',
    inLastDays: 'in last',
    inNextDays: 'in next',
    is: 'is',
    isNot: 'is not',
    in: 'in',
    notIn: 'not in',
  };
  return labels[operator] || operator;
}

/**
 * Format value for display
 */
function formatValue(value: any, operator: string): string {
  if (value === null || value === undefined || value === '') {
    return '';
  }

  if (Array.isArray(value)) {
    return value.join(', ');
  }

  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }

  if (operator === 'inLastDays' || operator === 'inNextDays') {
    return `${value} days`;
  }

  // Truncate long values
  const str = String(value);
  if (str.length > 30) {
    return `${str.substring(0, 27)}...`;
  }

  return str;
}

/**
 * Convert a rule to a filter chip
 */
function ruleToChip(rule: SearchRule, fieldLabel: string): FilterChip {
  const operatorLabel = getOperatorLabel(rule.operator);
  const valueLabel = formatValue(rule.value, rule.operator);
  const value2Label = rule.value2 ? formatValue(rule.value2, rule.operator) : '';

  let label: string;
  if (rule.operator === 'isEmpty' || rule.operator === 'isNotEmpty') {
    label = `${fieldLabel} ${operatorLabel}`;
  } else if (rule.operator === 'between') {
    label = `${fieldLabel} ${operatorLabel} ${valueLabel} and ${value2Label}`;
  } else {
    label = `${fieldLabel} ${operatorLabel} ${valueLabel}`;
  }

  return {
    id: rule.id,
    label,
    field: rule.field,
    operator: rule.operator,
    value: rule.value,
    value2: rule.value2,
    removable: true,
    editable: true,
  };
}

/**
 * Extract all rules from a search group (including nested groups)
 */
function extractAllRules(group: SearchGroup): SearchRule[] {
  const rules: SearchRule[] = [...group.rules];
  
  if (group.groups) {
    for (const nestedGroup of group.groups) {
      rules.push(...extractAllRules(nestedGroup));
    }
  }
  
  return rules;
}

/**
 * FilterChips Component
 */
export function FilterChips({
  query,
  onRemoveFilter,
  onEditFilter,
  onClearAll,
  className = '',
}: FilterChipsProps) {
  // Extract all rules from the query
  const allRules = extractAllRules(query);
  
  // Convert rules to chips
  const chips: FilterChip[] = allRules.map(rule =>
    ruleToChip(rule, rule.field), // In a real implementation, you'd look up the field label
  );

  if (chips.length === 0) {
    return null;
  }

  return (
    <m.div
      className={`flex flex-wrap items-center gap-2 ${className}`}
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
    >
      {/* Filter Count Badge */}
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
          Active Filters:
        </span>
        <span className="px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full">
          {chips.length}
        </span>
      </div>

      {/* Filter Chips */}
      <AnimatePresence mode="popLayout">
        {chips.map((chip) => (
          <m.div
            key={chip.id}
            variants={staggerItem}
            layout
            initial="hidden"
            animate="visible"
            exit={{
              opacity: 0,
              scale: 0.8,
              transition: { duration: 0.2 },
            }}
            transition={springConfigs.gentle}
          >
            <div className="group flex items-center space-x-1 px-3 py-1.5 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-full text-sm hover:border-blue-500 dark:hover:border-blue-500 transition-colors">
              <span className="text-neutral-900 dark:text-neutral-100">
                {chip.label}
              </span>
              
              <div className="flex items-center space-x-0.5 ml-1">
                {chip.editable && onEditFilter && (
                  <button
                    type="button"
                    onClick={() => onEditFilter(chip.id)}
                    className="p-0.5 text-neutral-500 hover:text-blue-600 dark:hover:text-blue-400 rounded transition-colors opacity-0 group-hover:opacity-100"
                    aria-label={`Edit filter: ${chip.label}`}
                  >
                    <Edit className="h-3 w-3" />
                  </button>
                )}
                
                {chip.removable && (
                  <button
                    type="button"
                    onClick={() => onRemoveFilter(chip.id)}
                    className="p-0.5 text-neutral-500 hover:text-red-600 dark:hover:text-red-400 rounded transition-colors"
                    aria-label={`Remove filter: ${chip.label}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            </div>
          </m.div>
        ))}
      </AnimatePresence>

      {/* Clear All Button */}
      {chips.length > 1 && (
        <m.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Button2
            type="button"
            variant="ghost"
            size="sm"
            onClick={onClearAll}
            className="flex items-center space-x-1 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            <Trash2 className="h-3 w-3" />
            <span>Clear All</span>
          </Button2>
        </m.div>
      )}
    </m.div>
  );
}

/**
 * Utility function to remove a rule from a search group
 */
export function removeRuleFromQuery(query: SearchGroup, ruleId: string): SearchGroup {
  // Remove from current level
  const updatedRules = query.rules.filter(rule => rule.id !== ruleId);
  
  // Recursively remove from nested groups
  const updatedGroups = query.groups?.map(group =>
    removeRuleFromQuery(group, ruleId),
  ).filter(group =>
    // Remove empty groups
    group.rules.length > 0 || (group.groups && group.groups.length > 0),
  );
  
  return {
    ...query,
    rules: updatedRules,
    groups: updatedGroups,
  };
}

/**
 * Utility function to find a rule in a search group
 */
export function findRuleInQuery(query: SearchGroup, ruleId: string): SearchRule | null {
  // Check current level
  const rule = query.rules.find(r => r.id === ruleId);
  if (rule) return rule;
  
  // Check nested groups
  if (query.groups) {
    for (const group of query.groups) {
      const found = findRuleInQuery(group, ruleId);
      if (found) return found;
    }
  }
  
  return null;
}
