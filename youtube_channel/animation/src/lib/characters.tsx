import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, R} from './rough';

export type Mood = 'neutral' | 'happy' | 'worried' | 'shocked' | 'thinking' | 'confident';

const blinkScale = (frame: number, offset = 0) => {
	const f = (frame + offset + 60) % 110;
	return f < 4 ? 0.15 : 1;
};

/**
 * Penny: the series mascot. Origin is at her feet (centre).
 * Roughly 380px tall at scale 1.
 */
export const Penny: React.FC<{
	mood?: Mood;
	draw?: number;
	walk?: boolean;
	wave?: boolean;
	look?: number; // -1 left .. 1 right
	holdGuitar?: boolean;
}> = ({mood = 'neutral', draw = 1, walk = false, wave = false, look = 0, holdGuitar = false}) => {
	const frame = useCurrentFrame();
	const sw = walk ? Math.sin(frame / 4) * 14 : 0;
	const bob = walk ? Math.abs(Math.sin(frame / 4)) * -6 : Math.sin(frame / 20) * 1.5;
	const blink = blinkScale(frame);
	const ex = look * 6;
	const waveA = wave ? Math.sin(frame / 3) * 18 : 0;
	const shocked = mood === 'shocked';

	return (
		<g transform={`translate(0 ${bob})`}>
			{/* legs */}
			<R s={{kind: 'line', x1: -18, y1: -110, x2: -22 - sw, y2: 0}} o={{strokeWidth: 6}} draw={draw} seed={11} />
			<R s={{kind: 'line', x1: 18, y1: -110, x2: 22 + sw, y2: 0}} o={{strokeWidth: 6}} draw={draw} seed={12} />
			<R s={{kind: 'ellipse', x: -26 - sw, y: 0, w: 34, h: 14}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={13} />
			<R s={{kind: 'ellipse', x: 26 + sw, y: 0, w: 34, h: 14}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={14} />
			{/* body: yellow hoodie */}
			<R
				s={{kind: 'polygon', pts: [[-48, -230], [48, -230], [62, -105], [-62, -105]]}}
				o={{fill: C.yellow, fillStyle: 'hachure', hachureAngle: -41}}
				draw={draw}
				seed={15}
			/>
			{/* arms */}
			{holdGuitar ? (
				<>
					<R s={{kind: 'line', x1: -46, y1: -215, x2: -10, y2: -150}} o={{strokeWidth: 6}} draw={draw} seed={16} />
					<R s={{kind: 'line', x1: 46, y1: -215, x2: 30, y2: -160}} o={{strokeWidth: 6}} draw={draw} seed={17} />
				</>
			) : wave ? (
				<>
					<R s={{kind: 'line', x1: -46, y1: -215, x2: -70, y2: -130}} o={{strokeWidth: 6}} draw={draw} seed={16} />
					<R s={{kind: 'line', x1: 46, y1: -215, x2: 95 + waveA, y2: -300}} o={{strokeWidth: 6}} draw={draw} seed={18} />
				</>
			) : shocked ? (
				<>
					<R s={{kind: 'line', x1: -46, y1: -215, x2: -90, y2: -290}} o={{strokeWidth: 6}} draw={draw} seed={16} />
					<R s={{kind: 'line', x1: 46, y1: -215, x2: 90, y2: -290}} o={{strokeWidth: 6}} draw={draw} seed={17} />
				</>
			) : mood === 'thinking' ? (
				<>
					<R s={{kind: 'line', x1: -46, y1: -215, x2: -70, y2: -130}} o={{strokeWidth: 6}} draw={draw} seed={16} />
					<R s={{kind: 'curve', pts: [[46, -215], [70, -180], [30, -255]]}} o={{strokeWidth: 6}} draw={draw} seed={17} />
				</>
			) : (
				<>
					<R s={{kind: 'line', x1: -46, y1: -215, x2: -70 + sw * 0.6, y2: -130}} o={{strokeWidth: 6}} draw={draw} seed={16} />
					<R s={{kind: 'line', x1: 46, y1: -215, x2: 70 - sw * 0.6, y2: -130}} o={{strokeWidth: 6}} draw={draw} seed={17} />
				</>
			)}
			{/* head */}
			<g transform="translate(0 -300)">
				{/* back hair (shoulder-length bob) */}
				<R s={{kind: 'path', d: 'M -78 -10 C -80 -90 80 -90 78 -10 L 80 60 C 50 70 -50 70 -80 60 Z'}} o={{fill: C.brown, fillStyle: 'solid'}} draw={draw} seed={18} />
				<R s={{kind: 'circle', x: 0, y: 0, d: 130}} o={{fill: C.skin, fillStyle: 'solid'}} draw={draw} seed={19} />
				{/* fringe */}
				<R
					s={{kind: 'path', d: 'M -66 -4 C -66 -78 66 -82 68 -6 C 44 -34 6 -40 -24 -30 C -40 -24 -56 -14 -66 -4 Z'}}
					o={{fill: C.brown, fillStyle: 'solid'}}
					draw={draw}
					seed={20}
				/>
				{/* eyes */}
				<g transform={`translate(${-22 + ex} 4) scale(1 ${shocked ? 1.4 : blink})`}>
					<R s={{kind: 'ellipse', x: 0, y: 0, w: shocked ? 20 : 12, h: shocked ? 20 : 16}} o={{fill: C.ink, fillStyle: 'solid', roughness: 0.6}} draw={draw} seed={21} />
				</g>
				<g transform={`translate(${22 + ex} 4) scale(1 ${shocked ? 1.4 : blink})`}>
					<R s={{kind: 'ellipse', x: 0, y: 0, w: shocked ? 20 : 12, h: shocked ? 20 : 16}} o={{fill: C.ink, fillStyle: 'solid', roughness: 0.6}} draw={draw} seed={22} />
				</g>
				{/* brows */}
				{mood === 'worried' && (
					<>
						<R s={{kind: 'line', x1: -34, y1: -14, x2: -12, y2: -22}} o={{strokeWidth: 3}} draw={draw} seed={23} />
						<R s={{kind: 'line', x1: 34, y1: -14, x2: 12, y2: -22}} o={{strokeWidth: 3}} draw={draw} seed={24} />
					</>
				)}
				{/* mouth */}
				{shocked ? (
					<R s={{kind: 'ellipse', x: 0, y: 36, w: 24, h: 30}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={25} />
				) : mood === 'worried' ? (
					<R s={{kind: 'arc', x: 0, y: 44, w: 36, h: 20, start: Math.PI * 1.1, stop: Math.PI * 1.9}} o={{strokeWidth: 3}} draw={draw} seed={25} />
				) : mood === 'thinking' ? (
					<R s={{kind: 'line', x1: -8, y1: 34, x2: 14, y2: 30}} o={{strokeWidth: 3}} draw={draw} seed={25} />
				) : (
					<R s={{kind: 'arc', x: 0, y: 26, w: mood === 'happy' || mood === 'confident' ? 44 : 30, h: 26, start: Math.PI * 0.15, stop: Math.PI * 0.85}} o={{strokeWidth: 3}} draw={draw} seed={25} />
				)}
				{/* cheeks */}
				<R s={{kind: 'circle', x: -38, y: 26, d: 14}} o={{fill: '#F29E8E', fillStyle: 'solid', stroke: 'none'}} draw={draw} seed={26} boil={false} />
				<R s={{kind: 'circle', x: 38, y: 26, d: 14}} o={{fill: '#F29E8E', fillStyle: 'solid', stroke: 'none'}} draw={draw} seed={27} boil={false} />
			</g>
			{holdGuitar && (
				<g transform="translate(10 -150) rotate(-35)">
					<Guitar draw={draw} />
				</g>
			)}
		</g>
	);
};

/**
 * The pawnbroker: big, round, bald, moustache, green vest. Origin at the bottom centre
 * of his torso (he usually stands behind a counter).
 */
export const Broker: React.FC<{
	mood?: 'smile' | 'grin' | 'smirk' | 'neutral';
	draw?: number;
	look?: number;
	arm?: number; // 0 = down, 1 = reaching forward
}> = ({mood = 'smile', draw = 1, look = 0, arm = 0}) => {
	const frame = useCurrentFrame();
	const blink = blinkScale(frame, 47);
	const bob = Math.sin(frame / 22) * 1.5;
	const ex = look * 7;
	const reachX = -70 - arm * 120;
	const reachY = -140 + arm * 30;
	return (
		<g transform={`translate(0 ${bob})`}>
			{/* torso */}
			<R s={{kind: 'ellipse', x: 0, y: -110, w: 250, h: 240}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={41} />
			<R
				s={{kind: 'polygon', pts: [[-110, -170], [-30, -200], [-20, 0], [-115, -20]]}}
				o={{fill: C.green, fillStyle: 'hachure', hachureAngle: 60}}
				draw={draw}
				seed={42}
			/>
			<R
				s={{kind: 'polygon', pts: [[110, -170], [30, -200], [20, 0], [115, -20]]}}
				o={{fill: C.green, fillStyle: 'hachure', hachureAngle: 60}}
				draw={draw}
				seed={43}
			/>
			{/* arm */}
			<R s={{kind: 'line', x1: -100, y1: -170, x2: reachX, y2: reachY}} o={{strokeWidth: 9}} draw={draw} seed={44} />
			<R s={{kind: 'circle', x: reachX, y: reachY, d: 34}} o={{fill: C.skin, fillStyle: 'solid'}} draw={draw} seed={45} />
			{/* head */}
			<g transform="translate(0 -275)">
				<R s={{kind: 'circle', x: 0, y: 0, d: 150}} o={{fill: C.skin, fillStyle: 'solid'}} draw={draw} seed={46} />
				<R s={{kind: 'arc', x: 0, y: -40, w: 70, h: 30, start: Math.PI * 1.15, stop: Math.PI * 1.85}} o={{strokeWidth: 2.5, stroke: '#D9A884'}} draw={draw} seed={47} />
				<g transform={`translate(${-26 + ex} -6) scale(1 ${blink})`}>
					<R s={{kind: 'ellipse', x: 0, y: 0, w: 12, h: 14}} o={{fill: C.ink, fillStyle: 'solid', roughness: 0.6}} draw={draw} seed={48} />
				</g>
				<g transform={`translate(${26 + ex} -6) scale(1 ${blink})`}>
					<R s={{kind: 'ellipse', x: 0, y: 0, w: 12, h: 14}} o={{fill: C.ink, fillStyle: 'solid', roughness: 0.6}} draw={draw} seed={49} />
				</g>
				{mood === 'smirk' && <R s={{kind: 'line', x1: 10, y1: -26, x2: 40, y2: -32}} o={{strokeWidth: 3.5}} draw={draw} seed={50} />}
				{/* moustache */}
				<R
					s={{kind: 'path', d: 'M -44 26 C -30 8 -8 12 0 20 C 8 12 30 8 44 26 C 30 22 12 30 0 26 C -12 30 -30 22 -44 26 Z'}}
					o={{fill: C.ink, fillStyle: 'solid'}}
					draw={draw}
					seed={51}
				/>
				{mood === 'grin' ? (
					<R s={{kind: 'arc', x: 0, y: 36, w: 70, h: 44, start: 0, stop: Math.PI, closed: true}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={52} />
				) : mood === 'smirk' ? (
					<R s={{kind: 'curve', pts: [[-18, 44], [8, 46], [28, 34]]}} o={{strokeWidth: 3.5}} draw={draw} seed={52} />
				) : mood === 'smile' ? (
					<R s={{kind: 'arc', x: 0, y: 36, w: 46, h: 22, start: Math.PI * 0.15, stop: Math.PI * 0.85}} o={{strokeWidth: 3.5}} draw={draw} seed={52} />
				) : (
					<R s={{kind: 'line', x1: -14, y1: 44, x2: 14, y2: 44}} o={{strokeWidth: 3.5}} draw={draw} seed={52} />
				)}
			</g>
		</g>
	);
};

/** Electric guitar, origin at body centre, ~260px long. */
export const Guitar: React.FC<{draw?: number}> = ({draw = 1}) => (
	<g>
		<R s={{kind: 'rect', x: -8, y: -190, w: 16, h: 150}} o={{fill: C.brown, fillStyle: 'solid'}} draw={draw} seed={61} />
		<R s={{kind: 'rect', x: -14, y: -215, w: 28, h: 30}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={62} />
		<R
			s={{kind: 'path', d: 'M 0 -50 C 40 -60 55 -20 40 0 C 70 20 60 70 0 70 C -60 70 -70 20 -40 0 C -55 -20 -40 -60 0 -50 Z'}}
			o={{fill: C.red, fillStyle: 'hachure', hachureAngle: 30}}
			draw={draw}
			seed={63}
		/>
		<R s={{kind: 'circle', x: 0, y: 10, d: 26}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={64} />
		<R s={{kind: 'rect', x: -20, y: 36, w: 40, h: 10}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={65} />
	</g>
);
