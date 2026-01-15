'use client'

interface CoinStackProps {
  className?: string
  size?: number
  metal?: 'gold' | 'silver' | 'bronze'
  animated?: boolean
}

const metalColors = {
  gold: {
    primary: '#FFD700',
    secondary: '#FFC700',
    tertiary: '#DAA520',
    dark: '#B8860B',
    shine: '#FFE55C',
  },
  silver: {
    primary: '#C0C0C0',
    secondary: '#D3D3D3',
    tertiary: '#A9A9A9',
    dark: '#808080',
    shine: '#E8E8E8',
  },
  bronze: {
    primary: '#CD7F32',
    secondary: '#D4943A',
    tertiary: '#B87333',
    dark: '#8B4513',
    shine: '#DDA15E',
  },
}

export function CoinStack({ className = '', size = 120, metal = 'gold', animated = true }: CoinStackProps) {
  const colors = metalColors[metal]

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id={`coinGrad-${metal}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={colors.shine} />
          <stop offset="50%" stopColor={colors.primary} />
          <stop offset="100%" stopColor={colors.tertiary} />
        </linearGradient>
      </defs>

      {/* Stack of coins from bottom to top */}
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <g key={i} transform={`translate(${i * 2}, ${80 - i * 12})`}>
          {/* Coin edge (side) */}
          <ellipse cx="50" cy="20" rx="35" ry="8" fill={colors.dark} />
          {/* Coin face */}
          <ellipse cx="50" cy="15" rx="35" ry="8" fill={`url(#coinGrad-${metal})`} />
          {/* Inner circle */}
          <ellipse cx="50" cy="15" rx="28" ry="6" fill="none" stroke={colors.dark} strokeWidth="1" opacity="0.5" />
          {/* Symbol on top coin */}
          {i === 5 && (
            <text x="50" y="18" textAnchor="middle" fill={colors.dark} fontSize="8" fontWeight="bold">
              {metal === 'gold' ? '₿' : metal === 'silver' ? 'Ag' : 'Cu'}
            </text>
          )}
        </g>
      ))}

      {/* Sparkles */}
      {animated && (
        <>
          <circle cx="30" cy="30" r="2" fill="white">
            <animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" />
          </circle>
          <circle cx="85" cy="50" r="1.5" fill="white">
            <animate attributeName="opacity" values="0;1;0" dur="1.8s" repeatCount="indefinite" begin="0.4s" />
          </circle>
          <circle cx="55" cy="20" r="2" fill="white">
            <animate attributeName="opacity" values="0;1;0" dur="1.3s" repeatCount="indefinite" begin="0.8s" />
          </circle>
        </>
      )}
    </svg>
  )
}
