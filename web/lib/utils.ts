import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatUSD(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function truncateAddress(address: string): string {
  if (address.length <= 16) return address
  return `${address.slice(0, 8)}...${address.slice(-6)}`
}

export function isValidAlgorandAddress(address: string): boolean {
  return address.length === 58 && /^[A-Z0-9]+$/.test(address)
}

export function getSovereigntyColor(status: string): string {
  if (status.includes('Generationally')) return 'emerald'
  if (status.includes('Antifragile')) return 'green'
  if (status.includes('Robust')) return 'yellow'
  if (status.includes('Fragile')) return 'red'
  return 'slate'
}

export function getSovereigntyEmoji(status: string): string {
  if (status.includes('Generationally')) return '🟩'
  if (status.includes('Antifragile')) return '🟢'
  if (status.includes('Robust')) return '🟡'
  if (status.includes('Fragile')) return '🔴'
  return '⚫'
}
