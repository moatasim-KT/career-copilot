/**
 * QueryBuilder Component
 * 
 * A visual query builder for constructing complex search queries with
 * nested groups, multiple rules, and AND/OR logic.
 */

'use client';

import { Plus, Trash2, Layers } from 'lucide-react';
import { useState, useCallback } from 'react';

import Button2 from '@/components/ui/Button2';
import Card, { CardContent } from '@/components/ui/Card2';
import { fadeVariants, slideVariants, springConfigs } from '@/lib/animations';
import { m, AnimatePresence } from '@/lib/motion';
import type { SearchGroup, SearchRule, SearchField, LogicOperator, SearchOperator } from '@/types/search';

import { RuleEditor } from './RuleEditor';

export interface QueryBuilderProps {
  /** Current query structure */
  query: SearchGroup;

  /** Callback when query changes */
  onChange: (query: SearchGroup) => void;

  /** Available fields for searching */
  fields: SearchField[];

  /** Whether the builder is disabled */
  disabled?: boolean;

  /** Maximum nesting depth (default: 3) */
  maxDepth?: number;

  /** Current nesting depth (internal) */
  depth?: number;

  /** Custom class name */
  className?: string;
}

/**
 * Generate a unique ID for rules and groups
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Create a new empty rule
 */
function createEmptyRule(fields: SearchField[]): SearchRule {
  const firstField = fields[0];
  return {
    id: generateId(),
    field: firstField?.name || '',
    operator: (firstField?.defaultOperator || firstField?.operators[0] || 'equals') as SearchOperator,
    value: '',
  };
}

/**
 * Create a new empty group
 */
function createEmptyGroup(): SearchGroup {
  return {
    id: generateId(),
    logic: 'AND',
    rules: [],
    groups: [],
  };
}

/**
 * QueryBuilder Component
 */
