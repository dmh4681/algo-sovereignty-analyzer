'use client'

interface MineCartProps {
  className?: string
  size?: number
  filled?: boolean
  animated?: boolean
}

export function MineCart({ className = '', size = 180, filled = true, animated = true }: MineCartProps) {
  return (
    <svg
      width={size}
      height={size * 0.7}
      viewBox="0 0 180 126"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Track/rails */}
      <rect x="10" y="110" width="160" height="6" fill="#4A4A4A" rx="1" />
      <rect x="20" y="108" width="10" height="10" fill="#5C4033" />
      <rect x="60" y="108" width="10" height="10" fill="#5C4033" />
      <rect x="110" y="108" width="10" height="10" fill="#5C4033" />
      <rect x="150" y="108" width="10" height="10" fill="#5C4033" />

      {/* Wheels */}
      <g>
        <circle cx="50" cy="100" r="15" fill="#4A4A4A" stroke="#333" strokeWidth="2" />
        <circle cx="50" cy="100" r="8" fill="#333" />
        <circle cx="50" cy="100" r="3" fill="#666" />
        {animated && (
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 50 100"
            to="360 50 100"
            dur="2s"
            repeatCount="indefinite"
          />
        )}
      </g>
      <g>
        <circle cx="130" cy="100" r="15" fill="#4A4A4A" stroke="#333" strokeWidth="2" />
        <circle cx="130" cy="100" r="8" fill="#333" />
        <circle cx="130" cy="100" r="3" fill="#666" />
        {animated && (
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 130 100"
            to="360 130 100"
            dur="2s"
            repeatCount="indefinite"
          />
        )}
      </g>

      {/* Cart body */}
      <path
        d="M25 85 L35 35 L145 35 L155 85 Z"
        fill="#5C4033"
        stroke="#4A3728"
        strokeWidth="2"
      />

      {/* Cart interior */}
      <path
        d="M30 82 L38 40 L142 40 L150 82 Z"
        fill="#3D2817"
      />

      {/* Metal rim */}
      <path
        d="M25 85 L155 85"
        stroke="#708090"
        strokeWidth="4"
        strokeLinecap="round"
      />

      {/* Metal bands */}
      <line x1="35" y1="35" x2="30" y2="85" stroke="#708090" strokeWidth="3" />
      <line x1="145" y1="35" x2="150" y2="85" stroke="#708090" strokeWidth="3" />
      <line x1="90" y1="35" x2="90" y2="85" stroke="#708090" strokeWidth="2" />

      {/* Ore/treasure inside */}
      {filled && (
        <>
          {/* Gold nuggets */}
          <ellipse cx="70" cy="55" rx="20" ry="8" fill="#FFD700" />
          <ellipse cx="110" cy="55" rx="18" ry="7" fill="#FFC700" />
          <circle cx="55" cy="50" r="10" fill="#FFD700" />
          <circle cx="85" cy="48" r="12" fill="#DAA520" />
          <circle cx="115" cy="50" r="9" fill="#FFD700" />
          <circle cx="125" cy="55" r="8" fill="#FFC700" />

          {/* Some silver ore */}
          <circle cx="65" cy="58" r="6" fill="#C0C0C0" />
          <circle cx="100" cy="52" r="7" fill="#A9A9A9" />

          {/* Rock/ore chunks */}
          <polygon points="45,60 55,55 50,65" fill="#696969" />
          <polygon points="130,58 140,52 138,62" fill="#708090" />

          {/* Sparkles on gold */}
          {animated && (
            <>
              <circle cx="75" cy="45" r="2" fill="white">
                <animate attributeName="opacity" values="0;1;0" dur="1.2s" repeatCount="indefinite" />
              </circle>
              <circle cx="105" cy="48" r="1.5" fill="white">
                <animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" begin="0.3s" />
              </circle>
              <circle cx="60" cy="52" r="1.5" fill="white">
                <animate attributeName="opacity" values="0;1;0" dur="1.8s" repeatCount="indefinite" begin="0.6s" />
              </circle>
            </>
          )}
        </>
      )}

      {/* Handle */}
      <rect x="155" y="50" width="20" height="6" fill="#5C4033" rx="2" />
      <circle cx="172" cy="53" r="5" fill="#708090" />
    </svg>
  )
}
