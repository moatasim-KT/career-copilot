'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';

export const Navbar = () => {
  const pathname = usePathname();
  const { token, logout } = useAuth();

  const navItems = [
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'Profile', href: '/profile' },
    { name: 'Jobs', href: '/jobs' },
    { name: 'Recommendations', href: '/recommendations' },
    { name: 'Skill Gap', href: '/skill-gap' },
  ];

  if (!token) {
    // Don't render navbar if not authenticated
    return null;
  }

  return (
    <nav className="bg-gray-800 p-4 fixed w-full z-10 top-0">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/dashboard" className="text-white text-2xl font-bold">
          Career Copilot
        </Link>
        <div className="flex space-x-4">
          {navItems.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`text-white hover:text-gray-300 ${pathname === item.href ? 'font-bold' : ''}`}
            >
              {item.name}
            </Link>
          ))}
          <button
            onClick={logout}
            className="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-3 rounded text-sm"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};
