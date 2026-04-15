/**
 * ServiceFlow design primitives.
 * Переносит UI-кит из .design-kit на нашу React+TS архитектуру, используя
 * CSS-классы вместо inline-стилей.
 */

import {
  forwardRef,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from 'react';
import { AlertTriangle, type LucideIcon } from 'lucide-react';

// ── Button ────────────────────────────────────────────────

type ButtonVariant = 'primary' | 'ghost' | 'quiet' | 'danger';
type ButtonSize = 'md' | 'sm';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: LucideIcon;
  fullWidth?: boolean;
  children?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = 'primary',
    size = 'md',
    icon: Icon,
    fullWidth,
    className = '',
    children,
    ...rest
  },
  ref,
) {
  const classes = [
    'sf-btn',
    `sf-btn--${size}`,
    `sf-btn--${variant}`,
    fullWidth ? 'sf-btn--full' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');
  const iconSize = size === 'sm' ? 14 : 16;
  return (
    <button ref={ref} className={classes} {...rest}>
      {Icon ? <Icon size={iconSize} strokeWidth={1.5} /> : null}
      {children}
    </button>
  );
});

// ── Inputs ────────────────────────────────────────────────

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  mono?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { mono, className = '', ...rest },
  ref,
) {
  const classes = ['sf-input', mono ? 'sf-input--mono' : '', className]
    .filter(Boolean)
    .join(' ');
  return <input ref={ref} className={classes} {...rest} />;
});

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className = '', ...rest }, ref) {
  return <textarea ref={ref} className={`sf-textarea ${className}`} {...rest} />;
});

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement>
>(function Select({ className = '', children, ...rest }, ref) {
  return (
    <select ref={ref} className={`sf-select ${className}`} {...rest}>
      {children}
    </select>
  );
});

// ── Field (label + control) ───────────────────────────────

interface FieldProps {
  label: string;
  children: ReactNode;
  hint?: ReactNode;
}

export function Field({ label, children, hint }: FieldProps) {
  return (
    <label className="sf-field">
      <span className="sf-field__label">{label}</span>
      {children}
      {hint ? <span className="sf-form__hint">{hint}</span> : null}
    </label>
  );
}

// ── Error message ────────────────────────────────────────

export function ErrorMessage({ children }: { children: ReactNode }) {
  return (
    <div className="sf-error">
      <AlertTriangle size={14} strokeWidth={1.5} /> {children}
    </div>
  );
}

// ── Card ─────────────────────────────────────────────────

interface CardProps {
  children: ReactNode;
  elevated?: boolean;
  className?: string;
}

export function Card({ children, elevated, className = '' }: CardProps) {
  const classes = ['sf-card', elevated ? 'sf-card--elevated' : '', className]
    .filter(Boolean)
    .join(' ');
  return <div className={classes}>{children}</div>;
}

export function CardHeader({
  title,
  subtitle,
  right,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  right?: ReactNode;
}) {
  return (
    <div className="sf-card__header">
      <div>
        <div className="sf-card__title">{title}</div>
        {subtitle ? <div className="sf-card__subtitle">{subtitle}</div> : null}
      </div>
      {right}
    </div>
  );
}

// ── Avatar ───────────────────────────────────────────────

export function Avatar({ name, size = 32 }: { name: string; size?: number }) {
  const initials = (name || '?')
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
  return (
    <div
      className="sf-avatar"
      style={{ width: size, height: size, fontSize: Math.round(size * 0.4) }}
    >
      {initials}
    </div>
  );
}

// ── Eyebrow ──────────────────────────────────────────────

export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="sf-eyebrow">{children}</div>;
}

// ── PageHeader ───────────────────────────────────────────

interface PageHeaderProps {
  title: string;
  subtitle?: ReactNode;
  right?: ReactNode;
}

export function PageHeader({ title, subtitle, right }: PageHeaderProps) {
  return (
    <div className="sf-page-header">
      <div>
        <h1 className="sf-page-header__title">{title}</h1>
        {subtitle ? <div className="sf-page-header__subtitle">{subtitle}</div> : null}
      </div>
      {right}
    </div>
  );
}

// ── Empty state ──────────────────────────────────────────

import { Inbox } from 'lucide-react';

interface EmptyProps {
  icon?: LucideIcon;
  children: ReactNode;
}

export function Empty({ icon: Icon = Inbox, children }: EmptyProps) {
  return (
    <div className="sf-empty">
      <div className="sf-empty__icon">
        <Icon size={28} strokeWidth={1.3} />
      </div>
      <div className="sf-empty__text">{children}</div>
    </div>
  );
}

// ── Brand mark (logo) ────────────────────────────────────

export function BrandMark({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <circle cx="16" cy="16" r="14" fill="none" stroke="#1F1E1C" strokeWidth="1.5" />
      <circle cx="16" cy="16" r="8" fill="none" stroke="#CC785C" strokeWidth="1.5" />
      <circle cx="16" cy="16" r="2.5" fill="#1F1E1C" />
    </svg>
  );
}

// ── Time formatting (relative < 24h, absolute after) ────

export function formatTime(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diff = (now - d.getTime()) / 1000;

  if (diff < 60) return 'только что';
  if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`;

  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}
