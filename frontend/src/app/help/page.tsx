/**
 * Help Center Page
 * 
 * Comprehensive help documentation with searchable FAQ,
 * organized by categories, and links to video tutorials.
 * 
 * Categories:
 * - Getting Started
 * - Features
 * - Troubleshooting
 * - Account & Settings
 * - Privacy & Security
 */

'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Lightbulb,
  AlertCircle,
  Settings,
  Shield,
  Video,
  ExternalLink,
  Mail,
  MessageCircle,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Card2 } from '@/components/ui/Card2';
import { FeatureTour, useFeatureTour } from '@/components/help/FeatureTour';

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
  keywords: string[];
}

interface Category {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const categories: Category[] = [
  {
    id: 'getting-started',
    name: 'Getting Started',
    icon: BookOpen,
    description: 'Learn the basics and set up your account',
  },
  {
    id: 'features',
    name: 'Features',
    icon: Lightbulb,
    description: 'Explore all the features and capabilities',
  },
  {
    id: 'troubleshooting',
    name: 'Troubleshooting',
    icon: AlertCircle,
    description: 'Solve common issues and errors',
  },
  {
    id: 'account-settings',
    name: 'Account & Settings',
    icon: Settings,
    description: 'Manage your account and preferences',
  },
  {
    id: 'privacy-security',
    name: 'Privacy & Security',
    icon: Shield,
    description: 'Learn about data protection and security',
  },
];

const faqItems: FAQItem[] = [
  // Getting Started
  {
    id: 'gs-1',
    question: 'How do I get started with Career Copilot?',
    answer:
      'After signing up, you\'ll be guided through a quick onboarding process where you can set up your profile, add your skills, upload your resume, and set job preferences. You can also take the feature tour to learn about key features.',
    category: 'getting-started',
    keywords: ['onboarding', 'setup', 'start', 'begin', 'new user'],
  },
  {
    id: 'gs-2',
    question: 'How do I upload my resume?',
    answer:
      'Go to your Profile settings and click on "Upload Resume". We support PDF and DOCX formats. Our AI will automatically extract your skills and experience to help match you with relevant jobs.',
    category: 'getting-started',
    keywords: ['resume', 'upload', 'cv', 'document', 'pdf'],
  },
  {
    id: 'gs-3',
    question: 'How do I add my skills?',
    answer:
      'Navigate to your Profile settings and find the Skills section. You can search for skills from our database or add custom skills. You can also set proficiency levels for each skill.',
    category: 'getting-started',
    keywords: ['skills', 'expertise', 'proficiency', 'add'],
  },

  // Features
  {
    id: 'f-1',
    question: 'What is the Command Palette?',
    answer:
      'The Command Palette is a powerful search tool that lets you quickly navigate to any page, search for jobs and applications, and execute actions. Press ⌘K (Mac) or Ctrl+K (Windows) to open it.',
    category: 'features',
    keywords: ['command palette', 'keyboard', 'shortcut', 'search', 'navigation'],
  },
  {
    id: 'f-2',
    question: 'How does Advanced Search work?',
    answer:
      'Advanced Search lets you build complex queries using AND/OR logic. You can combine multiple filters, save searches for later, and export results. Click the "Advanced Search" button on the Jobs or Applications page to get started.',
    category: 'features',
    keywords: ['advanced search', 'filters', 'query', 'search'],
  },
  {
    id: 'f-3',
    question: 'How do I track my applications?',
    answer:
      'All your applications are tracked on the Applications page. You can view them in table or Kanban board format, update statuses by dragging cards, add notes, set reminders, and export your application history.',
    category: 'features',
    keywords: ['applications', 'tracking', 'status', 'kanban', 'manage'],
  },
  {
    id: 'f-4',
    question: 'What are bulk operations?',
    answer:
      'Bulk operations let you perform actions on multiple items at once. Select items using checkboxes, and a toolbar will appear at the bottom with available actions like changing status, archiving, or exporting.',
    category: 'features',
    keywords: ['bulk', 'multiple', 'batch', 'operations', 'actions'],
  },
  {
    id: 'f-5',
    question: 'How do notifications work?',
    answer:
      'You\'ll receive notifications for new job matches, application updates, and reminders. You can customize notification preferences in Settings and enable browser push notifications for real-time updates.',
    category: 'features',
    keywords: ['notifications', 'alerts', 'push', 'updates'],
  },

  // Troubleshooting
  {
    id: 't-1',
    question: 'Why am I not receiving notifications?',
    answer:
      'Check your notification preferences in Settings. Make sure notifications are enabled for the categories you want. If using browser push notifications, ensure you\'ve granted permission in your browser settings.',
    category: 'troubleshooting',
    keywords: ['notifications', 'not working', 'missing', 'push'],
  },
  {
    id: 't-2',
    question: 'Why can\'t I see my uploaded resume?',
    answer:
      'Make sure you uploaded a supported format (PDF or DOCX) and the file size is under 10MB. If the upload failed, try again or contact support if the issue persists.',
    category: 'troubleshooting',
    keywords: ['resume', 'upload', 'failed', 'not showing'],
  },
  {
    id: 't-3',
    question: 'The application is running slowly. What can I do?',
    answer:
      'Try clearing your browser cache and cookies. Make sure you\'re using a modern browser (Chrome, Firefox, Safari, or Edge). If you have many browser extensions, try disabling them temporarily.',
    category: 'troubleshooting',
    keywords: ['slow', 'performance', 'lag', 'loading'],
  },
  {
    id: 't-4',
    question: 'I\'m getting an error message. What should I do?',
    answer:
      'Most errors are temporary. Try refreshing the page or logging out and back in. If the error persists, take a screenshot and contact support with details about what you were doing when the error occurred.',
    category: 'troubleshooting',
    keywords: ['error', 'bug', 'issue', 'problem', 'crash'],
  },

  // Account & Settings
  {
    id: 'as-1',
    question: 'How do I change my password?',
    answer:
      'Go to Settings > Account and click "Change Password". You\'ll need to enter your current password and then your new password twice to confirm.',
    category: 'account-settings',
    keywords: ['password', 'change', 'reset', 'security'],
  },
  {
    id: 'as-2',
    question: 'How do I enable dark mode?',
    answer:
      'Click the theme toggle button in the navigation bar (sun/moon icon) or go to Settings > Appearance. You can choose Light, Dark, or System (follows your device preference).',
    category: 'account-settings',
    keywords: ['dark mode', 'theme', 'appearance', 'light', 'dark'],
  },
  {
    id: 'as-3',
    question: 'Can I customize the dashboard layout?',
    answer:
      'Yes! You can drag and drop widgets to reorder them on your dashboard. Your layout is automatically saved. You can also reset to the default layout in Settings.',
    category: 'account-settings',
    keywords: ['dashboard', 'customize', 'layout', 'widgets', 'drag'],
  },
  {
    id: 'as-4',
    question: 'How do I export my data?',
    answer:
      'Go to Settings > Data and click "Export Data". You can export specific data types (applications, jobs) as CSV or PDF, or export all your data as a JSON backup file.',
    category: 'account-settings',
    keywords: ['export', 'download', 'backup', 'data', 'csv', 'pdf'],
  },

  // Privacy & Security
  {
    id: 'ps-1',
    question: 'How is my data protected?',
    answer:
      'We use industry-standard encryption for data in transit (HTTPS) and at rest. Your data is stored securely and never shared with third parties without your explicit consent.',
    category: 'privacy-security',
    keywords: ['privacy', 'security', 'encryption', 'data protection'],
  },
  {
    id: 'ps-2',
    question: 'Can I delete my account?',
    answer:
      'Yes, you can delete your account in Settings > Data. This action cannot be undone and will permanently delete all your data after a 30-day grace period.',
    category: 'privacy-security',
    keywords: ['delete', 'account', 'remove', 'close'],
  },
  {
    id: 'ps-3',
    question: 'Who can see my profile and applications?',
    answer:
      'Your data is private by default. Only you can see your profile, applications, and saved jobs. We do not share your information with employers unless you explicitly apply to a job.',
    category: 'privacy-security',
    keywords: ['privacy', 'visibility', 'profile', 'who can see'],
  },
];

const videoTutorials = [
  {
    id: 'v-1',
    title: 'Getting Started with Career Copilot',
    duration: '5:30',
    thumbnail: '/images/tutorials/getting-started.jpg',
    url: '#',
  },
  {
    id: 'v-2',
    title: 'Using the Command Palette',
    duration: '3:15',
    thumbnail: '/images/tutorials/command-palette.jpg',
    url: '#',
  },
  {
    id: 'v-3',
    title: 'Advanced Search Techniques',
    duration: '7:45',
    thumbnail: '/images/tutorials/advanced-search.jpg',
    url: '#',
  },
  {
    id: 'v-4',
    title: 'Tracking Applications Effectively',
    duration: '6:20',
    thumbnail: '/images/tutorials/tracking-applications.jpg',
    url: '#',
  },
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const { isOpen, openTour, closeTour, completeTour } = useFeatureTour();

  // Filter FAQ items based on search and category
  const filteredFAQs = useMemo(() => {
    let filtered = faqItems;

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter((item) => item.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (item) =>
          item.question.toLowerCase().includes(query) ||
          item.answer.toLowerCase().includes(query) ||
          item.keywords.some((keyword) => keyword.toLowerCase().includes(query))
      );
    }

    return filtered;
  }, [searchQuery, selectedCategory]);

