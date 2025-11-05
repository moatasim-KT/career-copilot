
import React, { useState } from 'react';
import { format } from 'date-fns';
import { Calendar as CalendarIcon } from 'lucide-react';
import { DayPicker } from 'react-day-picker';
import 'react-day-picker/dist/style.css';

import { cn } from '@/lib/utils';
import { Button } from './Button';
import { Popover, PopoverContent, PopoverTrigger } from './Popover'; // Assuming Popover components exist

export interface DatePickerProps {
  /** The selected date */
  date?: Date;
  /** Callback function when date changes */
  onSelect?: (date: Date | undefined) => void;
  /** Optional label for the date picker */
  label?: string;
  /** Optional error message to display */
  error?: string;
  /** Placeholder text */
  placeholder?: string;
  /** Whether the date picker is disabled */
  disabled?: boolean;
}

export default function DatePicker({
  date,
  onSelect,
  label,
  error,
  placeholder = 'Pick a date',
  disabled,
}: DatePickerProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="grid w-full items-center gap-1.5">
      {label && (
        <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          {label}
        </label>
      )}
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button
            variant={"outline"}
            className={cn(
              "w-full justify-start text-left font-normal",
              !date && "text-muted-foreground",
              error && "border-red-500",
            )}
            disabled={disabled}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date ? format(date, "PPP") : <span>{placeholder}</span>}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0">
          <DayPicker
            mode="single"
            selected={date}
            onSelect={(newDate) => {
              onSelect?.(newDate);
              setIsOpen(false);
            }}
            initialFocus
          />
        </PopoverContent>
      </Popover>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
