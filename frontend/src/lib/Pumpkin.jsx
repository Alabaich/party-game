import { useEffect, useMemo, useState } from 'react'
import QR from 'qrcode'

// A carved jack-o'-lantern whose belly is a scannable QR code. When `announce`
// is set, the QR melts into a face, the mouth opens and the name rises out of it.
//
// QR is drawn as black modules on a lighter carved plate: scanners need contrast
// and an even quiet zone, which the ribbed gradient of the body wouldn't give.

const DARK = '#1c0a03'

function useQrModules(value) {
  return useMemo(() => {
    try {
      const qr = QR.create(value, { errorCorrectionLevel: 'M' })
      const { size, data } = qr.modules
      const cells = []
      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) if (data[y * size + x]) cells.push([x, y])
      }
      return { size, cells }
    } catch {
      return { size: 21, cells: [] }
    }
  }, [value])
}

export default function Pumpkin({ value, announce, subtitle = 'JUST JOINED!', onClick, className = '' }) {
  const { size, cells } = useQrModules(value)
  // QR plate geometry (viewBox units)
  const plate = 250
  const quiet = 3
  const unit = plate / (size + quiet * 2)
  const px = 300 - plate / 2
  const py = 315 - plate / 2

  const face = !!announce
  // keep the last text while the face fades out
  const [shown, setShown] = useState({ announce, subtitle })
  useEffect(() => { if (announce) setShown({ announce, subtitle }) }, [announce, subtitle])
  const name = (shown.announce || '').slice(0, 24)
  const nameSize = name.length > 16 ? 36 : name.length > 11 ? 46 : name.length > 7 ? 56 : 66

  return (
    <svg viewBox="0 0 600 560" className={`pumpkin ${face ? 'is-face' : ''} ${onClick ? 'cursor-pointer' : ''} ${className}`}
      role="img" onClick={onClick}
      aria-label={face ? `${name} ${shown.subtitle}` : 'Scan the QR code to join'}>
      <defs>
        <radialGradient id="pk-body" cx="50%" cy="40%" r="65%">
          <stop offset="0%" stopColor="#ffa53a" />
          <stop offset="55%" stopColor="#ff8a1f" />
          <stop offset="100%" stopColor="#c9500a" />
        </radialGradient>
        <linearGradient id="pk-rib" x1="0" x2="1">
          <stop offset="0%" stopColor="#d9600c" />
          <stop offset="50%" stopColor="#ff9a2e" />
          <stop offset="100%" stopColor="#d9600c" />
        </linearGradient>
        <radialGradient id="pk-glow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="#ffe08a" />
          <stop offset="60%" stopColor="#ffb23e" />
          <stop offset="100%" stopColor="#ff7a00" />
        </radialGradient>
        <radialGradient id="pk-maw" cx="50%" cy="60%" r="70%">
          <stop offset="0%" stopColor="#4a1200" />
          <stop offset="55%" stopColor="#220700" />
          <stop offset="100%" stopColor={DARK} />
        </radialGradient>
        <filter id="pk-text-glow" x="-30%" y="-60%" width="160%" height="220%">
          <feGaussianBlur stdDeviation="6" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="pk-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="18" stdDeviation="16" floodColor="#000" floodOpacity="0.55" />
        </filter>
      </defs>

      <g className="pk-wobble" filter="url(#pk-shadow)">
        {/* stem */}
        <path d="M292 92 C288 64 300 40 326 26 C334 22 342 30 336 38 C322 56 318 74 322 96 Z" fill="#3f7a22" />
        <path d="M300 90 C300 70 310 50 326 36" stroke="#2c5a16" strokeWidth="5" fill="none" strokeLinecap="round" />
        {/* body: outer lobes, then inner lobes, then centre */}
        <ellipse cx="160" cy="320" rx="140" ry="215" fill="url(#pk-rib)" />
        <ellipse cx="440" cy="320" rx="140" ry="215" fill="url(#pk-rib)" />
        <ellipse cx="220" cy="315" rx="140" ry="228" fill="url(#pk-body)" />
        <ellipse cx="380" cy="315" rx="140" ry="228" fill="url(#pk-body)" />
        <ellipse cx="300" cy="312" rx="150" ry="236" fill="url(#pk-body)" />
        {/* rib shading */}
        {[[205, 0.18], [395, 0.18], [130, 0.22], [470, 0.22]].map(([x, o]) => (
          <path key={x} d={`M${x} 110 C${x + (x < 300 ? -30 : 30)} 250 ${x + (x < 300 ? -30 : 30)} 400 ${x} 530`}
            stroke="#8a3304" strokeOpacity={o} strokeWidth="6" fill="none" strokeLinecap="round" />
        ))}
        <ellipse cx="250" cy="170" rx="42" ry="18" fill="#fff" opacity="0.12" transform="rotate(-25 250 170)" />

        {/* QR on a carved, lighter plate */}
        <g className="pk-qr">
          <rect x={px - 10} y={py - 10} width={plate + 20} height={plate + 20} rx="26" fill="#a8440a" opacity="0.55" />
          <rect x={px} y={py} width={plate} height={plate} rx="18" fill="#ffd9a3" />
          <g transform={`translate(${px + quiet * unit} ${py + quiet * unit})`} fill={DARK} shapeRendering="crispEdges">
            {cells.map(([x, y]) => (
              <rect key={`${x}-${y}`} x={x * unit} y={y * unit} width={unit + 0.3} height={unit + 0.3} />
            ))}
          </g>
        </g>

        {/* carved face — angry eyes, big square maw with jagged teeth */}
        <g className="pk-face">
          {/* furrowed brows & a crack: carved scratches */}
          <g className="pk-eyes" stroke="#7a2a02" strokeWidth="6" strokeLinecap="round" fill="none" opacity="0.8">
            <path d="M170 168 Q215 150 262 186" />
            <path d="M430 168 Q385 150 338 186" />
            <path d="M300 118 L292 140 L304 152 L296 172" strokeWidth="4" />
          </g>
          <g className="pk-eyes">
            {/* rim = cut flesh, then the dark hole */}
            <path d="M162 196 L272 238 L254 272 L178 258 Z" fill="#ffd27a" />
            <path d="M168 202 L266 240 L250 266 L182 253 Z" fill={DARK} />
            <path d="M438 196 L328 238 L346 272 L422 258 Z" fill="#ffd27a" />
            <path d="M432 202 L334 240 L350 266 L418 253 Z" fill={DARK} />
            <circle cx="224" cy="248" r="7" fill="#ff5a1a" className="pk-pupil" />
            <circle cx="376" cy="248" r="7" fill="#ff5a1a" className="pk-pupil" />
            <path d="M280 300 L320 300 L300 266 Z" fill="#ffd27a" />
            <path d="M285 297 L315 297 L300 272 Z" fill={DARK} />
          </g>
          <g className="pk-mouth">
            {/* the opening itself: teeth are just uncut pumpkin, the light rim
                follows the cut edge (zigzag teeth included), not a box around it */}
            <path d="M136 318 L156 352 L176 314 L196 346 L218 312 L238 340 L262 310 L282 338 L300 309
                     L318 338 L338 310 L362 340 L382 312 L404 346 L424 314 L444 352 L464 318
                     L458 492 L440 462 L420 496 L396 468 L374 500 L350 472 L326 503 L300 474
                     L274 503 L250 472 L226 500 L204 468 L180 496 L160 462 L142 492 Z"
              fill="url(#pk-maw)" stroke="#ffd27a" strokeWidth="5" strokeLinejoin="round" />
          </g>
          <g className="pk-name" filter="url(#pk-text-glow)">
            <text x="300" y="418" textAnchor="middle" fontFamily='"Bricolage Grotesque", system-ui, sans-serif'
              fontWeight="800" fontSize={nameSize} fill="#ffd65e">{name}</text>
            <text x="300" y="452" textAnchor="middle" fontFamily='"Space Mono", monospace'
              fontWeight="700" fontSize="20" letterSpacing="3" fill="#ffae3a">{shown.subtitle}</text>
          </g>
        </g>
      </g>
    </svg>
  )
}
