import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, G, R, T} from './rough';

/** Paper background with faint hand-drawn grain lines. */
export const Paper: React.FC = () => (
	<>
		<rect x={0} y={0} width={1920} height={1080} fill={C.paper} />
		<R s={{kind: 'line', x1: 0, y1: 1010, x2: 1920, y2: 1012}} o={{stroke: C.shadow, strokeWidth: 2, roughness: 2}} seed={901} />
	</>
);

/** Pawn shop interior: shelves, neon sign, counter. Counter top sits at y=760. */
export const PawnShop: React.FC<{draw?: number; neon?: string; neonColor?: string}> = ({draw = 1, neon = 'PAWN', neonColor = C.red}) => {
	const frame = useCurrentFrame();
	const flicker = frame % 47 < 2 ? 0.35 : 1;
	return (
		<g>
			{/* back wall shelves */}
			{[300, 480].map((y, i) => (
				<R key={y} s={{kind: 'line', x1: 1000, y1: y, x2: 1840, y2: y}} o={{strokeWidth: 5}} draw={draw} seed={300 + i} />
			))}
			{/* shelf items: tv, trumpet-ish horn, clock, boxes */}
			<R s={{kind: 'rect', x: 1040, y: 200, w: 130, h: 98}} o={{fill: C.blue, fillStyle: 'hachure'}} draw={draw} seed={310} />
			<R s={{kind: 'circle', x: 1290, y: 250, d: 90}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={311} />
			<R s={{kind: 'line', x1: 1290, y1: 250, x2: 1290, y2: 220}} o={{strokeWidth: 3}} draw={draw} seed={312} />
			<R s={{kind: 'line', x1: 1290, y1: 250, x2: 1312, y2: 262}} o={{strokeWidth: 3}} draw={draw} seed={313} />
			<R s={{kind: 'rect', x: 1400, y: 230, w: 80, h: 68}} o={{fill: C.gold, fillStyle: 'cross-hatch'}} draw={draw} seed={314} />
			<R s={{kind: 'rect', x: 1520, y: 190, w: 60, h: 108}} o={{fill: C.green, fillStyle: 'hachure'}} draw={draw} seed={315} />
			<R s={{kind: 'ellipse', x: 1720, y: 262, w: 140, h: 70}} o={{fill: C.shadow, fillStyle: 'hachure'}} draw={draw} seed={316} />
			<R s={{kind: 'rect', x: 1060, y: 400, w: 70, h: 78}} o={{fill: C.red, fillStyle: 'hachure'}} draw={draw} seed={317} />
			<R s={{kind: 'circle', x: 1250, y: 440, d: 70}} o={{fill: C.gold, fillStyle: 'solid'}} draw={draw} seed={318} />
			<R s={{kind: 'rect', x: 1370, y: 380, w: 150, h: 98}} o={{fill: C.shadow, fillStyle: 'cross-hatch'}} draw={draw} seed={319} />
			<R s={{kind: 'rect', x: 1600, y: 410, w: 180, h: 68}} o={{fill: C.blue, fillStyle: 'hachure'}} draw={draw} seed={320} />
			{/* neon sign */}
			<G x={420} y={170} o={flicker * Math.min(1, draw)}>
				<R s={{kind: 'rect', x: -190, y: -70, w: 380, h: 140}} o={{stroke: neonColor, strokeWidth: 6}} draw={draw} seed={330} />
				<T x={0} y={4} size={96} font="marker" color={neonColor}>
					{neon}
				</T>
			</G>
			{/* three golden balls: the pawnbroker's symbol */}
			{[
				[700, 120],
				[760, 120],
				[730, 175],
			].map(([x, y], i) => (
				<R key={i} s={{kind: 'circle', x, y, d: 54}} o={{fill: C.gold, fillStyle: 'solid'}} draw={draw} seed={340 + i} />
			))}
			{/* counter */}
			<R s={{kind: 'rect', x: 980, y: 760, w: 900, h: 260}} o={{fill: C.brown, fillStyle: 'hachure', hachureAngle: 80}} draw={draw} seed={350} />
			<R s={{kind: 'rect', x: 960, y: 740, w: 940, h: 30}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={351} />
		</g>
	);
};

export const Cash: React.FC<{thick?: boolean; draw?: number}> = ({thick = false, draw = 1}) => (
	<g>
		{Array.from({length: thick ? 5 : 2}).map((_, i) => (
			<R key={i} s={{kind: 'rect', x: -60, y: -30 - i * 8, w: 120, h: 56}} o={{fill: C.green, fillStyle: 'solid'}} draw={draw} seed={400 + i} />
		))}
		<T x={0} y={thick ? -32 : -6} size={34} color={C.white} font="marker">
			$
		</T>
	</g>
);

export const Coin: React.FC<{draw?: number; seed?: number}> = ({draw = 1, seed = 1}) => (
	<g>
		<R s={{kind: 'circle', x: 0, y: 0, d: 60}} o={{fill: C.gold, fillStyle: 'solid'}} draw={draw} seed={410 + seed} />
		<T x={0} y={2} size={36} font="marker" color={C.ink}>
			$
		</T>
	</g>
);

/** Glass jar; `level` 0..1 fills it with coins. Origin at jar bottom centre. */
export const Jar: React.FC<{level?: number; label?: string; draw?: number}> = ({level = 0, label = 'FEES', draw = 1}) => {
	const h = 300 * Math.min(1, level);
	return (
		<g>
			{h > 0 && <R s={{kind: 'rect', x: -95, y: -h, w: 190, h}} o={{fill: C.gold, fillStyle: 'cross-hatch', stroke: 'none'}} seed={420} />}
			<R
				s={{kind: 'path', d: 'M -110 -340 L -110 -10 C -110 5 110 5 110 -10 L 110 -340'}}
				o={{strokeWidth: 5}}
				draw={draw}
				seed={421}
			/>
			<R s={{kind: 'rect', x: -125, y: -380, w: 250, h: 40}} o={{fill: C.shadow, fillStyle: 'solid'}} draw={draw} seed={422} />
			<R s={{kind: 'rect', x: -80, y: -230, w: 160, h: 70}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={423} />
			<T x={0} y={-193} size={44} font="marker" color={C.red}>
				{label}
			</T>
		</g>
	);
};

export const Car: React.FC<{draw?: number; light?: boolean}> = ({draw = 1, light = false}) => {
	const frame = useCurrentFrame();
	const on = light && frame % 20 < 12;
	return (
		<g>
			<R s={{kind: 'path', d: 'M -260 0 L -260 -90 L -150 -100 L -90 -180 L 110 -180 L 180 -100 L 260 -80 L 260 0 Z'}} o={{fill: C.blue, fillStyle: 'hachure'}} draw={draw} seed={430} />
			<R s={{kind: 'polygon', pts: [[-130, -105], [-80, -165], [0, -165], [0, -105]]}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={431} />
			<R s={{kind: 'polygon', pts: [[20, -105], [20, -165], [100, -165], [150, -105]]}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={432} />
			<R s={{kind: 'circle', x: -150, y: 0, d: 100}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={433} />
			<R s={{kind: 'circle', x: 150, y: 0, d: 100}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={434} />
			{on && (
				<G x={0} y={-290}>
					<R s={{kind: 'polygon', pts: [[0, -70], [75, 60], [-75, 60]]}} o={{fill: C.yellow, fillStyle: 'solid', stroke: C.red, strokeWidth: 6}} seed={435} />
					<T x={0} y={20} size={80} font="marker" color={C.red}>
						!
					</T>
				</G>
			)}
		</g>
	);
};

export const Phone: React.FC<{draw?: number; children?: React.ReactNode}> = ({draw = 1, children}) => (
	<g>
		<R s={{kind: 'rect', x: -130, y: -240, w: 260, h: 480}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={440} />
		<R s={{kind: 'rect', x: -112, y: -205, w: 224, h: 400}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={441} />
		{children}
	</g>
);

/** Paper card with text, origin centre. */
export const Card: React.FC<{w: number; h: number; fill?: string; seed?: number; draw?: number; children?: React.ReactNode}> = ({
	w,
	h,
	fill = C.white,
	seed = 1,
	draw = 1,
	children,
}) => (
	<g>
		<R s={{kind: 'rect', x: -w / 2 + 8, y: -h / 2 + 10, w, h}} o={{fill: C.shadow, fillStyle: 'solid', stroke: 'none'}} draw={draw} seed={450 + seed} boil={false} />
		<R s={{kind: 'rect', x: -w / 2, y: -h / 2, w, h}} o={{fill, fillStyle: 'solid'}} draw={draw} seed={460 + seed} />
		{children}
	</g>
);

/** A gear with N teeth, origin centre. */
export const Gear: React.FC<{r: number; teeth?: number; rot?: number; fill?: string; seed?: number; draw?: number; label?: string}> = ({
	r,
	teeth = 10,
	rot = 0,
	fill = C.shadow,
	seed = 1,
	draw = 1,
	label,
}) => {
	const pts: [number, number][] = [];
	for (let i = 0; i < teeth * 2; i++) {
		const a = (i / (teeth * 2)) * Math.PI * 2;
		const rr = i % 2 === 0 ? r : r * 0.82;
		pts.push([Math.cos(a) * rr, Math.sin(a) * rr]);
		const a2 = ((i + 0.6) / (teeth * 2)) * Math.PI * 2;
		pts.push([Math.cos(a2) * rr, Math.sin(a2) * rr]);
	}
	return (
		<g>
			<g transform={`rotate(${rot})`}>
				<R s={{kind: 'polygon', pts}} o={{fill, fillStyle: 'hachure'}} draw={draw} seed={470 + seed} boil={false} />
				<R s={{kind: 'circle', x: 0, y: 0, d: r * 0.9}} o={{fill: C.paper, fillStyle: 'solid'}} draw={draw} seed={480 + seed} boil={false} />
			</g>
			{label && (
				<T x={0} y={2} size={r * 0.32} font="marker" scale={Math.min(1, draw)}>
					{label}
				</T>
			)}
		</g>
	);
};

/** Tick mark. */
export const Tick: React.FC<{draw?: number; seed?: number; color?: string}> = ({draw = 1, seed = 1, color = C.green}) => (
	<R s={{kind: 'curve', pts: [[-22, 0], [-6, 18], [26, -26]]}} o={{stroke: color, strokeWidth: 9}} draw={draw} seed={490 + seed} />
);

/** Cross mark. */
export const Cross: React.FC<{draw?: number; seed?: number; size?: number}> = ({draw = 1, seed = 1, size = 40}) => (
	<g>
		<R s={{kind: 'line', x1: -size, y1: -size, x2: size, y2: size}} o={{stroke: C.red, strokeWidth: 10}} draw={Math.min(1, draw * 2)} seed={500 + seed} />
		<R s={{kind: 'line', x1: size, y1: -size, x2: -size, y2: size}} o={{stroke: C.red, strokeWidth: 10}} draw={Math.max(0, draw * 2 - 1)} seed={510 + seed} />
	</g>
);

/** Price tag, origin at the hole. */
export const PriceTag: React.FC<{text: string; draw?: number; seed?: number; fill?: string}> = ({text, draw = 1, seed = 1, fill = C.yellow}) => (
	<g>
		<R s={{kind: 'polygon', pts: [[0, 0], [50, -45], [230, -45], [230, 45], [50, 45]]}} o={{fill, fillStyle: 'solid'}} draw={draw} seed={520 + seed} />
		<R s={{kind: 'circle', x: 36, y: 0, d: 16}} o={{fill: C.paper, fillStyle: 'solid'}} draw={draw} seed={530 + seed} />
		<T x={140} y={4} size={52} font="marker" scale={Math.min(1, draw)}>
			{text}
		</T>
	</g>
);

/** Speech bubble, origin at bubble centre; tail points down-left by default. */
export const Bubble: React.FC<{w: number; h: number; draw?: number; tail?: 'left' | 'right'; children?: React.ReactNode}> = ({
	w,
	h,
	draw = 1,
	tail = 'left',
	children,
}) => {
	const tx = tail === 'left' ? -w / 4 : w / 4;
	return (
		<g>
			<R s={{kind: 'ellipse', x: 0, y: 0, w, h}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={540} />
			<R s={{kind: 'polygon', pts: [[tx - 20, h / 2 - 12], [tx + 20, h / 2 - 12], [tx + (tail === 'left' ? -40 : 40), h / 2 + 50]]}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={541} />
			{draw > 0.5 && children}
		</g>
	);
};
