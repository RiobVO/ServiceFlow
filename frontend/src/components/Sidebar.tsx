import { NavLink } from 'react-router-dom';
import {
  Inbox,
  LayoutGrid,
  ListChecks,
  LogOut,
  Users as UsersIcon,
  type LucideIcon,
} from 'lucide-react';
import type { User } from '../types';
import { Avatar, BrandMark } from './primitives';

interface NavItem {
  to: string;
  icon: LucideIcon;
  label: string;
}

const ROLE_NAV: Record<User['role'], NavItem[]> = {
  admin: [
    { to: '/', icon: LayoutGrid, label: 'Обзор' },
    { to: '/requests', icon: ListChecks, label: 'Все заявки' },
    { to: '/queue', icon: Inbox, label: 'Очередь' },
    { to: '/users', icon: UsersIcon, label: 'Пользователи' },
  ],
  agent: [
    { to: '/', icon: LayoutGrid, label: 'Обзор' },
    { to: '/requests', icon: ListChecks, label: 'Все заявки' },
    { to: '/queue', icon: Inbox, label: 'Очередь' },
  ],
  employee: [
    { to: '/', icon: LayoutGrid, label: 'Обзор' },
    { to: '/my', icon: ListChecks, label: 'Мои заявки' },
  ],
};

export function Sidebar({ user, onLogout }: { user: User; onLogout: () => void }) {
  const links = ROLE_NAV[user.role] ?? ROLE_NAV.employee;

  return (
    <aside className="sf-sidebar">
      <div className="sf-sidebar__brand">
        <BrandMark size={22} />
        <span className="sf-sidebar__brand-name">ServiceFlow</span>
      </div>

      <div className="sf-sidebar__section">Навигация</div>
      <nav className="sf-sidebar__nav">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) => `sf-nav-row ${isActive ? 'is-active' : ''}`}
            >
              <Icon size={18} strokeWidth={1.5} />
              {link.label}
            </NavLink>
          );
        })}
      </nav>

      <div className="sf-sidebar__footer">
        <div className="sf-sidebar__user">
          <Avatar name={user.full_name} size={30} />
          <div style={{ overflow: 'hidden', flex: 1 }}>
            <div className="sf-sidebar__user-name">{user.full_name}</div>
            <div className="sf-sidebar__user-role">{user.role}</div>
          </div>
        </div>
        <button type="button" className="sf-nav-row" onClick={onLogout}>
          <LogOut size={18} strokeWidth={1.5} />
          Выйти
        </button>
      </div>
    </aside>
  );
}
