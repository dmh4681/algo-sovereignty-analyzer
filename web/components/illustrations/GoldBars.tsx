'use client'

interface GoldBarsProps {
  className?: string
  size?: number
  variant?: 'stack' | 'single' | 'pile'
  animated?: boolean
}

export function GoldBars({ className = '', size = 150, variant = 'stack', animated = true }: GoldBarsProps) {
  if (variant === 'single') {
    return (
      <svg
        width={size}
        height={size * 0.5}
        viewBox="0 0 150 75"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
      >
        {/* Single gold bar */}
        <defs>
          <linearGradient id="goldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFE55C" />
            <stop offset="50%" stopColor="#FFD700" />
            <stop offset="100%" stopColor="#DAA520" />
          </linearGradient>
        </defs>

        {/* Top face */}
        <polygon points="30,20 120,20 135,35 15,35" fill="#FFE55C" />
        {/* Front face */}
        <polygon points="15,35 135,35 135,55 15,55" fill="url(#goldGradient)" />
        {/* Right face */}
        <polygon points="135,35 120,20 120,40 135,55" fill="#DAA520" />

        {/* Stamped text/symbol */}
        <text x="75" y="48" textAnchor="middle" fill="#B8860B" fontSize="12" fontWeight="bold">999.9</text>

        {/* Shine effect */}
        <polygon points="25,25 40,25 35,32 20,32" fill="white" opacity="0.4" />

        {animated && (
          <polygon points="25,25 40,25 35,32 20,32" fill="white">
            <animate attributeName="opacity" values="0.2;0.6;0.2" dur="2s" repeatCount="indefinite" />
          </polygon>
        )}
      </svg>
    )
  }

  if (variant === 'pile') {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
      >
        <defs>
          <linearGradient id="goldGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFE55C" />
            <stop offset="50%" stopColor="#FFD700" />
            <stop offset="100%" stopColor="#DAA520" />
          </linearGradient>
        </defs>

        {/* Bottom layer - 3 bars */}
        <g transform="translate(20, 140)">
          <polygon points="0,0 80,0 90,15 -10,15 90,15 90,30 -10,30 -10,15" fill="#DAA520" />
          <polygon points="0,0 80,0 90,15 -10,15" fill="#FFE55C" />
          <polygon points="-10,15 90,15 90,30 -10,30" fill="url(#goldGrad1)" />
        </g>
        <g transform="translate(60, 140)">
          <polygon points="0,0 80,0 90,15 -10,15" fill="#FFE55C" />
          <polygon points="-10,15 90,15 90,30 -10,30" fill="url(#goldGrad1)" />
          <polygon points="90,15 80,0 80,15 90,30" fill="#B8860B" />
        </g>
        <g transform="translate(100, 140)">
          <polygon points="0,0 80,0 90,15 -10,15" fill="#FFE55C" />
          <polygon points="-10,15 90,15 90,30 -10,30" fill="url(#goldGrad1)" />
          <polygon points="90,15 80,0 80,15 90,30" fill="#B8860B" />
        </g>

        {/* Middle layer - 2 bars */}
        <g transform="translate(40, 105)">
          <polygon points="0,0 80,0 90,15 -10,15" fill="#FFE55C" />
          <polygon points="-10,15 90,15 90,30 -10,30" fill="url(#goldGrad1)" />
          <polygon points="90,15 80,0 80,15 90,30" fill="#B8860B" />
        </g>
        <g transform="translate(80, 105)">
          <polygon points="0,0 80,0 90,15 -10,15" fill="#FFE55C" />
          <polygon points="-10,15 90,15 90,30 -10,30" fill="url(#goldGrad1)" />
          <polygon points="90,15 80,0 80,15 90,30" fill="#B8860B" />
        </g>

        {/* Top bar */}
        <g transform="translate(60, 70)">
          <polygon points="0,0 80,0 90,15 -10,15" fill="#FFE55C" />
          <polygon points="-10,15 90,15 90,30 -10,30" fill="url(#goldGrad1)" />
          <polygon points="90,15 80,0 80,15 90,30" fill="#B8860B" />
        </g>

        {/* Sparkles */}
        {animated && (
          <>
            <circle cx="50" cy="120" r="3" fill="white">
              <animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" />
            </circle>
            <circle cx="150" cy="130" r="2" fill="white">
              <animate attributeName="opacity" values="0;1;0" dur="1.8s" repeatCount="indefinite" begin="0.5s" />
            </circle>
            <circle cx="100" cy="80" r="2.5" fill="white">
              <animate attributeName="opacity" values="0;1;0" dur="1.3s" repeatCount="indefinite" begin="0.3s" />
            </circle>
          </>
        )}
      </svg>
    )
  }

  // Default: stack variant
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 150 150"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="goldGradStack" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFE55C" />
          <stop offset="50%" stopColor="#FFD700" />
          <stop offset="100%" stopColor="#DAA520" />
        </linearGradient>
      </defs>

      {/* Bottom bar */}
      <g transform="translate(15, 100)">
        <polygon points="0,0 100,0 115,20 -15,20" fill="#FFE55C" />
        <polygon points="-15,20 115,20 115,35 -15,35" fill="url(#goldGradStack)" />
        <polygon points="115,20 100,0 100,15 115,35" fill="#B8860B" />
      </g>

      {/* Middle bar */}
      <g transform="translate(20, 65)">
        <polygon points="0,0 100,0 115,20 -15,20" fill="#FFE55C" />
        <polygon points="-15,20 115,20 115,35 -15,35" fill="url(#goldGradStack)" />
        <polygon points="115,20 100,0 100,15 115,35" fill="#B8860B" />
      </g>

      {/* Top bar */}
      <g transform="translate(25, 30)">
        <polygon points="0,0 100,0 115,20 -15,20" fill="#FFE55C" />
        <polygon points="-15,20 115,20 115,35 -15,35" fill="url(#goldGradStack)" />
        <polygon points="115,20 100,0 100,15 115,35" fill="#B8860B" />
        {/* Stamp */}
        <text x="50" y="30" textAnchor="middle" fill="#B8860B" fontSize="10" fontWeight="bold">GOLD</text>
      </g>

      {/* Sparkle */}
      {animated && (
        <>
          <circle cx="40" cy="45" r="3" fill="white">
            <animate attributeName="opacity" values="0;1;0" dur="2s" repeatCount="indefinite" />
          </circle>
          <circle cx="110" cy="90" r="2" fill="white">
            <animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" begin="0.7s" />
          </circle>
        </>
      )}
    </svg>
  )
}
