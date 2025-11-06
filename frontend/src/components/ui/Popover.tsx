
import { Popover as HeadlessPopover, Transition } from '@headlessui/react';
import React, { Fragment } from 'react';

import { cn } from '@/lib/utils';

export function Popover({ children, open, onOpenChange }: { children: React.ReactNode; open: boolean; onOpenChange: (open: boolean) => void }) {
  return (
    <HeadlessPopover open={open} onChange={onOpenChange} as="div" className="relative">
      {children}
    </HeadlessPopover>
  );
}

export function PopoverTrigger({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
  if (asChild && React.isValidElement(children)) {
    return <HeadlessPopover.Button as={Fragment}>{children}</HeadlessPopover.Button>;
  }
  return <HeadlessPopover.Button>{children}</HeadlessPopover.Button>;
}

export function PopoverContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <Transition
      as={Fragment}
      enter="transition ease-out duration-200"
      enterFrom="opacity-0 translate-y-1"
      enterTo="opacity-100 translate-y-0"
      leave="transition ease-in duration-150"
      leaveFrom="opacity-100 translate-y-0"
      leaveTo="opacity-0 translate-y-1"
    >
      <HeadlessPopover.Panel
        className={cn(
          'absolute z-50 mt-2 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none',
          className,
        )}
      >
        {children}
      </HeadlessPopover.Panel>
    </Transition>
  );
}
