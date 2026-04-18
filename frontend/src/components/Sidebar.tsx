import { NavLink } from 'react-router-dom';
import type { User } from '../types';

interface Props {
  user: User | null;
  onLogout: () => void;
}

const roleNav: Record<string, { to: string; icon: string; label: string }[]> = {
  admin: [
    { to: '/',         icon: '▦', label: 'Обзор' },
    { to: '/requests', icon: '◈', label: 'Все заявки' },
    { to: '/queue',    icon: '◎', label: 'Очередь' },
    { to: '/users',    icon: '◉', label: 'Пользователи' },
  ],
  agent: [
    { to: '/',         icon: '▦', label: 'Обзор' },
    { to: '/requests', icon: '◈', label: 'Все заявки' },
    { to: '/queue',    icon: '◎', label: 'Очередь' },
  ],
  employee: [
    { to: '/',          icon: '▦', label: 'Обзор' },
    { to: '/my',        icon: '◈', label: 'Мои заявки' },
  ],
};

export function Sidebar({ user, onLogout }: Props) {
  const links = user ? (roleNav[user.role] ?? roleNav.employee) : [];
  const initials = user?.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() ?? '?';

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⚡</div>
        <span className="sidebar-logo-text">ServiceFlow</span>
      </div>

      <span className="nav-label">Навигация</span>

      {links.map(l => (
        <NavLink
          key={l.to}
          to={l.to}
          end={l.to === '/'}
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          <span className="icon">{l.icon}</span>
          {l.label}
        </NavLink>
      ))}

      <div className="sidebar-bottom">
        {user ? (
          <>
            <div className="user-card">
              <div className="user-avatar">{initials}</div>
              <div className="user-info">
                <div className="user-name">{user.full_name}</div>
                <div className="user-role">{user.role}</div>
              </div>
            </div>
            <button className="nav-link" style={{ marginTop: 8, color: 'var(--red)' }} onClick={onLogout}>
              <span className="icon">⏏</span> Выйти
            </button>
          </>
        ) : (
          <div className="user-card">
            <div className="user-avatar" style={{ background: 'var(--bg-3)' }}>?</div>
            <div className="user-info">
              <div className="user-name">Не подключён</div>
              <div className="user-role">—</div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
