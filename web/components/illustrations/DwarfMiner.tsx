'use client'

interface DwarfMinerProps {
  className?: string
  size?: number
  animated?: boolean
}

export function DwarfMiner({ className = '', size = 200, animated = true }: DwarfMinerProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Helmet with lamp */}
      <ellipse cx="100" cy="65" rx="45" ry="35" fill="#8B4513" />
      <ellipse cx="100" cy="60" rx="40" ry="30" fill="#A0522D" />
      {/* Helmet lamp */}
      <circle cx="100" cy="40" r="10" fill="#FFD700">
        {animated && (
          <animate
            attributeName="opacity"
            values="0.7;1;0.7"
            dur="2s"
            repeatCount="indefinite"
          />
        )}
      </circle>
      {/* Lamp glow */}
      <circle cx="100" cy="40" r="15" fill="#FFD700" opacity="0.3">
        {animated && (
          <animate
            attributeName="r"
            values="15;20;15"
            dur="2s"
            repeatCount="indefinite"
          />
        )}
      </circle>

      {/* Face */}
      <ellipse cx="100" cy="85" rx="35" ry="30" fill="#DEB887" />

      {/* Eyes */}
      <ellipse cx="87" cy="80" rx="6" ry="7" fill="white" />
      <ellipse cx="113" cy="80" rx="6" ry="7" fill="white" />
      <circle cx="88" cy="81" r="3" fill="#4A3728" />
      <circle cx="114" cy="81" r="3" fill="#4A3728" />

      {/* Bushy eyebrows */}
      <path d="M77 72 Q87 68 97 74" stroke="#8B4513" strokeWidth="4" fill="none" strokeLinecap="round" />
      <path d="M103 74 Q113 68 123 72" stroke="#8B4513" strokeWidth="4" fill="none" strokeLinecap="round" />

      {/* Nose */}
      <ellipse cx="100" cy="92" rx="8" ry="6" fill="#CD853F" />

      {/* Big beard */}
      <path
        d="M65 95 Q60 130 80 160 Q100 175 120 160 Q140 130 135 95"
        fill="#8B4513"
      />
      <path
        d="M70 100 Q65 125 85 150 Q100 160 115 150 Q135 125 130 100"
        fill="#A0522D"
      />

      {/* Smile under beard */}
      <path d="M90 100 Q100 108 110 100" stroke="#4A3728" strokeWidth="2" fill="none" strokeLinecap="round" />

      {/* Body/Tunic */}
      <path
        d="M60 155 L60 190 L140 190 L140 155 Q100 145 60 155"
        fill="#654321"
      />
      {/* Belt */}
      <rect x="60" y="165" width="80" height="10" fill="#4A3728" />
      <rect x="95" y="163" width="10" height="14" fill="#FFD700" rx="2" />

      {/* Arms */}
      <ellipse cx="50" cy="165" rx="12" ry="20" fill="#DEB887" />
      <ellipse cx="150" cy="165" rx="12" ry="20" fill="#DEB887" />

      {/* Pickaxe in hand */}
      <g transform="translate(145, 140) rotate(30)">
        {/* Handle */}
        <rect x="-3" y="0" width="6" height="50" fill="#8B4513" rx="2" />
        {/* Head */}
        <path d="M-20 0 L20 0 L15 -8 L-15 -8 Z" fill="#708090" />
        <path d="M15 0 L35 -15 L30 -20 L12 -8" fill="#708090" />
        <path d="M-15 0 L-35 -15 L-30 -20 L-12 -8" fill="#708090" />
        {/* Metallic shine */}
        <path d="M-10 -4 L10 -4" stroke="#A9A9A9" strokeWidth="2" />
        {animated && (
          <animateTransform
            attributeName="transform"
            type="rotate"
            values="0;5;0;-5;0"
            dur="1s"
            repeatCount="indefinite"
          />
        )}
      </g>

      {/* Gold nugget sparkles around */}
      {animated && (
        <>
          <circle cx="35" cy="120" r="3" fill="#FFD700">
            <animate attributeName="opacity" values="0;1;0" dur="1.5s" repeatCount="indefinite" />
          </circle>
          <circle cx="165" cy="100" r="2" fill="#FFD700">
            <animate attributeName="opacity" values="0;1;0" dur="2s" repeatCount="indefinite" begin="0.5s" />
          </circle>
          <circle cx="45" cy="80" r="2" fill="#FFD700">
            <animate attributeName="opacity" values="0;1;0" dur="1.8s" repeatCount="indefinite" begin="0.3s" />
          </circle>
        </>
      )}
    </svg>
  )
}
