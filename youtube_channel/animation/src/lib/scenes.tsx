import React from 'react';
import {MARKER} from './rough';

/**
 * Topic backdrops for thumbnails, drawn in a 1280x720 space as soft silhouettes
 * (dark shapes + faint highlights) so they read as "place" without fighting the headline.
 */
export type SceneId =
	| 'pawn'
	| 'warehouse'
	| 'cards'
	| 'casino'
	| 'apps'
	| 'subs'
	| 'bnpl'
	| 'broke'
	| 'giftcards'
	| 'gym'
	| 'ink'
	| 'tvs'
	| 'airport';

const D = '#000';
const DO = 0.5; // silhouette opacity
const L = '#FFF';
const LO = 0.14; // highlight opacity

const Floor: React.FC<{y?: number}> = ({y = 600}) => <rect x={0} y={y} width={1280} height={720 - y} fill={D} opacity={0.3} />;

const Neon: React.FC<{x: number; y: number; text: string; color: string; size?: number}> = ({x, y, text, color, size = 70}) => (
	<g>
		<text x={x} y={y} textAnchor="middle" fontFamily={MARKER} fontSize={size} fill="none" stroke={color} strokeWidth={14} opacity={0.35}>
			{text}
		</text>
		<text x={x} y={y} textAnchor="middle" fontFamily={MARKER} fontSize={size} fill="none" stroke={color} strokeWidth={5} opacity={0.9}>
			{text}
		</text>
	</g>
);

const Shelves: React.FC<{y0: number; rows: number; gap: number}> = ({y0, rows, gap}) => (
	<g>
		{Array.from({length: rows}).map((_, i) => (
			<rect key={i} x={0} y={y0 + i * gap} width={1280} height={10} fill={D} opacity={0.4} />
		))}
	</g>
);

const Pawn = () => (
	<g>
		<Shelves y0={200} rows={3} gap={150} />
		{/* guitars hanging */}
		{[80, 200, 1120, 1230].map((x, i) => (
			<g key={i} opacity={DO} transform={`translate(${x} 60) rotate(${i % 2 ? 8 : -8})`}>
				<rect x={-6} y={0} width={12} height={110} fill={D} />
				<ellipse cx={0} cy={140} rx={34} ry={40} fill={D} />
				<ellipse cx={0} cy={200} rx={46} ry={52} fill={D} />
			</g>
		))}
		{/* watches, TVs, cameras on shelves */}
		{Array.from({length: 14}).map((_, i) => (
			<rect key={i} x={30 + i * 92} y={i % 2 ? 145 : 300} width={60} height={i % 2 ? 55 : 40} rx={6} fill={D} opacity={DO} />
		))}
		<Neon x={1040} y={120} text="PAWN" color="#FF3B6B" size={90} />
		<Floor />
	</g>
);

const Warehouse = () => (
	<g>
		{/* ceiling lights */}
		{[160, 480, 800, 1120].map((x) => (
			<g key={x}>
				<rect x={x - 60} y={20} width={120} height={14} fill={L} opacity={0.5} />
				<polygon points={`${x - 60},34 ${x + 60},34 ${x + 160},360 ${x - 160},360`} fill={L} opacity={0.05} />
			</g>
		))}
		{/* racks of boxes in perspective */}
		{[0, 1].map((side) =>
			Array.from({length: 4}).map((_, r) =>
				Array.from({length: 5}).map((__, c) => {
					const x = side ? 1280 - (c + 1) * 70 : c * 70;
					return <rect key={`${side}${r}${c}`} x={x + 6} y={130 + r * 115} width={58} height={95} fill={D} opacity={DO * (1 - c * 0.12)} />;
				}),
			),
		)}
		<Shelves y0={225} rows={4} gap={115} />
		<Floor y={590} />
	</g>
);

const Cards = () => (
	<g>
		{Array.from({length: 9}).map((_, i) => {
			const x = (i % 3) * 470 - 60 + (i % 2) * 60;
			const y = Math.floor(i / 3) * 250 - 30;
			return (
				<g key={i} transform={`translate(${x} ${y}) rotate(${(i % 3) * 8 - 8})`} opacity={0.35}>
					<rect width={330} height={205} rx={22} fill={D} />
					<rect x={30} y={60} width={56} height={42} rx={6} fill={L} opacity={0.5} />
					<rect x={30} y={150} width={200} height={14} rx={7} fill={L} opacity={0.4} />
				</g>
			);
		})}
		<Neon x={250} y={110} text="%" color="#FFD84D" size={120} />
	</g>
);

