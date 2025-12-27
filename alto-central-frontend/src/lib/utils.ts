import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function sanitizeUIMessages(messages: any[]) {
  return messages.map(message => ({
    ...message,
    content: typeof message.content === 'string' ? message.content : message.content
  }))
}

export function truncateString(str: string, maxLength: number): string {
  if (!str) return ''
  if (str.length <= maxLength) return str
  return str.substring(0, maxLength) + '...'
}
