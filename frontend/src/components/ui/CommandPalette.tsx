import React from 'react';
import { Command } from 'cmdk';
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut';
import { commandCategories } from '@/lib/commands';
import { useQuery } from '@tanstack/react-query';
import { Briefcase, FileText, History, Trash2 } from 'lucide-react';

// Mock data for jobs and applications
const mockJobs = [
  { id: 1, title: 'Software Engineer', company: 'Google', description: '...' },
  { id: 2, title: 'Frontend Developer', company: 'Facebook', description: '...' },
  { id: 3, title: 'Backend Developer', company: 'Amazon', description: '...' },
];

const mockApplications = [
  { id: 1, job: mockJobs[0], notes: 'Applied on 2023-01-01' },
  { id: 2, job: mockJobs[1], notes: 'Applied on 2023-01-05' },
];

// TODO: Replace with actual API client once .gitignore issue is resolved
const apiClient = {
  getJobs: async () => mockJobs,
  getApplications: async () => mockApplications,
};

const RECENT_SEARCHES_KEY = 'command-palette-recent-searches';

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState('');
  const [recentSearches, setRecentSearches] = React.useState<string[]>([]);

  useKeyboardShortcut(() => setOpen((open) => !open), 'k');

  React.useEffect(() => {
    const storedSearches = localStorage.getItem(RECENT_SEARCHES_KEY);
    if (storedSearches) {
      setRecentSearches(JSON.parse(storedSearches));
    }
  }, []);

  const addRecentSearch = (newSearch: string) => {
    setRecentSearches((prevSearches) => {
      const updatedSearches = [
        newSearch,
        ...prevSearches.filter((s) => s !== newSearch),
      ].slice(0, 10); // Keep last 10 searches
      localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updatedSearches));
      return updatedSearches;
    });
  };

  const clearRecentSearches = () => {
    localStorage.removeItem(RECENT_SEARCHES_KEY);
    setRecentSearches([]);
  };

  const { data: jobs } = useQuery({
    queryKey: ['jobs'],
    queryFn: apiClient.getJobs,
  });

  const { data: applications } = useQuery({
    queryKey: ['applications'],
    queryFn: apiClient.getApplications,
  });

  const filteredJobs = React.useMemo(() => {
    if (!jobs) return [];
    return jobs.filter((job) =>
      job.title.toLowerCase().includes(search.toLowerCase()) ||
      job.company.toLowerCase().includes(search.toLowerCase())
    );
  }, [jobs, search]);

  const filteredApplications = React.useMemo(() => {
    if (!applications) return [];
    return applications.filter((application) =>
      application.job.title.toLowerCase().includes(search.toLowerCase()) ||
      application.job.company.toLowerCase().includes(search.toLowerCase())
    );
  }, [applications, search]);

  return (
    <Command.Dialog open={open} onOpenChange={setOpen} label="Command Menu">
      <Command.Input
        value={search}
        onValueChange={setSearch}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && search.trim() !== '') {
            addRecentSearch(search.trim());
          }
        }}
      />
      <Command.List>
        <Command.Empty>No results found.</Command.Empty>

        {recentSearches.length > 0 && search === '' && (
          <Command.Group heading="Recent Searches">
            {recentSearches.map((recentSearch) => (
              <Command.Item
                key={recentSearch}
                onSelect={() => {
                  setSearch(recentSearch);
                  setOpen(false);
                }}
              >
                <History className="mr-2 h-4 w-4" />
                {recentSearch}
              </Command.Item>
            ))}
            <Command.Item onSelect={clearRecentSearches}>
              <Trash2 className="mr-2 h-4 w-4" />
              Clear all recent searches
            </Command.Item>
          </Command.Group>
        )}

        {commandCategories.map((category) => (
          <Command.Group key={category.name} heading={category.name}>
            {category.commands.map((command) => (
              <Command.Item
                key={command.id}
                onSelect={() => {
                  command.action();
                  addRecentSearch(command.label);
                }}
                keywords={command.keywords}
              >
                <command.icon className="mr-2 h-4 w-4" />
                {command.label}
              </Command.Item>
            ))}
          </Command.Group>
        ))}
        {filteredJobs.length > 0 && (
          <Command.Group heading="Jobs">
            {filteredJobs.map((job) => (
              <Command.Item
                key={job.id}
                onSelect={() => {
                  window.location.href = `/jobs/${job.id}`;
                  addRecentSearch(`${job.title} at ${job.company}`);
                }}
              >
                <Briefcase className="mr-2 h-4 w-4" />
                {job.title} at {job.company}
              </Command.Item>
            ))}
          </Command.Group>
        )}
        {filteredApplications.length > 0 && (
          <Command.Group heading="Applications">
            {filteredApplications.map((application) => (
              <Command.Item
                key={application.id}
                onSelect={() => {
                  window.location.href = `/applications/${application.id}`;
                  addRecentSearch(
                    `${application.job.title} (${application.job.company})`
                  );
                }}
              >
                <FileText className="mr-2 h-4 w-4" />
                {application.job.title} ({application.job.company})
              </Command.Item>
            ))}
          </Command.Group>
        )}
      </Command.List>
    </Command.Dialog>
  );
}