const Casino = () => (
	<g>
		{/* row of slot machines */}
		{Array.from({length: 9}).map((_, i) => (
			<g key={i} transform={`translate(${i * 150 - 20} 300)`} opacity={DO + 0.05}>
				<rect width={120} height={300} rx={12} fill={D} />
				<rect x={15} y={50} width={90} height={60} fill={L} opacity={0.35} />
				<circle cx={60} cy={20} r={14} fill={['#FF3B6B', '#FFD84D', '#4DD8FF'][i % 3]} opacity={0.9} />
			</g>
		))}
		{/* roulette wheel */}
		<g transform="translate(1110 150)" opacity={0.35}>
			<circle r={120} fill={D} />
			{Array.from({length: 18}).map((_, i) => (
				<path key={i} d={`M0 0 L${Math.cos((i / 18) * 6.283) * 110} ${Math.sin((i / 18) * 6.283) * 110} L${Math.cos(((i + 0.5) / 18) * 6.283) * 110} ${Math.sin(((i + 0.5) / 18) * 6.283) * 110}Z`} fill={i % 2 ? '#C62F35' : L} opacity={0.6} />
			))}
			<circle r={40} fill={D} />
		</g>
		<Neon x={220} y={130} text="JACKPOT" color="#FFD84D" size={80} />
		<Floor />
	</g>
);

const Apps = () => (
	<g>
		{Array.from({length: 40}).map((_, i) => (
			<rect key={i} x={(i % 10) * 132 + 10} y={Math.floor(i / 10) * 132 + 70} width={100} height={100} rx={26} fill={['#FF3B6B', '#4DD8FF', '#FFD84D', '#7CFF8A', L][i % 5]} opacity={0.2} />
		))}
		{[
			[180, 90],
			[1080, 230],
			[300, 480],
		].map(([x, y], i) => (
			<g key={i} opacity={0.5}>
				<circle cx={x} cy={y} r={34} fill="#E5484D" />
				<text x={x} y={y + 14} textAnchor="middle" fontFamily={MARKER} fontSize={40} fill={L}>
					{[9, 23, 99][i]}
				</text>
			</g>
		))}
	</g>
);

const Subs = () => (
	<g>
		{/* calendar grid with circled renewal dates */}
		<g opacity={0.3}>
			<rect x={40} y={40} width={1200} height={620} rx={20} fill={D} />
		</g>
		{Array.from({length: 35}).map((_, i) => {
			const x = 70 + (i % 7) * 165;
			const y = 70 + Math.floor(i / 7) * 115;
			const hit = [3, 9, 15, 22, 28].includes(i);
			return (
				<g key={i}>
					<rect x={x} y={y} width={150} height={100} rx={10} fill={L} opacity={0.07} />
					<text x={x + 14} y={y + 34} fontFamily={MARKER} fontSize={28} fill={L} opacity={0.3}>
						{i + 1}
					</text>
					{hit && <circle cx={x + 75} cy={y + 50} r={42} fill="none" stroke="#FF3B6B" strokeWidth={6} opacity={0.6} />}
				</g>
			);
		})}
	</g>
);

const Bnpl = () => (
	<g>
		{/* shopping bags */}
		{Array.from({length: 8}).map((_, i) => (
			<g key={i} transform={`translate(${i * 165 + 10} ${380 + (i % 2) * 40})`} opacity={DO}>
				<path d="M30 0 Q60 -60 90 0" fill="none" stroke={D} strokeWidth={10} />
				<rect x={0} y={0} width={120} height={150} rx={8} fill={D} />
			</g>
		))}
		{/* price tags */}
		{[150, 640, 1120].map((x, i) => (
			<g key={i} transform={`translate(${x} 120) rotate(${i * 10 - 10})`} opacity={0.35}>
				<polygon points="0,0 150,0 180,40 150,80 0,80" fill={L} opacity={0.5} />
				<text x={70} y={52} textAnchor="middle" fontFamily={MARKER} fontSize={34} fill={D}>
					1/4
				</text>
			</g>
		))}
		<Floor y={590} />
	</g>
);

const Broke = () => (
	<g>
		{/* street of storefronts */}
		{[
			['CHECK CASHING', '#4DD8FF'],
			['PAYDAY LOANS', '#FFD84D'],
			['ATM', '#7CFF8A'],
		].map(([t, c], i) => (
			<g key={i} transform={`translate(${i * 440 - 20} 150)`}>
				<rect width={420} height={450} fill={D} opacity={DO} />
				<rect x={30} y={170} width={360} height={230} fill={L} opacity={0.08} />
				<Neon x={210} y={110} text={t} color={c} size={t.length > 5 ? 46 : 80} />
			</g>
		))}
		<Floor y={600} />
	</g>
);

const GiftCards = () => (
	<g>
		{Array.from({length: 8}).map((_, i) => (
			<g key={i} transform={`translate(${(i % 4) * 330 + 20} ${Math.floor(i / 4) * 300 + 60}) rotate(${(i % 3) * 10 - 10})`} opacity={0.25}>
				{i % 2 ? (
					<>
						<rect width={220} height={180} fill={D} />
						<rect x={95} width={30} height={180} fill={L} opacity={0.6} />
						<rect y={75} width={220} height={30} fill={L} opacity={0.6} />
					</>
				) : (
					<>
						<rect width={260} height={160} rx={18} fill={D} />
						<text x={130} y={100} textAnchor="middle" fontFamily={MARKER} fontSize={60} fill={L} opacity={0.6}>
							GIFT
						</text>
					</>
				)}
			</g>
		))}
	</g>
);

