'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Search, ArrowRight } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { isValidAlgorandAddress } from '@/lib/utils'

/**
 * Props for the {@link SearchBar} component.
 *
 * @property defaultAddress - Pre-filled Algorand address (e.g., from URL params)
 * @property onAnalyze - Callback invoked with the validated address when the user
 *   submits. If not provided, the component navigates to `/analyze?address=...`
 *   using Next.js router.
 * @property showExamples - Whether to show the "Try an example" link below the
 *   input when no address is entered. Defaults to true.
 * @property size - Visual size variant. "large" increases input height and button
 *   size for hero/landing page use. Defaults to "default".
 */
interface SearchBarProps {
  defaultAddress?: string
  onAnalyze?: (address: string) => void
  showExamples?: boolean
  size?: 'default' | 'large'
}

/**
 * Algorand wallet address input with validation and navigation.
 *
 * This is the primary entry point for users to begin wallet analysis. It provides:
 * - Real-time address validation (58 uppercase alphanumeric characters)
 * - Visual feedback: red border and character count when address is invalid
 * - Auto-uppercase conversion on input
 * - Example address pre-fill button for demo purposes
 * - Two submission modes: callback (`onAnalyze`) or router navigation
 *
 * Validation uses `isValidAlgorandAddress()` from `@/lib/utils`, which checks
 * that the address is exactly 58 characters and matches the Algorand base32 format.
 *
 * Accessibility: Uses `role="search"`, `aria-label`, `aria-describedby`,
 * `aria-invalid`, and `role="alert"` for error messages.
 *
 * @param props - Component props
 *
 * @example
 * ```tsx
 * // On landing page (navigates to /analyze)
 * <SearchBar size="large" showExamples={true} />
 *
 * // In a modal (callback mode)
 * <SearchBar onAnalyze={(addr) => fetchData(addr)} showExamples={false} />
 * ```
 */
export function SearchBar({
  defaultAddress = '',
  onAnalyze,
  showExamples = true,
  size = 'default'
}: SearchBarProps) {
  const [address, setAddress] = useState(defaultAddress)
  const [isValid, setIsValid] = useState(false)
  const router = useRouter()

  useEffect(() => {
    setIsValid(isValidAlgorandAddress(address))
  }, [address])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) return

    if (onAnalyze) {
      onAnalyze(address)
    } else {
      router.push(`/analyze?address=${encodeURIComponent(address)}`)
    }
  }

  const fillExample = () => {
    const exampleAddress = 'I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4'
    setAddress(exampleAddress)
  }

  const inputSize = size === 'large' ? 'h-14 text-lg' : ''
  const buttonSize = size === 'large' ? 'xl' : 'default'

  return (
    <div className="w-full space-y-3">
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3" role="search">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" aria-hidden="true" />
          <Input
            value={address}
            onChange={(e) => setAddress(e.target.value.toUpperCase())}
            placeholder="Paste Algorand address (58 characters)"
            aria-label="Algorand wallet address"
            aria-describedby={address && !isValid ? "address-error" : undefined}
            aria-invalid={address && !isValid ? true : undefined}
            className={`pl-10 font-mono ${inputSize} ${
              address && !isValid ? 'border-red-500 focus-visible:ring-red-500' : ''
            }`}
            maxLength={58}
          />
        </div>
        <Button
          type="submit"
          disabled={!isValid}
          size={buttonSize as 'default' | 'xl'}
          className="group"
          aria-label="Analyze wallet for sovereignty score"
        >
          Analyze Wallet
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
        </Button>
      </form>

      {address && !isValid && (
        <p id="address-error" className="text-sm text-red-400" role="alert">
          {address.length < 58
            ? `${58 - address.length} more characters needed`
            : 'Invalid address format'}
        </p>
      )}

      {showExamples && !address && (
        <p className="text-sm text-slate-500">
          Try an example:{' '}
          <button
            onClick={fillExample}
            className="text-orange-500 hover:text-orange-400 underline underline-offset-2 font-mono"
          >
            I26BHU...L3BIP4
          </button>
        </p>
      )}
    </div>
  )
}
