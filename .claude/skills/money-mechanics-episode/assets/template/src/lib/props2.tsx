import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, G, R, T} from './rough';

/** Warehouse store interior: tall racking with boxes, high ceiling lights. Floor at y=1010. */
export const Warehouse: React.FC<{draw?: number}> = ({draw = 1}) => (
	<g>
		{[0, 1, 2].map((i) => (
			<g key={i} transform={`translate(${i * 640} 0)`}>
				<R s={{kind: 'line', x1: 60, y1: 200, x2: 60, y2: 1010}} o={{strokeWidth: 6, stroke: C.blue}} draw={draw} seed={1000 + i} />
				<R s={{kind: 'line', x1: 580, y1: 200, x2: 580, y2: 1010}} o={{strokeWidth: 6, stroke: C.blue}} draw={draw} seed={1010 + i} />
				{[420, 640, 860].map((y, j) => (
					<g key={y}>
						<R s={{kind: 'line', x1: 60, y1: y, x2: 580, y2: y}} o={{strokeWidth: 6, stroke: C.red}} draw={draw} seed={1020 + i * 3 + j} />
						{[0, 1, 2, 3].map((b) => (
							<R
								key={b}
								s={{kind: 'rect', x: 80 + b * 125, y: y - 120 + ((b + j) % 2) * 20, w: 105, h: 120 - ((b + j) % 2) * 20}}
								o={{fill: '#D9B98C', fillStyle: 'hachure', hachureGap: 12}}
								draw={draw}
								seed={1040 + i * 12 + j * 4 + b}
								boil={false}
							/>
						))}
					</g>
				))}
			</g>
		))}
		{[300, 960, 1620].map((x, i) => (
			<R key={x} s={{kind: 'line', x1: x - 120, y1: 90, x2: x + 120, y2: 90}} o={{strokeWidth: 10, stroke: C.shadow}} draw={draw} seed={1090 + i} />
		))}
	</g>
);

/** Membership card, origin centre (~300x190). */
export const MemberCard: React.FC<{draw?: number; exec?: boolean; seed?: number}> = ({draw = 1, exec = false, seed = 1}) => (
	<g>
		<R s={{kind: 'rect', x: -150, y: -95, w: 300, h: 190}} o={{fill: exec ? C.ink : C.white, fillStyle: 'solid'}} draw={draw} seed={1100 + seed} boil={false} />
		<R s={{kind: 'rect', x: -150, y: -95, w: 300, h: 50}} o={{fill: exec ? C.gold : C.red, fillStyle: 'solid'}} draw={draw} seed={1110 + seed} boil={false} />
		<T x={0} y={-68} size={30} font="marker" color={exec ? C.ink : C.white} scale={Math.min(1, draw)}>
			{exec ? 'EXECUTIVE' : 'MEMBER'}
		</T>
		<R s={{kind: 'rect', x: -125, y: -25, w: 70, h: 90}} o={{fill: C.skin, fillStyle: 'solid'}} draw={draw} seed={1120 + seed} boil={false} />
		{[0, 1, 2].map((i) => (
			<R key={i} s={{kind: 'line', x1: -30, y1: -10 + i * 30, x2: 120 - i * 30, y2: -10 + i * 30}} o={{strokeWidth: 4, stroke: exec ? C.gold : C.shadow}} draw={draw} seed={1130 + seed * 3 + i} boil={false} />
		))}
	</g>
);

/** Hot dog + cup combo, origin centre. */
export const HotDog: React.FC<{draw?: number}> = ({draw = 1}) => (
	<g>
		<R s={{kind: 'ellipse', x: -60, y: 20, w: 220, h: 70}} o={{fill: '#E8B067', fillStyle: 'solid'}} draw={draw} seed={1200} />
		<R s={{kind: 'ellipse', x: -60, y: 8, w: 230, h: 40}} o={{fill: '#C0533A', fillStyle: 'solid'}} draw={draw} seed={1201} />
		<R s={{kind: 'curve', pts: [[-160, 4], [-120, -4], [-80, 8], [-40, -4], [0, 8], [40, 2]]}} o={{stroke: C.yellow, strokeWidth: 7}} draw={draw} seed={1202} />
		<R s={{kind: 'polygon', pts: [[90, -90], [190, -90], [175, 60], [105, 60]]}} o={{fill: C.red, fillStyle: 'hachure'}} draw={draw} seed={1203} />
		<R s={{kind: 'line', x1: 160, y1: -90, x2: 175, y2: -150}} o={{strokeWidth: 6}} draw={draw} seed={1204} />
	</g>
);

