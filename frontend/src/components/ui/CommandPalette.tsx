
import { Command } from 'cmdk';
import React from 'react';

import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut';
import { commandCategories } from '@/lib/commands';

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);

  useKeyboardShortcut(() => setOpen((open) => !open), 'k');

  return (
    <Command.Dialog open={open} onOpenChange={setOpen} label="Command Menu">
      <Command.Input />
      <Command.List>
        <Command.Empty>No results found.</Command.Empty>
        {commandCategories.map((category) => (
          <Command.Group key={category.name} heading={category.name}>
            {category.commands.map((command) => (
              <Command.Item
                key={command.id}
                onSelect={command.action}
                keywords={command.keywords}
              >
                <command.icon className="mr-2 h-4 w-4" />
                {command.label}
              </Command.Item>
            ))}
          </Command.Group>
        ))}
      </Command.List>
    </Command.Dialog>
  );
}
