import { Link, type LinkProps } from '@tanstack/react-router'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost'

const base =
  'inline-flex min-h-11 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold no-underline transition-[background-color,border-color,color,opacity] duration-150 disabled:cursor-not-allowed disabled:opacity-50'

const variants: Record<ButtonVariant, string> = {
  primary: 'border border-accent bg-accent text-accent-contrast hover:opacity-90',
  secondary: 'border border-border bg-subtle text-foreground hover:border-border-strong',
  ghost: 'border border-transparent bg-transparent text-secondary hover:bg-subtle hover:text-foreground',
}

export function buttonClass(variant: ButtonVariant = 'secondary', extra = ''): string {
  return `${base} ${variants[variant]} ${extra}`.trim()
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
}

export function Button({ variant = 'secondary', className = '', type = 'button', ...props }: ButtonProps) {
  return <button type={type} className={buttonClass(variant, className)} {...props} />
}

interface ButtonLinkProps {
  to: LinkProps['to']
  params?: LinkProps['params']
  variant?: ButtonVariant
  children: ReactNode
}

export function ButtonLink({ to, params, variant = 'secondary', children }: ButtonLinkProps) {
  return (
    <Link to={to} params={params} className={buttonClass(variant)}>
      {children}
    </Link>
  )
}
