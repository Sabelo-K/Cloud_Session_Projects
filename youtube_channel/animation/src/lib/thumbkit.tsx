import React from 'react';
import {AbsoluteFill} from 'remotion';
import {C, MARKER, R} from './rough';

/** Shared thumbnail kit: saturated sunburst backgrounds, chunky outlined headlines, arrows and glows. */

export const Burst: React.FC<{bg: string; ray: string; cx?: number; cy?: number}> = ({bg, ray, cx = 900, cy = 380}) => (
	<g>
		<rect x={0} y={0} width={1280} height={720} fill={bg} />
		{Array.from({length: 18}).map((_, i) => {
			const a0 = (i / 18) * Math.PI * 2;
			const a1 = a0 + Math.PI / 18;
			const r = 1600;
			return <path key={i} d={`M ${cx} ${cy} L ${cx + Math.cos(a0) * r} ${cy + Math.sin(a0) * r} L ${cx + Math.cos(a1) * r} ${cy + Math.sin(a1) * r} Z`} fill={ray} />;
		})}
		<defs>
			<radialGradient id="vig" cx="50%" cy="50%" r="75%">
				<stop offset="55%" stopColor="#000" stopOpacity={0} />
				<stop offset="100%" stopColor="#000" stopOpacity={0.45} />
			</radialGradient>
		</defs>
		<rect x={0} y={0} width={1280} height={720} fill="url(#vig)" />
	</g>
);

/** Soft glow behind the hero object. */
export const Glow: React.FC<{x: number; y: number; r: number; color?: string}> = ({x, y, r, color = C.yellow}) => (
	<g>
		<defs>
			<radialGradient id={`glow${x}${y}`}>
				<stop offset="0%" stopColor={color} stopOpacity={0.95} />
				<stop offset="100%" stopColor={color} stopOpacity={0} />
			</radialGradient>
		</defs>
		<circle cx={x} cy={y} r={r} fill={`url(#glow${x}${y})`} />
	</g>
);

/** Chunky headline: fill colour, thick ink outline, hard drop shadow. */
export const Headline: React.FC<{x: number; y: number; size: number; color?: string; rotate?: number; children: React.ReactNode}> = ({
	x,
	y,
	size,
	color = C.yellow,
	rotate = -4,
	children,
}) => {
	const common = {textAnchor: 'middle' as const, dominantBaseline: 'middle' as const, fontFamily: MARKER, fontSize: size, strokeLinejoin: 'round' as const, paintOrder: 'stroke' as const};
	return (
		<g transform={`translate(${x} ${y}) rotate(${rotate})`}>
			<text {...common} x={size * 0.06} y={size * 0.08} fill={C.ink} stroke={C.ink} strokeWidth={size / 4}>
				{children}
			</text>
			<text {...common} fill={color} stroke={C.ink} strokeWidth={size / 5.5}>
				{children}
			</text>
		</g>
	);
};

/** Big hand-drawn red arrow from (x1,y1) to (x2,y2). */
export const Arrow: React.FC<{x1: number; y1: number; x2: number; y2: number; color?: string}> = ({x1, y1, x2, y2, color = C.red}) => {
	const a = Math.atan2(y2 - y1, x2 - x1);
	const h = 70;
	const p1: [number, number] = [x2 - Math.cos(a - 0.5) * h, y2 - Math.sin(a - 0.5) * h];
	const p2: [number, number] = [x2 - Math.cos(a + 0.5) * h, y2 - Math.sin(a + 0.5) * h];
	const mx = (x1 + x2) / 2 - Math.sin(a) * 60;
	const my = (y1 + y2) / 2 + Math.cos(a) * 60;
	return (
		<g>
			<R s={{kind: 'curve', pts: [[x1, y1], [mx, my], [x2 - Math.cos(a) * 30, y2 - Math.sin(a) * 30]]}} o={{stroke: C.ink, strokeWidth: 30, roughness: 0.6}} seed={901} boil={false} />
			<R s={{kind: 'curve', pts: [[x1, y1], [mx, my], [x2 - Math.cos(a) * 30, y2 - Math.sin(a) * 30]]}} o={{stroke: color, strokeWidth: 18, roughness: 0.6}} seed={901} boil={false} />
			<R s={{kind: 'polygon', pts: [[x2, y2], p1, p2]}} o={{fill: color, fillStyle: 'solid', stroke: C.ink, strokeWidth: 6, roughness: 0.6}} seed={902} boil={false} />
		</g>
	);
};

