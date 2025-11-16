/**
 * RuleEditor Component
 * 
 * Edits a single search rule with field-specific operators and value inputs.
 */

'use client';

import { Trash2, AlertCircle } from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';

import Button2 from '@/components/ui/Button2';
import Card2, { CardContent } from '@/components/ui/Card2';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import { fadeVariants } from '@/lib/animations';
import { m } from '@/lib/motion';
import type { SearchRule, SearchField, SearchOperator, FieldType } from '@/types/search';

export interface RuleEditorProps {
  /** The rule being edited */
  rule: SearchRule;

  /** Available fields */
  fields: SearchField[];

  /** Callback when rule changes */
  onChange: (rule: SearchRule) => void;

  /** Callback when rule should be deleted */
  onDelete: () => void;

  /** Whether the editor is disabled */
  disabled?: boolean;

  /** Custom class name */
  className?: string;
}

/**
 * Get operators for a specific field type
 */
function getOperatorsForFieldType(type: FieldType): SearchOperator[] {
  switch (type) {
    case 'text':
      return ['contains', 'equals', 'startsWith', 'endsWith', 'isEmpty', 'isNotEmpty'];
    case 'number':
      return ['equals', 'gt', 'gte', 'lt', 'lte', 'between', 'isEmpty', 'isNotEmpty'];
    case 'date':
      return ['before', 'after', 'between', 'inLastDays', 'inNextDays', 'isEmpty', 'isNotEmpty'];
    case 'boolean':
      return ['is', 'isNot'];
    case 'select':
    case 'multiselect':
      return ['equals', 'in', 'notIn', 'isEmpty', 'isNotEmpty'];
    default:
      return ['equals'];
  }
}

/**
 * Get human-readable label for an operator
 */
function getOperatorLabel(operator: SearchOperator): string {
  const labels: Record<string, string> = {
    contains: 'contains',
    equals: 'equals',
    startsWith: 'starts with',
    endsWith: 'ends with',
    isEmpty: 'is empty',
    isNotEmpty: 'is not empty',
    gt: 'greater than',
    gte: 'greater than or equal',
    lt: 'less than',
    lte: 'less than or equal',
    between: 'between',
    before: 'before',
    after: 'after',
    inLastDays: 'in last X days',
    inNextDays: 'in next X days',
    is: 'is',
    isNot: 'is not',
    in: 'is one of',
    notIn: 'is not one of',
  };
  return labels[operator] || operator;
}

/**
 * Check if operator requires a value input
 */
function operatorNeedsValue(operator: SearchOperator): boolean {
  return !['isEmpty', 'isNotEmpty'].includes(operator);
}

/**
 * Check if operator requires two value inputs (e.g., between)
 */
function operatorNeedsTwoValues(operator: SearchOperator): boolean {
  return ['between'].includes(operator);
}

/**
 * Validate rule value based on field type and operator
 */
function validateRuleValue(rule: SearchRule, field: SearchField): string | null {
  if (!operatorNeedsValue(rule.operator)) {
    return null; // No value needed
  }

  if (!rule.value && rule.value !== 0 && rule.value !== false) {
    return 'Value is required';
  }

  // Type-specific validation
  switch (field.type) {
    case 'number':
      if (isNaN(Number(rule.value))) {
        return 'Must be a valid number';
      }
      if (operatorNeedsTwoValues(rule.operator)) {
        if (!rule.value2 && rule.value2 !== 0) {
          return 'Second value is required';
        }
        if (isNaN(Number(rule.value2))) {
          return 'Second value must be a valid number';
        }
        if (Number(rule.value) >= Number(rule.value2)) {
          return 'First value must be less than second value';
        }
      }
      break;

    case 'date':
      if (rule.operator === 'inLastDays' || rule.operator === 'inNextDays') {
        if (isNaN(Number(rule.value)) || Number(rule.value) < 1) {
          return 'Must be a positive number';
        }
      } else if (operatorNeedsTwoValues(rule.operator)) {
        if (!rule.value2) {
          return 'Second date is required';
        }
        if (new Date(rule.value) >= new Date(rule.value2)) {
          return 'Start date must be before end date';
        }
      }
      break;

    case 'select':
      if (field.options && !field.options.find(opt => opt.value === rule.value)) {
        return 'Invalid selection';
      }
      break;

    case 'multiselect':
      if (!Array.isArray(rule.value) || rule.value.length === 0) {
        return 'At least one option must be selected';
      }
      break;
  }

  return null;
}

/**
 * RuleEditor Component
 */
