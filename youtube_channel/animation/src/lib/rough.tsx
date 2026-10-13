import React, {useMemo} from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import rough from 'roughjs';
import type {Options} from 'roughjs/bin/core';
import {continueRender, delayRender, staticFile} from 'remotion';

// Fonts are bundled locally (both SIL Open Font License) so renders work offline.
export const HAND = 'Patrick Hand';
export const MARKER = 'Permanent Marker';
if (typeof window !== 'undefined' && typeof FontFace !== 'undefined') {
	const handle = delayRender('fonts');
	Promise.all(
		[
			[HAND, 'fonts/PatrickHand.woff2'],
			[MARKER, 'fonts/PermanentMarker.woff2'],
		].map(([family, file]) =>
			new FontFace(family, `url(${staticFile(file)})`).load().then((f) => document.fonts.add(f)),
		),
	).then(() => continueRender(handle));
}

// Money Mechanics palette
export const C = {
	yellow: '#FFC83D',
	ink: '#1E1E24',
	green: '#2EAD6B',
	red: '#E5484D',
	paper: '#F6F1E7',
	shadow: '#C9C2B5',
	skin: '#F2C7A5',
	blue: '#4C7BD9',
	brown: '#9A6B3F',
	gold: '#E8B62C',
	white: '#FFFFFF',
};

const gen = rough.generator();

export type Shape =
	| {kind: 'rect'; x: number; y: number; w: number; h: number}
	| {kind: 'circle'; x: number; y: number; d: number}
	| {kind: 'ellipse'; x: number; y: number; w: number; h: number}
	| {kind: 'line'; x1: number; y1: number; x2: number; y2: number}
	| {kind: 'polygon'; pts: [number, number][]}
	| {kind: 'curve'; pts: [number, number][]}
	| {kind: 'path'; d: string}
	| {kind: 'arc'; x: number; y: number; w: number; h: number; start: number; stop: number; closed?: boolean};

const build = (s: Shape, o: Options) => {
	switch (s.kind) {
		case 'rect':
			return gen.rectangle(s.x, s.y, s.w, s.h, o);
		case 'circle':
			return gen.circle(s.x, s.y, s.d, o);
		case 'ellipse':
			return gen.ellipse(s.x, s.y, s.w, s.h, o);
		case 'line':
			return gen.line(s.x1, s.y1, s.x2, s.y2, o);
		case 'polygon':
			return gen.polygon(s.pts, o);
		case 'curve':
			return gen.curve(s.pts, o);
		case 'path':
			return gen.path(s.d, o);
		case 'arc':
			return gen.arc(s.x, s.y, s.w, s.h, s.start, s.stop, s.closed ?? false, o);
	}
};

// Classic hand-drawn "line boil": the drawing is re-sketched a few times a second.
const BOIL_EVERY = 5;

/**
 * A single hand-drawn shape. `draw` (0..1) animates the strokes being drawn on;
 * fills fade in during the last part of the draw.
 */
export const R: React.FC<{
	s: Shape;
	o?: Options;
	draw?: number;
	seed?: number;
	boil?: boolean;
}> = ({s, o = {}, draw = 1, seed = 1, boil = true}) => {
	const frame = useCurrentFrame();
	const variant = boil ? Math.floor(frame / BOIL_EVERY) % 3 : 0;
	const key = JSON.stringify(s) + JSON.stringify(o) + seed + variant;
	const paths = useMemo(
		() =>
			gen.toPaths(
				build(s, {
					roughness: 1.3,
					bowing: 1,
					stroke: C.ink,
					strokeWidth: 3.5,
					fillWeight: 2.2,
					hachureGap: 9,
					...o,
					seed: seed * 7 + variant + 1,
				}),
			),
		// eslint-disable-next-line react-hooks/exhaustive-deps
		[key],
	);
	if (draw <= 0) return null;
	const fillOpacity = interpolate(draw, [0.6, 1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<g>
			{paths.map((p, i) => {
				const isFill = p.stroke === 'none' || (!!o.fill && p.stroke === o.fill);
				if (isFill) {
					return <path key={i} d={p.d} fill={p.fill ?? 'none'} stroke={p.stroke} strokeWidth={p.strokeWidth} opacity={fillOpacity} />;
				}
				return (
					<path
						key={i}
						d={p.d}
						fill={p.fill ?? 'none'}
						stroke={p.stroke}
						strokeWidth={p.strokeWidth}
						strokeLinecap="round"
						strokeLinejoin="round"
						pathLength={1}
						strokeDasharray={1}
						strokeDashoffset={1 - Math.min(1, draw)}
						opacity={p.fill && p.fill !== 'none' ? fillOpacity : 1}
					/>
				);
			})}
		</g>
	);
};

/** Progress helper: 0..1 between `start` and `start+dur` seconds of the local timeline. */
export const useP = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const p = (start: number, dur = 0.6, ease = Easing.out(Easing.cubic)) =>
		interpolate(t, [start, start + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
	const pop = (start: number, dur = 0.45) =>
		interpolate(t, [start, start + dur], [0, 1], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
			easing: Easing.out(Easing.back(2.2)),
		});
	return {t, frame, fps, p, pop};
};

/** Hand-lettered text with a subtle wobble. */
export const T: React.FC<{
	x: number;
	y: number;
	size?: number;
	color?: string;
	font?: 'hand' | 'marker';
	anchor?: 'start' | 'middle' | 'end';
	children: React.ReactNode;
	scale?: number;
	rotate?: number;
	stroke?: string;
}> = ({x, y, size = 48, color = C.ink, font = 'hand', anchor = 'middle', children, scale = 1, rotate = 0, stroke}) => {
	const frame = useCurrentFrame();
	const wob = Math.sin(Math.floor(frame / BOIL_EVERY) * 2.1 + x) * 0.6;
	if (scale <= 0) return null;
	return (
		<g transform={`translate(${x} ${y}) rotate(${rotate + wob}) scale(${scale})`}>
			<text
				textAnchor={anchor}
				dominantBaseline="middle"
				fontFamily={font === 'hand' ? HAND : MARKER}
				fontSize={size}
				fill={color}
				stroke={stroke}
				strokeWidth={stroke ? size / 9 : 0}
				paintOrder="stroke"
				strokeLinejoin="round"
			>
				{children}
			</text>
		</g>
	);
};

/** Group helper with translate/scale/rotate/opacity. */
export const G: React.FC<{
	x?: number;
	y?: number;
	s?: number;
	r?: number;
	o?: number;
	children: React.ReactNode;
}> = ({x = 0, y = 0, s = 1, r = 0, o = 1, children}) =>
	s <= 0 || o <= 0 ? null : (
		<g transform={`translate(${x} ${y}) rotate(${r}) scale(${s})`} opacity={o}>
			{children}
		</g>
	);

/** Counting number that ticks up. */
export const countUp = (p: number, to: number) => Math.round(to * p);
