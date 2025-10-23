'use client';

import { Briefcase, Github, Mail, Heart } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="col-span-1 sm:col-span-2 lg:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <Briefcase className="h-6 w-6 text-blue-600" />
              <span className="text-lg font-bold text-gray-900">Career Copilot</span>
            </div>
            <p className="text-gray-600 text-sm mb-4 max-w-md">
              AI-powered job application tracking and career guidance platform. 
              Transform your job search with intelligent recommendations and insights.
            </p>
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
              <a
                href="mailto:support@careercopilot.com"
                className="flex items-center space-x-2 text-gray-500 hover:text-blue-600 transition-colors"
              >
                <Mail className="h-4 w-4" />
                <span className="text-sm">Contact Support</span>
              </a>
              <a
                href="https://github.com/career-copilot"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-gray-500 hover:text-blue-600 transition-colors"
              >
                <Github className="h-4 w-4" />
                <span className="text-sm">GitHub</span>
              </a>
            </div>
          </div>

          {/* Features Section */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Features</h3>
            <ul className="space-y-2">
              <li>
                <span className="text-sm text-gray-600 hover:text-blue-600 cursor-pointer transition-colors">
                  Job Tracking
                </span>
              </li>
              <li>
                <span className="text-sm text-gray-600 hover:text-blue-600 cursor-pointer transition-colors">
                  AI Recommendations
                </span>
              </li>
              <li>
                <span className="text-sm text-gray-600 hover:text-blue-600 cursor-pointer transition-colors">
                  Skill Gap Analysis
                </span>
              </li>
              <li>
                <span className="text-sm text-gray-600 hover:text-blue-600 cursor-pointer transition-colors">
                  Application Analytics
                </span>
              </li>
            </ul>
          </div>

          {/* Resources Section */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Resources</h3>
            <ul className="space-y-2">
              <li>
                <span className="text-sm text-gray-600 hover:text-blue-600 cursor-pointer transition-colors">
                  Getting Started
                </span>
              </li>
              <li>
                <span className="text-sm text-gray-600 hover:text-blue-600 cursor-pointer transition-colors">
                  User Guide
                </span>
              </li>
              <li>
                <span className="text-sm text-gray-600 hover:text-blue-600 cursor-pointer transition-colors">
                  API Documentation
                </span>
              </li>
              <li>
                <span className="text-sm text-gray-600 hover:text-blue-600 cursor-pointer transition-colors">
                  Privacy Policy
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-200 pt-6 mt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">© {currentYear} Career Copilot</span>
              <Heart className="h-4 w-4 text-red-500" />
              <span className="text-sm text-gray-500">Built for job seekers</span>
            </div>
            <div className="flex items-center space-x-6">
              <span className="text-sm text-gray-500 hover:text-blue-600 cursor-pointer transition-colors">
                Terms of Service
              </span>
              <span className="text-sm text-gray-500 hover:text-blue-600 cursor-pointer transition-colors">
                Privacy Policy
              </span>
              <span className="text-sm text-gray-500 hover:text-blue-600 cursor-pointer transition-colors">
                Cookie Policy
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}