export function RuleEditor({
  rule,
  fields,
  onChange,
  onDelete,
  disabled = false,
  className = '',
}: RuleEditorProps) {
  const [validationError, setValidationError] = useState<string | null>(null);

  // Find the current field definition
  const currentField = useMemo(
    () => fields.find(f => f.name === rule.field) || fields[0],
    [fields, rule.field],
  );

  // Get available operators for current field
  const availableOperators = useMemo(
    () => currentField ? (currentField.operators || getOperatorsForFieldType(currentField.type)) : [],
    [currentField],
  );

  // Validate on changes
  useEffect(() => {
    if (currentField) {
      const error = validateRuleValue(rule, currentField);
      setValidationError(error);
    }
  }, [rule, currentField]);

  const handleFieldChange = (fieldName: string) => {
    const newField = fields.find(f => f.name === fieldName);
    if (!newField) return;

    const newOperators = newField.operators || getOperatorsForFieldType(newField.type);
    const newOperator = newOperators[0] as SearchOperator;

    onChange({
      ...rule,
      field: fieldName,
      operator: newOperator,
      value: '',
      value2: undefined,
    });
  };

  const handleOperatorChange = (operator: SearchOperator) => {
    onChange({
      ...rule,
      operator,
      value: operatorNeedsValue(operator) ? rule.value : '',
      value2: operatorNeedsTwoValues(operator) ? rule.value2 : undefined,
    });
  };

  const handleValueChange = (value: any) => {
    onChange({
      ...rule,
      value,
    });
  };

  const handleValue2Change = (value2: any) => {
    onChange({
      ...rule,
      value2,
    });
  };

  const needsValue = operatorNeedsValue(rule.operator);
  const needsTwoValues = operatorNeedsTwoValues(rule.operator);

  return (
    <m.div
      className={className}
      variants={fadeVariants}
      initial="hidden"
      animate="visible"
    >
      <Card2 className="bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700">
        <CardContent className="p-3">
          <div className="flex items-start space-x-2">
            {/* Field Selector */}
            <div className="flex-1 min-w-0">
              <Select
                value={rule.field}
                onChange={(e) => handleFieldChange(e.target.value)}
                disabled={disabled}
                options={fields.map(field => ({
                  value: field.name,
                  label: field.label,
                }))}
                className="text-sm"
              />
            </div>

            {/* Operator Selector */}
            <div className="flex-1 min-w-0">
              <Select
                value={rule.operator}
                onChange={(e) => handleOperatorChange(e.target.value as SearchOperator)}
                disabled={disabled}
                options={availableOperators.map(op => ({
                  value: op,
                  label: getOperatorLabel(op),
                }))}
                className="text-sm"
              />
            </div>

            {/* Value Input(s) */}
            {needsValue && (
              <>
                <div className="flex-1 min-w-0">
                  <ValueInput
                    field={currentField}
                    operator={rule.operator}
                    value={rule.value}
                    onChange={handleValueChange}
                    disabled={disabled}
                  />
                </div>

                {needsTwoValues && (
                  <>
                    <span className="text-sm text-neutral-500 dark:text-neutral-400 self-center">and</span>
                    <div className="flex-1 min-w-0">
                      <ValueInput
                        field={currentField}
                        operator={rule.operator}
                        value={rule.value2}
                        onChange={handleValue2Change}
                        disabled={disabled}
                      />
                    </div>
                  </>
                )}
              </>
            )}

            {/* Delete Button */}
            <Button2
              type="button"
              variant="ghost"
              size="sm"
              onClick={onDelete}
              disabled={disabled}
              className="flex-shrink-0 text-red-500 hover:text-red-700 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
              aria-label="Delete rule"
            >
              <Trash2 className="h-4 w-4" />
            </Button2>
          </div>

          {/* Validation Error */}
          {validationError && (
            <m.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-2 flex items-center space-x-1 text-xs text-red-600 dark:text-red-400"
            >
              <AlertCircle className="h-3 w-3 flex-shrink-0" />
              <span>{validationError}</span>
            </m.div>
          )}

          {/* Help Text */}
          {currentField?.helpText && !validationError && (
            <m.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-2 text-xs text-neutral-500 dark:text-neutral-400"
            >
              {currentField.helpText}
            </m.div>
          )}
        </CardContent>
      </Card2>
    </m.div>
  );
}

/**
 * ValueInput Component - Renders appropriate input based on field type
 */
interface ValueInputProps {
  field: SearchField;
  operator: SearchOperator;
  value: any;
  onChange: (value: any) => void;
  disabled?: boolean;
}

function ValueInput({ field, operator, value, onChange, disabled }: ValueInputProps) {
  switch (field.type) {
    case 'text':
      return (
        <Input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}...`}
          className="text-sm"
        />
      );

    case 'number':
      if (operator === 'inLastDays' || operator === 'inNextDays') {
        return (
          <Input
            type="number"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder="Number of days"
            min="1"
            className="text-sm"
          />
        );
      }
      return (
        <Input
          type="number"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder={field.placeholder || 'Enter number...'}
          className="text-sm"
        />
      );

    case 'date':
      if (operator === 'inLastDays' || operator === 'inNextDays') {
        return (
          <Input
            type="number"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder="Number of days"
            min="1"
            className="text-sm"
          />
        );
      }
      return (
        <Input
          type="date"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className="text-sm"
        />
      );

    case 'boolean':
      return (
        <Select
          value={value === true ? 'true' : value === false ? 'false' : ''}
          onChange={(e) => onChange(e.target.value === 'true')}
          disabled={disabled}
          options={[
            { value: 'true', label: 'True' },
            { value: 'false', label: 'False' },
          ]}
          className="text-sm"
        />
      );

    case 'select':
      return (
        <Select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          options={field.options || []}
          className="text-sm"
        />
      );

    case 'multiselect':
      // For multiselect, we'll use a simple comma-separated input for now
      // In a real implementation, you'd use a proper multiselect component
      return (
        <Input
          type="text"
          value={Array.isArray(value) ? value.join(', ') : ''}
          onChange={(e) => onChange(e.target.value.split(',').map(v => v.trim()).filter(Boolean))}
          disabled={disabled}
          placeholder="Enter values separated by commas..."
          className="text-sm"
        />
      );

    default:
      return (
        <Input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder={field.placeholder || 'Enter value...'}
          className="text-sm"
        />
      );
  }
}
