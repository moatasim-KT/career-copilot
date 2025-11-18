'use client';

import { Briefcase, Github, Mail, Heart } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white dark:bg-neutral-950 border-t border-neutral-200 dark:border-neutral-800 mt-auto">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12 max-w-7xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="col-span-1 sm:col-span-2 lg:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Briefcase className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              <span className="text-lg font-bold text-neutral-900 dark:text-neutral-100">Career Copilot</span>
            </div>
            <p className="text-neutral-600 dark:text-neutral-400 text-sm mb-6 max-w-md leading-relaxed">
              AI-powered job application tracking and career guidance platform.
              Transform your job search with intelligent recommendations and insights.
            </p>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <a
                href="mailto:support@careercopilot.com"
                className="flex items-center gap-2 text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors min-h-[44px] py-2"
              >
                <Mail className="h-4 w-4" />
                <span className="text-sm font-medium">Contact Support</span>
              </a>
              <a
                href="https://github.com/career-copilot"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors min-h-[44px] py-2"
              >
                <Github className="h-4 w-4" />
                <span className="text-sm font-medium">GitHub</span>
              </a>
            </div>
          </div>

          {/* Features Section */}
          <div>
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-4">Features</h3>
            <ul className="space-y-3">
              <li>
                <span className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                  Job Tracking
                </span>
              </li>
              <li>
                <span className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                  AI Recommendations
                </span>
              </li>
              <li>
                <span className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                  Skill Gap Analysis
                </span>
              </li>
              <li>
                <span className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                  Application Analytics
                </span>
              </li>
            </ul>
          </div>

          {/* Resources Section */}
          <div>
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-4">Resources</h3>
            <ul className="space-y-3">
              <li>
                <span className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                  Getting Started
                </span>
              </li>
              <li>
                <span className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                  User Guide
                </span>
              </li>
              <li>
                <span className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                  API Documentation
                </span>
              </li>
              <li>
                <span className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                  Privacy Policy
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-neutral-200 dark:border-neutral-800 pt-8 mt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-500 dark:text-neutral-500">© {currentYear} Career Copilot</span>
              <Heart className="h-4 w-4 text-red-500 dark:text-red-400" />
              <span className="text-sm text-neutral-500 dark:text-neutral-500">Built for job seekers</span>
            </div>
            <div className="flex items-center gap-6">
              <span className="text-sm text-neutral-500 dark:text-neutral-500 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                Terms of Service
              </span>
              <span className="text-sm text-neutral-500 dark:text-neutral-500 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                Privacy Policy
              </span>
              <span className="text-sm text-neutral-500 dark:text-neutral-500 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors">
                Cookie Policy
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}