  const toggleItem = (id: string) => {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(selectedCategory === categoryId ? null : categoryId);
  };

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
      {/* Header */}
      <div className="bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-neutral-900 dark:text-neutral-100 mb-4">
              Help Center
            </h1>
            <p className="text-lg text-neutral-600 dark:text-neutral-400 mb-8">
              Find answers to common questions and learn how to use Career Copilot
            </p>

            {/* Search Bar */}
            <div className="max-w-2xl mx-auto">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-400" />
                <input
                  type="text"
                  placeholder="Search for help..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={cn(
                    'w-full pl-12 pr-4 py-3 rounded-lg',
                    'bg-neutral-50 dark:bg-neutral-900',
                    'border border-neutral-300 dark:border-neutral-600',
                    'text-neutral-900 dark:text-neutral-100',
                    'placeholder-neutral-500 dark:placeholder-neutral-400',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500',
                    'transition-colors',
                  )}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-4 space-y-6">
              {/* Categories */}
              <Card2 className="p-4">
                <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-3">
                  Categories
                </h2>
                <div className="space-y-1">
                  {categories.map((category) => {
                    const Icon = category.icon;
                    const isSelected = selectedCategory === category.id;
                    return (
                      <button
                        key={category.id}
                        onClick={() => handleCategoryClick(category.id)}
                        className={cn(
                          'w-full flex items-center gap-3 px-3 py-2 rounded-lg',
                          'text-sm font-medium transition-colors',
                          isSelected
                            ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                            : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800',
                        )}
                      >
                        <Icon className="h-4 w-4 flex-shrink-0" />
                        <span className="flex-1 text-left">{category.name}</span>
                      </button>
                    );
                  })}
                </div>
              </Card2>

              {/* Quick Actions */}
              <Card2 className="p-4">
                <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-3">
                  Quick Actions
                </h2>
                <div className="space-y-2">
                  <button
                    onClick={openTour}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2 rounded-lg',
                      'text-sm font-medium',
                      'text-neutral-700 dark:text-neutral-300',
                      'hover:bg-neutral-100 dark:hover:bg-neutral-800',
                      'transition-colors',
                    )}
                  >
                    <Video className="h-4 w-4" />
                    Take Feature Tour
                  </button>
                  <a
                    href="mailto:support@careercopilot.com"
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2 rounded-lg',
                      'text-sm font-medium',
                      'text-neutral-700 dark:text-neutral-300',
                      'hover:bg-neutral-100 dark:hover:bg-neutral-800',
                      'transition-colors',
                    )}
                  >
                    <Mail className="h-4 w-4" />
                    Email Support
                  </a>
                  <button
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2 rounded-lg',
                      'text-sm font-medium',
                      'text-neutral-700 dark:text-neutral-300',
                      'hover:bg-neutral-100 dark:hover:bg-neutral-800',
                      'transition-colors',
                    )}
                  >
                    <MessageCircle className="h-4 w-4" />
                    Live Chat
                  </button>
                </div>
              </Card2>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-8">
            {/* Category Description */}
            {selectedCategory && (
              <Card2 className="p-6">
                {(() => {
                  const category = categories.find((c) => c.id === selectedCategory);
                  if (!category) return null;
                  const Icon = category.icon;
                  return (
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                        <Icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 mb-1">
                          {category.name}
                        </h2>
                        <p className="text-neutral-600 dark:text-neutral-400">
                          {category.description}
                        </p>
                      </div>
                    </div>
                  );
                })()}
              </Card2>
            )}

            {/* FAQ Items */}
            <div>
              <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-4">
                {searchQuery
                  ? `Search Results (${filteredFAQs.length})`
                  : selectedCategory
                  ? 'Frequently Asked Questions'
                  : 'All Questions'}
              </h2>

              {filteredFAQs.length === 0 ? (
                <Card2 className="p-12 text-center">
                  <AlertCircle className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                    No results found
                  </h3>
                  <p className="text-neutral-600 dark:text-neutral-400">
                    Try adjusting your search or browse by category
                  </p>
                </Card2>
              ) : (
                <div className="space-y-3">
                  {filteredFAQs.map((item) => {
                    const isExpanded = expandedItems.has(item.id);
                    return (
                      <Card2 key={item.id} className="overflow-hidden">
                        <button
                          onClick={() => toggleItem(item.id)}
                          className={cn(
                            'w-full flex items-center justify-between gap-4 p-4',
                            'text-left transition-colors',
                            'hover:bg-neutral-50 dark:hover:bg-neutral-800/50',
                          )}
                        >
                          <span className="text-base font-medium text-neutral-900 dark:text-neutral-100">
                            {item.question}
                          </span>
                          <motion.div
                            animate={{ rotate: isExpanded ? 180 : 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            <ChevronDown className="h-5 w-5 text-neutral-500 flex-shrink-0" />
                          </motion.div>
                        </button>

                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.2 }}
                              className="overflow-hidden"
                            >
                              <div className="px-4 pb-4 pt-0">
                                <p className="text-neutral-600 dark:text-neutral-400">
                                  {item.answer}
                                </p>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </Card2>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Video Tutorials */}
            {!searchQuery && !selectedCategory && (
              <div>
                <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-4">
                  Video Tutorials
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {videoTutorials.map((video) => (
                    <Card2 key={video.id} className="overflow-hidden group cursor-pointer">
                      <div className="relative aspect-video bg-neutral-200 dark:bg-neutral-700">
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="p-4 rounded-full bg-white/90 dark:bg-neutral-800/90 group-hover:scale-110 transition-transform">
                            <Video className="h-8 w-8 text-primary-600 dark:text-primary-400" />
                          </div>
                        </div>
                      </div>
                      <div className="p-4">
                        <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                          {video.title}
                        </h3>
                        <p className="text-sm text-neutral-600 dark:text-neutral-400">
                          {video.duration}
                        </p>
                      </div>
                    </Card2>
                  ))}
                </div>
              </div>
            )}

            {/* Contact Support */}
            <Card2 className="p-6 bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800">
              <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
                Still need help?
              </h2>
              <p className="text-neutral-600 dark:text-neutral-400 mb-4">
                Can't find what you're looking for? Our support team is here to help.
              </p>
              <div className="flex flex-wrap gap-3">
                <a
                  href="mailto:support@careercopilot.com"
                  className={cn(
                    'inline-flex items-center gap-2 px-4 py-2 rounded-lg',
                    'text-sm font-medium',
                    'bg-primary-600 text-white',
                    'hover:bg-primary-700',
                    'transition-colors',
                  )}
                >
                  <Mail className="h-4 w-4" />
                  Email Support
                </a>
                <button
                  className={cn(
                    'inline-flex items-center gap-2 px-4 py-2 rounded-lg',
                    'text-sm font-medium',
                    'bg-white dark:bg-neutral-800',
                    'text-neutral-700 dark:text-neutral-300',
                    'border border-neutral-300 dark:border-neutral-600',
                    'hover:bg-neutral-50 dark:hover:bg-neutral-700',
                    'transition-colors',
                  )}
                >
                  <MessageCircle className="h-4 w-4" />
                  Start Live Chat
                </button>
              </div>
            </Card2>
          </div>
        </div>
      </div>

      {/* Feature Tour Modal */}
      <FeatureTour isOpen={isOpen} onClose={closeTour} onComplete={completeTour} />
    </div>
  );
}