export function QueryBuilder({
  query,
  onChange,
  fields,
  disabled = false,
  maxDepth = 3,
  depth = 0,
  className = '',
}: QueryBuilderProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set([query.id]));

  const toggleGroupExpanded = useCallback((groupId: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  }, []);

  const handleLogicChange = useCallback((logic: LogicOperator) => {
    onChange({ ...query, logic });
  }, [query, onChange]);

  const handleAddRule = useCallback(() => {
    const newRule = createEmptyRule(fields);
    onChange({
      ...query,
      rules: [...query.rules, newRule],
    });
  }, [query, fields, onChange]);

  const handleAddGroup = useCallback(() => {
    const newGroup = createEmptyGroup();
    onChange({
      ...query,
      groups: [...(query.groups || []), newGroup],
    });
    // Auto-expand the new group
    setExpandedGroups(prev => new Set(prev).add(newGroup.id));
  }, [query, onChange]);

  const handleUpdateRule = useCallback((ruleId: string, updatedRule: SearchRule) => {
    onChange({
      ...query,
      rules: query.rules.map(rule => rule.id === ruleId ? updatedRule : rule),
    });
  }, [query, onChange]);

  const handleDeleteRule = useCallback((ruleId: string) => {
    onChange({
      ...query,
      rules: query.rules.filter(rule => rule.id !== ruleId),
    });
  }, [query, onChange]);

  const handleUpdateGroup = useCallback((groupId: string, updatedGroup: SearchGroup) => {
    onChange({
      ...query,
      groups: (query.groups || []).map(group => group.id === groupId ? updatedGroup : group),
    });
  }, [query, onChange]);

  const handleDeleteGroup = useCallback((groupId: string) => {
    onChange({
      ...query,
      groups: (query.groups || []).filter(group => group.id !== groupId),
    });
  }, [query, onChange]);

  const isExpanded = expandedGroups.has(query.id);
  const canAddGroup = depth < maxDepth;
  const hasContent = query.rules.length > 0 || (query.groups && query.groups.length > 0);

  // Indentation based on depth
  const indentClass = depth > 0 ? 'ml-6 pl-4 border-l-2 border-neutral-300 dark:border-neutral-700' : '';

  return (
    <m.div
      className={`${className} ${indentClass}`}
      initial="hidden"
      animate="visible"
      variants={fadeVariants}
    >
      <Card className={`${depth > 0 ? 'bg-neutral-50 dark:bg-neutral-900' : ''}`}>
        <CardContent className="p-4">
          {/* Group Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              {depth > 0 && (
                <button
                  type="button"
                  onClick={() => toggleGroupExpanded(query.id)}
                  className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors"
                  aria-label={isExpanded ? 'Collapse group' : 'Expand group'}
                >
                  <m.div
                    animate={{ rotate: isExpanded ? 90 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </m.div>
                </button>
              )}

              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  {depth === 0 ? 'Search Criteria' : 'Group'}
                </span>
                {hasContent && (
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    ({query.rules.length} rule{query.rules.length !== 1 ? 's' : ''}
                    {query.groups && query.groups.length > 0 && `, ${query.groups.length} group${query.groups.length !== 1 ? 's' : ''}`})
                  </span>
                )}
              </div>

              {/* Logic Toggle */}
              {hasContent && (
                <div className="flex items-center space-x-1 bg-neutral-100 dark:bg-neutral-800 rounded-md p-1">
                  <button
                    type="button"
                    onClick={() => handleLogicChange('AND')}
                    disabled={disabled}
                    className={`
                      px-3 py-1 text-xs font-medium rounded transition-colors
                      ${query.logic === 'AND'
                        ? 'bg-blue-600 text-white'
                        : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700'
                      }
                      ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    AND
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLogicChange('OR')}
                    disabled={disabled}
                    className={`
                      px-3 py-1 text-xs font-medium rounded transition-colors
                      ${query.logic === 'OR'
                        ? 'bg-blue-600 text-white'
                        : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700'
                      }
                      ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    OR
                  </button>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2">
              <Button2
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddRule}
                disabled={disabled}
                className="flex items-center space-x-1"
              >
                <Plus className="h-3 w-3" />
                <span>Rule</span>
              </Button2>

              {canAddGroup && (
                <Button2
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddGroup}
                  disabled={disabled}
                  className="flex items-center space-x-1"
                >
                  <Layers className="h-3 w-3" />
                  <span>Group</span>
                </Button2>
              )}
            </div>
          </div>

          {/* Group Content */}
          <AnimatePresence>
            {isExpanded && (
              <m.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-3"
              >
                {/* Rules */}
                <AnimatePresence mode="popLayout">
                  {query.rules.map((rule, index) => (
                    <m.div
                      key={rule.id}
                      variants={slideVariants.up}
                      initial="hidden"
                      animate="visible"
                      exit={{
                        opacity: 0,
                        x: -20,
                        transition: { duration: 0.2 },
                      }}
                      layout
                      transition={springConfigs.gentle}
                    >
                      <div className="flex items-start space-x-2">
                        {/* Logic Indicator */}
                        {index > 0 && (
                          <div className="flex-shrink-0 mt-3">
                            <span className="inline-block px-2 py-1 text-xs font-medium bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded">
                              {query.logic}
                            </span>
                          </div>
                        )}

                        {/* Rule Editor */}
                        <div className="flex-1">
                          <RuleEditor
                            rule={rule}
                            fields={fields}
                            onChange={(updatedRule) => handleUpdateRule(rule.id, updatedRule)}
                            onDelete={() => handleDeleteRule(rule.id)}
                            disabled={disabled}
                          />
                        </div>
                      </div>
                    </m.div>
                  ))}
                </AnimatePresence>

                {/* Nested Groups */}
                <AnimatePresence mode="popLayout">
                  {query.groups && query.groups.map((group, index) => (
                    <m.div
                      key={group.id}
                      variants={slideVariants.up}
                      initial="hidden"
                      animate="visible"
                      exit={{
                        opacity: 0,
                        x: -20,
                        transition: { duration: 0.2 },
                      }}
                      layout
                      transition={springConfigs.gentle}
                    >
                      <div className="flex items-start space-x-2">
                        {/* Logic Indicator */}
                        {(query.rules.length > 0 || index > 0) && (
                          <div className="flex-shrink-0 mt-3">
                            <span className="inline-block px-2 py-1 text-xs font-medium bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded">
                              {query.logic}
                            </span>
                          </div>
                        )}

                        {/* Nested Query Builder */}
                        <div className="flex-1 relative">
                          <QueryBuilder
                            query={group}
                            onChange={(updatedGroup) => handleUpdateGroup(group.id, updatedGroup)}
                            fields={fields}
                            disabled={disabled}
                            maxDepth={maxDepth}
                            depth={depth + 1}
                          />

                          {/* Delete Group Button */}
                          <button
                            type="button"
                            onClick={() => handleDeleteGroup(group.id)}
                            disabled={disabled}
                            className="absolute top-2 right-2 p-1 text-red-500 hover:text-red-700 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                            aria-label="Delete group"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </m.div>
                  ))}
                </AnimatePresence>

                {/* Empty State */}
                {!hasContent && (
                  <m.div
                    variants={fadeVariants}
                    initial="hidden"
                    animate="visible"
                    className="text-center py-8 text-neutral-500 dark:text-neutral-400"
                  >
                    <p className="text-sm">No search criteria defined</p>
                    <p className="text-xs mt-1">Click &quot;Rule&quot; to add a search condition</p>
                  </m.div>
                )}
              </m.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </m.div>
  );
}
