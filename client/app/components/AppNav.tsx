'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { PATHS } from '@/app/config/routes';
import { GOALS } from '@/app/config/goals';

const navItems = [
  { label: 'Home', href: PATHS.home },
  { label: 'Dashboard', href: PATHS.dashboard },
  ...GOALS.map((g) => ({ label: g.navLabel, href: g.hrefNew })),
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="bg-gray-800 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-12 gap-6 overflow-x-auto">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`whitespace-nowrap text-sm font-medium hover:text-blue-300 ${
                pathname === item.href ? 'text-blue-400' : 'text-gray-300'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