/** Roast chicken, origin centre. */
export const Chicken: React.FC<{draw?: number; glow?: boolean}> = ({draw = 1, glow = false}) => {
	const frame = useCurrentFrame();
	return (
		<g>
			{glow && <R s={{kind: 'circle', x: 0, y: 0, d: 300 + Math.sin(frame / 6) * 12}} o={{stroke: C.yellow, strokeWidth: 10}} seed={1210} />}
			<R s={{kind: 'ellipse', x: 0, y: 10, w: 220, h: 150}} o={{fill: '#C98A3C', fillStyle: 'cross-hatch'}} draw={draw} seed={1211} />
			<R s={{kind: 'ellipse', x: -100, y: 50, w: 70, h: 45}} o={{fill: '#C98A3C', fillStyle: 'solid'}} draw={draw} seed={1212} />
			<R s={{kind: 'ellipse', x: 100, y: 50, w: 70, h: 45}} o={{fill: '#C98A3C', fillStyle: 'solid'}} draw={draw} seed={1213} />
			<R s={{kind: 'circle', x: -130, y: 62, d: 22}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={1214} />
			<R s={{kind: 'circle', x: 130, y: 62, d: 22}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={1215} />
		</g>
	);
};

/** Shopping cart, origin at bottom centre of basket. */
export const Cart: React.FC<{draw?: number; children?: React.ReactNode}> = ({draw = 1, children}) => (
	<g>
		{children}
		<R s={{kind: 'polygon', pts: [[-170, -200], [170, -200], [140, 0], [-140, 0]]}} o={{fill: C.shadow, fillStyle: 'cross-hatch', hachureGap: 18}} draw={draw} seed={1220} />
		<R s={{kind: 'line', x1: 170, y1: -200, x2: 230, y2: -250}} o={{strokeWidth: 7}} draw={draw} seed={1221} />
		<R s={{kind: 'line', x1: -140, y1: 0, x2: -150, y2: 60}} o={{strokeWidth: 5}} draw={draw} seed={1222} />
		<R s={{kind: 'line', x1: 140, y1: 0, x2: 150, y2: 60}} o={{strokeWidth: 5}} draw={draw} seed={1223} />
		<R s={{kind: 'circle', x: -150, y: 75, d: 36}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={1224} />
		<R s={{kind: 'circle', x: 150, y: 75, d: 36}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={1225} />
	</g>
);

export const TV: React.FC<{draw?: number}> = ({draw = 1}) => (
	<g>
		<R s={{kind: 'rect', x: -130, y: -85, w: 260, h: 160}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={1230} />
		<R s={{kind: 'rect', x: -115, y: -72, w: 230, h: 134}} o={{fill: C.blue, fillStyle: 'hachure'}} draw={draw} seed={1231} />
		<R s={{kind: 'line', x1: 0, y1: 75, x2: 0, y2: 105}} o={{strokeWidth: 8}} draw={draw} seed={1232} />
		<R s={{kind: 'line', x1: -50, y1: 105, x2: 50, y2: 105}} o={{strokeWidth: 8}} draw={draw} seed={1233} />
	</g>
);

export const PaperTowels: React.FC<{draw?: number}> = ({draw = 1}) => (
	<g>
		{[0, 1, 2, 3].map((i) => (
			<g key={i}>
				<R s={{kind: 'rect', x: -100 + (i % 2) * 100, y: -110 + Math.floor(i / 2) * 110, w: 95, h: 105}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={1240 + i} />
				<R s={{kind: 'circle', x: -52 + (i % 2) * 100, y: -58 + Math.floor(i / 2) * 110, d: 28}} o={{fill: C.shadow, fillStyle: 'solid'}} draw={draw} seed={1250 + i} />
			</g>
		))}
	</g>
);

export const Kayak: React.FC<{draw?: number}> = ({draw = 1}) => (
	<g>
		<R s={{kind: 'path', d: 'M -260 0 C -150 -50 150 -50 260 0 C 150 40 -150 40 -260 0 Z'}} o={{fill: C.yellow, fillStyle: 'hachure'}} draw={draw} seed={1260} />
		<R s={{kind: 'ellipse', x: 0, y: -6, w: 110, h: 30}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={1261} />
		<R s={{kind: 'line', x1: -170, y1: -90, x2: 170, y2: 60}} o={{strokeWidth: 6, stroke: C.brown}} draw={draw} seed={1262} />
	</g>
);

/** Long receipt unrolling; p = 0..1 unroll. Origin top centre. */
export const Receipt: React.FC<{p: number; lines: string[]; total: string}> = ({p, lines, total}) => {
	const h = 80 + lines.length * 50 + 120;
	const hh = h * p;
	if (hh < 2) return null;
	return (
		<g>
			<R s={{kind: 'rect', x: -170, y: 0, w: 340, h: hh}} o={{fill: C.white, fillStyle: 'solid'}} seed={1270} boil={false} />
			{lines.map((l, i) =>
				80 + i * 50 < hh ? (
					<T key={l} x={0} y={60 + i * 50} size={34}>
						{l}
					</T>
				) : null,
			)}
			{p >= 1 && (
				<>
					<R s={{kind: 'line', x1: -140, y1: h - 110, x2: 140, y2: h - 110}} o={{strokeWidth: 3, strokeLineDash: [8, 8]}} seed={1271} />
					<T x={0} y={h - 55} size={58} font="marker" color={C.red}>
						{total}
					</T>
				</>
			)}
		</g>
	);
};

/** Vault / safe, origin centre. */
export const Vault: React.FC<{draw?: number; open?: number}> = ({draw = 1, open = 0}) => (
	<g>
		<R s={{kind: 'rect', x: -200, y: -200, w: 400, h: 400}} o={{fill: C.shadow, fillStyle: 'cross-hatch'}} draw={draw} seed={1280} />
		<G x={-200 + 400 * open * 0.0} y={0}>
			<R s={{kind: 'circle', x: 0, y: 0, d: 150}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={1281} />
			{[0, 60, 120].map((a, i) => (
				<R key={a} s={{kind: 'line', x1: 0, y1: 0, x2: Math.cos((a * Math.PI) / 180) * 70, y2: Math.sin((a * Math.PI) / 180) * 70}} o={{strokeWidth: 6}} draw={draw} seed={1282 + i} />
			))}
		</G>
	</g>
);

/** Casino sign with flashing bulbs, origin centre. */
export const CasinoSign: React.FC<{draw?: number}> = ({draw = 1}) => {
	const frame = useCurrentFrame();
	return (
		<g>
			<R s={{kind: 'rect', x: -280, y: -110, w: 560, h: 220}} o={{fill: C.ink, fillStyle: 'solid', stroke: C.gold, strokeWidth: 6}} draw={draw} seed={1290} />
			{Array.from({length: 18}).map((_, i) => {
				const on = (Math.floor(frame / 4) + i) % 3 === 0;
				const x = -260 + (i % 9) * 65;
				const y = i < 9 ? -95 : 95;
				return <R key={i} s={{kind: 'circle', x, y, d: 18}} o={{fill: on ? C.yellow : '#6B5B2A', fillStyle: 'solid', stroke: 'none'}} seed={1300 + i} boil={false} />;
			})}
			<T x={0} y={6} size={110} font="marker" color={C.red} scale={Math.min(1, draw)}>
				CASINO
			</T>
		</g>
	);
};

/** Calculator, origin centre. Shows `display`. */
export const Calculator: React.FC<{display: string; draw?: number}> = ({display, draw = 1}) => (
	<g>
		<R s={{kind: 'rect', x: -170, y: -240, w: 340, h: 480}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={1320} />
		<R s={{kind: 'rect', x: -145, y: -215, w: 290, h: 110}} o={{fill: '#9BE7B4', fillStyle: 'solid'}} draw={draw} seed={1321} />
		<T x={130} y={-158} size={56} font="marker" anchor="end" scale={Math.min(1, draw)}>
			{display}
		</T>
		{Array.from({length: 12}).map((_, i) => (
			<R key={i} s={{kind: 'rect', x: -140 + (i % 3) * 100, y: -80 + Math.floor(i / 3) * 75, w: 80, h: 58}} o={{fill: i % 3 === 2 ? C.yellow : C.shadow, fillStyle: 'solid'}} draw={draw} seed={1330 + i} boil={false} />
		))}
	</g>
);