/** Red hand-drawn ring around something. */
export const Ring: React.FC<{x: number; y: number; w: number; h: number}> = ({x, y, w, h}) => (
	<R s={{kind: 'ellipse', x, y, w, h}} o={{stroke: C.red, strokeWidth: 12, roughness: 2}} seed={903} boil={false} />
);

export const ThumbFrame: React.FC<{children: React.ReactNode}> = ({children}) => (
	<AbsoluteFill>
		<svg viewBox="0 0 1280 720" width="100%" height="100%">
			{children}
		</svg>
	</AbsoluteFill>
);

/** Penny with a solid paper backing behind her hachured hoodie, so busy backgrounds don't show through. */
export const ThumbPenny: React.FC<{children: React.ReactNode}> = ({children}) => (
	<g>
		<polygon points="-48,-230 48,-230 62,-105 -62,-105" fill={C.paper} />
		{children}
	</g>
);

/** Tilted ribbon banner with a catchphrase, centred at (x,y). */
export const Ribbon: React.FC<{x: number; y: number; w: number; text: string; bg?: string; color?: string; size?: number; rotate?: number}> = ({
	x,
	y,
	w,
	text,
	bg = C.ink,
	color = C.yellow,
	size = 54,
	rotate = -3,
}) => (
	<g transform={`translate(${x} ${y}) rotate(${rotate})`}>
		<rect x={-w / 2 + 8} y={-size * 0.75 + 10} width={w} height={size * 1.5} fill="#000" opacity={0.35} />
		<rect x={-w / 2} y={-size * 0.75} width={w} height={size * 1.5} fill={bg} stroke={C.white} strokeWidth={6} />
		<text textAnchor="middle" dominantBaseline="middle" fontFamily={MARKER} fontSize={size} fill={color} y={4}>
			{text}
		</text>
	</g>
);

/** "Breaking News" lower third: red BREAKING tab, white headline strip, dark ticker, plus a LIVE badge top-right. */
export const NewsBar: React.FC<{text: string; ticker?: string}> = ({text, ticker = 'MONEY MECHANICS  •  HOW THE MONEY REALLY MOVES  •  MONEY MECHANICS'}) => (
	<g>
		<g transform="translate(550 589)">
			<rect x={-70} y={-26} width={140} height={52} rx={6} fill="#D7141A" stroke={C.white} strokeWidth={4} />
			<circle cx={-40} cy={0} r={10} fill={C.white} />
			<text x={14} y={3} textAnchor="middle" dominantBaseline="middle" fontFamily="Arial Black, Arial, sans-serif" fontWeight={900} fontSize={30} fill={C.white}>
				LIVE
			</text>
		</g>
		<rect x={0} y={556} width={1280} height={164} fill="#000" opacity={0.25} />
		<rect x={0} y={560} width={430} height={58} fill="#D7141A" />
		<polygon points="430,560 462,560 430,618" fill="#D7141A" />
		<text x={24} y={591} dominantBaseline="middle" fontFamily="Arial Black, Arial, sans-serif" fontWeight={900} fontSize={40} fill={C.white} fontStyle="italic">
			BREAKING NEWS
		</text>
		<rect x={0} y={618} width={1280} height={66} fill={C.white} />
		<rect x={0} y={618} width={14} height={66} fill="#D7141A" />
		<text x={36} y={653} dominantBaseline="middle" fontFamily="Arial Black, Arial, sans-serif" fontWeight={900} fontSize={text.length > 24 ? 44 : 50} fill={C.ink}>
			{text}
		</text>
		<rect x={0} y={684} width={1280} height={36} fill="#111" />
		<rect x={0} y={684} width={150} height={36} fill={C.yellow} />
		<text x={75} y={703} textAnchor="middle" dominantBaseline="middle" fontFamily="Arial Black, Arial, sans-serif" fontWeight={900} fontSize={20} fill={C.ink}>
			MARKETS
		</text>
		<text x={170} y={703} dominantBaseline="middle" fontFamily="Arial, sans-serif" fontWeight={700} fontSize={20} fill={C.white}>
			{ticker}
		</text>
	</g>
);
