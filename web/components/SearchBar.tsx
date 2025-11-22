'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Search, ArrowRight } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { isValidAlgorandAddress } from '@/lib/utils'

interface SearchBarProps {
  defaultAddress?: string
  onAnalyze?: (address: string) => void
  showExamples?: boolean
  size?: 'default' | 'large'
}

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
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
          <Input
            value={address}
            onChange={(e) => setAddress(e.target.value.toUpperCase())}
            placeholder="Paste Algorand address (58 characters)"
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
        >
          Analyze Wallet
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
        </Button>
      </form>

      {address && !isValid && (
        <p className="text-sm text-red-400">
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
