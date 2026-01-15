'use client'

interface TreasureChestProps {
  className?: string
  size?: number
  open?: boolean
  animated?: boolean
}

export function TreasureChest({ className = '', size = 200, open = true, animated = true }: TreasureChestProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Glow behind chest when open */}
      {open && (
        <ellipse cx="100" cy="100" rx="80" ry="60" fill="url(#treasureGlow)">
          {animated && (
            <animate
              attributeName="opacity"
              values="0.3;0.6;0.3"
              dur="2s"
              repeatCount="indefinite"
            />
          )}
        </ellipse>
      )}

      {/* Chest lid (open position) */}
      {open && (
        <g transform="translate(100, 70) rotate(-30) translate(-100, -70)">
          {/* Lid outer */}
          <path
            d="M30 70 Q30 40 100 40 Q170 40 170 70 L170 85 L30 85 Z"
            fill="#654321"
            stroke="#4A3728"
            strokeWidth="2"
          />
          {/* Lid inner curve */}
          <path
            d="M35 70 Q35 50 100 50 Q165 50 165 70"
            fill="#8B4513"
          />
          {/* Metal bands on lid */}
          <rect x="45" y="55" width="8" height="30" fill="#B8860B" rx="1" />
          <rect x="147" y="55" width="8" height="30" fill="#B8860B" rx="1" />
          <rect x="96" y="55" width="8" height="30" fill="#B8860B" rx="1" />
        </g>
      )}

      {/* Chest lid (closed position) */}
      {!open && (
        <>
          <path
            d="M30 100 Q30 70 100 70 Q170 70 170 100 L170 115 L30 115 Z"
            fill="#654321"
            stroke="#4A3728"
            strokeWidth="2"
          />
          <path
            d="M35 100 Q35 80 100 80 Q165 80 165 100"
            fill="#8B4513"
          />
          <rect x="45" y="85" width="8" height="30" fill="#B8860B" rx="1" />
          <rect x="147" y="85" width="8" height="30" fill="#B8860B" rx="1" />
          <rect x="96" y="85" width="8" height="30" fill="#B8860B" rx="1" />
        </>
      )}

      {/* Treasure inside (only when open) */}
      {open && (
        <>
          {/* Gold coins pile */}
          <ellipse cx="70" cy="105" rx="20" ry="8" fill="#FFD700" />
          <ellipse cx="130" cy="105" rx="20" ry="8" fill="#FFD700" />
          <ellipse cx="100" cy="100" rx="25" ry="10" fill="#FFC700" />

          {/* Individual coins */}
          <circle cx="60" cy="95" r="8" fill="#FFD700" stroke="#DAA520" strokeWidth="1" />
          <circle cx="80" cy="92" r="8" fill="#FFC700" stroke="#DAA520" strokeWidth="1" />
          <circle cx="100" cy="88" r="9" fill="#FFD700" stroke="#DAA520" strokeWidth="1" />
          <circle cx="120" cy="92" r="8" fill="#FFC700" stroke="#DAA520" strokeWidth="1" />
          <circle cx="140" cy="95" r="8" fill="#FFD700" stroke="#DAA520" strokeWidth="1" />

          {/* Gold bars */}
          <rect x="75" y="98" width="20" height="8" fill="#FFD700" rx="1" transform="rotate(-10, 85, 102)" />
          <rect x="105" y="98" width="20" height="8" fill="#FFC700" rx="1" transform="rotate(10, 115, 102)" />

          {/* Gems */}
          <polygon points="65,85 70,78 75,85 70,90" fill="#50C878" /> {/* Emerald */}
          <polygon points="130,82 135,75 140,82 135,87" fill="#E0115F" /> {/* Ruby */}

          {/* Sparkles */}
          {animated && (
            <>
              <circle cx="90" cy="80" r="2" fill="white">
                <animate attributeName="opacity" values="0;1;0" dur="1s" repeatCount="indefinite" />
              </circle>
              <circle cx="110" cy="85" r="2" fill="white">
                <animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" begin="0.3s" />
              </circle>
              <circle cx="75" cy="88" r="1.5" fill="white">
                <animate attributeName="opacity" values="0;1;0" dur="1.2s" repeatCount="indefinite" begin="0.6s" />
              </circle>
              <circle cx="125" cy="78" r="1.5" fill="white">
                <animate attributeName="opacity" values="0;1;0" dur="1.3s" repeatCount="indefinite" begin="0.9s" />
              </circle>
            </>
          )}
        </>
      )}

      {/* Chest body */}
      <rect x="30" y="115" width="140" height="60" fill="#654321" stroke="#4A3728" strokeWidth="2" rx="3" />

      {/* Wood grain texture */}
      <line x1="30" y1="130" x2="170" y2="130" stroke="#4A3728" strokeWidth="1" opacity="0.5" />
      <line x1="30" y1="145" x2="170" y2="145" stroke="#4A3728" strokeWidth="1" opacity="0.5" />
      <line x1="30" y1="160" x2="170" y2="160" stroke="#4A3728" strokeWidth="1" opacity="0.5" />

      {/* Metal bands */}
      <rect x="45" y="115" width="8" height="60" fill="#B8860B" rx="1" />
      <rect x="147" y="115" width="8" height="60" fill="#B8860B" rx="1" />

      {/* Lock plate */}
      <rect x="90" y="115" width="20" height="25" fill="#B8860B" rx="2" />
      <circle cx="100" cy="127" r="5" fill="#8B6914" />
      <rect x="98" y="127" width="4" height="8" fill="#8B6914" />

      {/* Corner reinforcements */}
      <path d="M30 115 L45 115 L45 130 L30 130 Z" fill="#8B6914" />
      <path d="M155 115 L170 115 L170 130 L155 130 Z" fill="#8B6914" />
      <path d="M30 160 L45 160 L45 175 L30 175 Z" fill="#8B6914" />
      <path d="M155 160 L170 160 L170 175 L155 175 Z" fill="#8B6914" />

      {/* Gradients */}
      <defs>
        <radialGradient id="treasureGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FFD700" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#FFD700" stopOpacity="0" />
        </radialGradient>
      </defs>
    </svg>
  )
}
