'use client'

interface PickaxeProps {
  className?: string
  size?: number
  variant?: 'gold' | 'silver' | 'default'
  animated?: boolean
}

const headColors = {
  gold: { primary: '#FFD700', secondary: '#DAA520', shine: '#FFE55C' },
  silver: { primary: '#C0C0C0', secondary: '#808080', shine: '#E8E8E8' },
  default: { primary: '#708090', secondary: '#4A5568', shine: '#A0AEC0' },
}

export function Pickaxe({ className = '', size = 100, variant = 'default', animated = true }: PickaxeProps) {
  const colors = headColors[variant]

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <g transform="rotate(-45, 50, 50)">
        {/* Handle */}
        <rect x="45" y="35" width="10" height="60" fill="#8B4513" rx="2" />
        <rect x="47" y="35" width="2" height="60" fill="#A0522D" opacity="0.5" />

        {/* Handle grip wrapping */}
        <rect x="44" y="75" width="12" height="3" fill="#4A3728" rx="1" />
        <rect x="44" y="82" width="12" height="3" fill="#4A3728" rx="1" />
        <rect x="44" y="89" width="12" height="3" fill="#4A3728" rx="1" />

        {/* Pickaxe head */}
        <path
          d="M20 30 L50 35 L80 30 L75 25 L50 28 L25 25 Z"
          fill={colors.primary}
          stroke={colors.secondary}
          strokeWidth="1"
        />

        {/* Left pick point */}
        <path
          d="M20 30 L5 15 L10 12 L25 25"
          fill={colors.primary}
          stroke={colors.secondary}
          strokeWidth="1"
        />

        {/* Right pick point */}
        <path
          d="M80 30 L95 15 L90 12 L75 25"
          fill={colors.primary}
          stroke={colors.secondary}
          strokeWidth="1"
        />

        {/* Metal shine */}
        <path d="M25 27 L45 30" stroke={colors.shine} strokeWidth="2" opacity="0.6" />
        <path d="M55 30 L75 27" stroke={colors.shine} strokeWidth="2" opacity="0.6" />

        {/* Sparkle on tip */}
        {animated && variant !== 'default' && (
          <>
            <circle cx="7" cy="13" r="3" fill="white">
              <animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" />
            </circle>
            <circle cx="93" cy="13" r="3" fill="white">
              <animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" begin="0.75s" />
            </circle>
          </>
        )}
      </g>

      {/* Motion lines when animated */}
      {animated && (
        <g opacity="0.3">
          <line x1="15" y1="85" x2="25" y2="75" stroke="#B8860B" strokeWidth="2">
            <animate attributeName="opacity" values="0;0.5;0" dur="0.8s" repeatCount="indefinite" />
          </line>
          <line x1="20" y1="90" x2="30" y2="80" stroke="#B8860B" strokeWidth="2">
            <animate attributeName="opacity" values="0;0.5;0" dur="0.8s" repeatCount="indefinite" begin="0.2s" />
          </line>
        </g>
      )}
    </svg>
  )
}