const Gym = () => (
	<g>
		{/* treadmills */}
		{Array.from({length: 6}).map((_, i) => (
			<g key={i} transform={`translate(${i * 215 + 10} 400)`} opacity={DO}>
				<rect x={0} y={140} width={180} height={30} rx={8} fill={D} />
				<rect x={140} y={0} width={14} height={150} fill={D} />
				<rect x={110} y={-10} width={70} height={30} rx={6} fill={D} />
			</g>
		))}
		{/* dumbbell rack */}
		{Array.from({length: 7}).map((_, i) => (
			<g key={i} transform={`translate(${i * 180 + 60} 150)`} opacity={DO}>
				<rect x={0} y={-30} width={22} height={60} rx={6} fill={D} />
				<rect x={22} y={-6} width={70} height={12} fill={D} />
				<rect x={92} y={-30} width={22} height={60} rx={6} fill={D} />
			</g>
		))}
		<Neon x={1080} y={300} text="GYM" color="#7CFF8A" size={90} />
		<Floor y={590} />
	</g>
);

const Ink = () => (
	<g>
		{/* ink drips from the top */}
		{Array.from({length: 16}).map((_, i) => {
			const x = i * 82 + 20;
			const len = 80 + ((i * 53) % 200);
			const c = ['#00B3E6', '#E6008A', '#FFD400', '#111'][i % 4];
			return (
				<g key={i} opacity={0.4}>
					<rect x={x} y={0} width={34} height={len} rx={17} fill={c} />
					<circle cx={x + 17} cy={len + 14} r={17} fill={c} />
				</g>
			);
		})}
		{/* printers */}
		{[150, 1130].map((x) => (
			<g key={x} transform={`translate(${x - 120} 450)`} opacity={DO}>
				<rect width={240} height={110} rx={14} fill={D} />
				<rect x={40} y={-40} width={160} height={50} fill={L} opacity={0.4} />
			</g>
		))}
		<Floor y={600} />
	</g>
);

const Tvs = () => (
	<g>
		{/* electronics store TV wall */}
		{Array.from({length: 15}).map((_, i) => (
			<g key={i} transform={`translate(${(i % 5) * 256 + 18} ${Math.floor(i / 5) * 170 + 40})`}>
				<rect width={220} height={140} rx={8} fill={D} opacity={0.45} />
				<rect x={10} y={10} width={200} height={120} fill={['#4DD8FF', '#FFD84D', '#FF3B6B', '#7CFF8A'][i % 4]} opacity={0.1} />
			</g>
		))}
		<Floor y={560} />
	</g>
);

const Airport = () => (
	<g>
		{/* departure board */}
		<g opacity={0.45}>
			<rect x={40} y={40} width={520} height={300} rx={10} fill={D} />
			{['NYC  10:40  BOARDING', 'LAX  11:15  ON TIME', 'ATL  11:50  DELAYED', 'MIA  12:30  ON TIME'].map((t, i) => (
				<text key={t} x={70} y={110 + i * 62} fontFamily="Courier New, monospace" fontWeight={700} fontSize={34} fill="#FFD84D">
					{t}
				</text>
			))}
		</g>
		{/* plane through the window */}
		<g transform="translate(980 150) rotate(-12)" opacity={0.35}>
			<ellipse cx={0} cy={0} rx={220} ry={34} fill={L} />
			<polygon points="-30,0 60,0 -60,150 -110,150" fill={L} />
			<polygon points="-30,0 60,0 -60,-150 -110,-150" fill={L} />
			<polygon points="-200,0 -160,0 -220,-80 -250,-80" fill={L} />
		</g>
		{/* window frames */}
		{[0, 1, 2, 3].map((i) => (
			<rect key={i} x={600 + i * 170} y={0} width={14} height={600} fill={D} opacity={0.4} />
		))}
		<Floor y={600} />
	</g>
);

const MAP: Record<SceneId, React.FC> = {
	pawn: Pawn,
	warehouse: Warehouse,
	cards: Cards,
	casino: Casino,
	apps: Apps,
	subs: Subs,
	bnpl: Bnpl,
	broke: Broke,
	giftcards: GiftCards,
	gym: Gym,
	ink: Ink,
	tvs: Tvs,
	airport: Airport,
};

/** Draw a scene to fill a w x h canvas: scaled to cover for wide canvases, stacked for tall ones. */
export const Scene: React.FC<{id: SceneId; w: number; h: number}> = ({id, w, h}) => {
	const S = MAP[id];
	if (h > w) {
		const s = w / 1280;
		const rows = Math.ceil(h / (720 * s));
		return (
			<g>
				{Array.from({length: rows}).map((_, i) => (
					<g key={i} transform={`translate(0 ${i * 720 * s}) scale(${s})`}>
						<S />
					</g>
				))}
			</g>
		);
	}
	const s = Math.max(w / 1280, h / 720);
	return (
		<g transform={`translate(${(w - 1280 * s) / 2} ${(h - 720 * s) / 2}) scale(${s})`}>
			<S />
		</g>
	);
};
