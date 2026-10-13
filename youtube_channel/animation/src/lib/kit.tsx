import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import {Penny} from './characters';
import {Card, Gear, Paper, Tick} from './props';
import {C, G, R, T, useP} from './rough';
import {SfxCue, Soundtrack} from './sound';

/**
 * Shared episode kit (from Ep 5 on): scene shell, cue helper, and the standard
 * beats every episode has (title card, three-engine intro, machine + rules, end screen).
 */

export const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
	<svg viewBox="0 0 1920 1080" width="100%" height="100%">
		<Paper />
		{children}
	</svg>
);

/** Cue helper: all times are GLOBAL seconds copied from the timing file. */
export const useCue = (sceneStart: number) => {
	const h = useP();
	return {
		...h,
		t: h.t + sceneStart,
		p: (g: number, d?: number) => h.p(g - sceneStart, d),
		pop: (g: number, d?: number) => h.pop(g - sceneStart, d),
		after: (g: number) => h.t + sceneStart >= g,
	};
};

export const money = (n: number) => '$' + n.toLocaleString('en-US');

export const Header: React.FC<{text: string; at: number; S: number}> = ({text, at, S}) => {
	const {pop} = useCue(S);
	return (
		<T x={960} y={100} size={74} font="marker" scale={pop(at)}>
			{text}
		</T>
	);
};

/** Card with a small label and a big number. */
export const Stat: React.FC<{label: string; value: string; w?: number; color?: string; fill?: string; size?: number; seed?: number}> = ({
	label,
	value,
	w = 760,
	color = C.red,
	fill = C.yellow,
	size = 84,
	seed = 1,
}) => (
	<Card w={w} h={200} seed={seed} fill={fill}>
		<T x={0} y={-50} size={38}>
			{label}
		</T>
		<T x={0} y={35} size={size} font="marker" color={color}>
			{value}
		</T>
	</Card>
);

/** Simple label card. */
export const Label: React.FC<{text: string; w?: number; size?: number; fill?: string; color?: string; seed?: number}> = ({
	text,
	w = 600,
	size = 52,
	fill = C.white,
	color = C.ink,
	seed = 2,
}) => (
	<Card w={w} h={size * 2.3} seed={seed} fill={fill}>
		<T x={0} y={6} size={size} font="marker" color={color}>
			{text}
		</T>
	</Card>
);

/** Pie chart showing `pct` (0..1) of the circle filled. */
export const Pie: React.FC<{pct: number; r?: number; color?: string}> = ({pct, r = 150, color = C.red}) => {
	const a = -Math.PI / 2 + Math.min(0.9999, pct) * Math.PI * 2;
	const large = pct > 0.5 ? 1 : 0;
	return (
		<g>
			<R s={{kind: 'circle', x: 0, y: 0, d: r * 2}} o={{fill: C.white, fillStyle: 'solid'}} seed={700} />
			{pct > 0.001 && <path d={`M 0 0 L 0 ${-r} A ${r} ${r} 0 ${large} 1 ${Math.cos(a) * r} ${Math.sin(a) * r} Z`} fill={color} stroke={C.ink} strokeWidth={3} />}
		</g>
	);
};

/** Progress bar from 0..1. */
export const Bar: React.FC<{w: number; h?: number; v: number; color?: string}> = ({w, h = 60, v, color = C.red}) => (
	<g>
		<R s={{kind: 'rect', x: 0, y: 0, w, h}} o={{fill: C.white, fillStyle: 'solid'}} seed={710} boil={false} />
		{v > 0.005 && <rect x={3} y={3} width={(w - 6) * Math.min(1, v)} height={h - 6} fill={color} />}
	</g>
);

/** The standard title: MONEY MECHANICS between two gears, with a subtitle. */
export const TitleCard: React.FC<{S: number; at: number; subtitle: string}> = ({S, at, subtitle}) => {
	const {pop, t} = useCue(S);
	const rot = t * 80;
	return (
		<>
			<G x={960} y={470} s={pop(at, 0.6)}>
				<G x={-420} y={0}>
					<Gear r={110} rot={rot} fill={C.yellow} seed={4} />
				</G>
				<G x={420} y={0}>
					<Gear r={110} rot={-rot} fill={C.yellow} seed={5} />
				</G>
				<T x={0} y={-40} size={130} font="marker">
					MONEY
				</T>
				<T x={0} y={90} size={130} font="marker" color={C.yellow} stroke={C.ink}>
					MECHANICS
				</T>
			</G>
			<T x={960} y={820} size={54} scale={pop(at + 0.9)}>
				{subtitle}
			</T>
		</>
	);
};

/** Three engine labels popping in one by one under a hero element. */
export const EngineLabels: React.FC<{S: number; at: number; labels: [string, string, string]; y?: number}> = ({S, at, labels, y = 760}) => {
	const {pop} = useCue(S);
	return (
		<>
			{labels.map((l, i) => (
				<G key={l} x={460 + i * 500} y={y} s={pop(at + i * 0.7)}>
					<Card w={420} h={120} seed={2 + i} fill={i === 1 ? C.red : C.white}>
						<T x={0} y={6} size={l.length > 9 ? 46 : 58} font="marker" color={i === 1 ? C.white : C.ink}>
							{l}
						</T>
					</Card>
				</G>
			))}
		</>
	);
};

/** The "so here's the machine" beat: three gears light up, then a punchline, then three rules. */
export const MachineAndRules: React.FC<{
	S: number;
	labels: [string, string, string];
	gearAt: [number, number, number];
	punch?: {text: string; at: number}[];
	rulesAt: number;
	banner: string;
	rules: {text: string; at: number}[];
}> = ({S, labels, gearAt, punch = [], rulesAt, banner, rules}) => {
	const {p, pop, after, t} = useCue(S);
	const rot = t * 50;
	if (t < rulesAt) {
		return (
			<Svg>
				<T x={960} y={100} size={74} font="marker" scale={pop(S + 0.1)}>
					THE MACHINE
				</T>
				{labels.map((l, i) => (
					<G key={l} x={460 + i * 500} y={430} s={pop(S + 0.2 + i * 0.3)}>
						<Gear r={150} rot={after(gearAt[i]) ? (i % 2 ? -rot : rot) : 0} fill={after(gearAt[i]) ? C.yellow : C.white} seed={30 + i} />
						<T x={0} y={230} size={l.length > 9 ? 46 : 58} font="marker">
							{l}
						</T>
					</G>
				))}
				{punch.map((pp, i) =>
					after(pp.at) ? (
						<T key={pp.text} x={960} y={870 + i * 100} size={i === punch.length - 1 ? 68 : 56} font="marker" color={i === punch.length - 1 ? C.red : C.ink} scale={pop(pp.at)}>
							{pp.text}
						</T>
					) : null,
				)}
			</Svg>
		);
	}
	return (
		<Svg>
			<G x={260} y={1000} s={0.85}>
				<Penny mood="confident" />
			</G>
			<G x={1100} y={190} s={pop(rulesAt)}>
				<Card w={1000} h={120} seed={23} fill={C.yellow}>
					<T x={0} y={6} size={50} font="marker">
						{banner}
					</T>
				</Card>
			</G>
			{rules.map((r, i) =>
				after(r.at - 0.9) ? (
					<G key={r.text} x={1100} y={420 + i * 190} s={pop(r.at - 0.9)}>
						<Card w={1000} h={150} seed={24 + i}>
							<T x={-440} y={4} size={64} font="marker" color={C.blue}>
								{i + 1}
							</T>
							<T x={30} y={4} size={r.text.length > 34 ? 38 : 44}>
								{r.text}
							</T>
							<G x={450} y={0}>
								<Tick draw={p(r.at + 1.5, 0.4)} seed={4 + i} />
							</G>
						</Card>
					</G>
				) : null,
			)}
		</Svg>
	);
};

export const EndScreen: React.FC<{S: number}> = ({S}) => {
	const {pop} = useCue(S);
	return (
		<Svg>
			<T x={960} y={110} size={84} font="marker" scale={pop(S)}>
				MONEY{' '}
				<tspan fill={C.yellow} stroke={C.ink} strokeWidth={8} paintOrder="stroke">
					MECHANICS
				</tspan>
			</T>
			<R s={{kind: 'rect', x: 1010, y: 260, w: 760, h: 428}} o={{strokeLineDash: [18, 12], stroke: C.shadow, strokeWidth: 4}} seed={95} boil={false} />
			<T x={1390} y={474} size={44} color={C.shadow}>
				(watch next)
			</T>
			<R s={{kind: 'circle', x: 520, y: 520, d: 300}} o={{strokeLineDash: [18, 12], stroke: C.shadow, strokeWidth: 4}} seed={96} boil={false} />
			<T x={520} y={720} size={44} color={C.shadow}>
				(subscribe)
			</T>
			<G x={250} y={1000} s={0.75}>
				<Penny wave mood="happy" />
			</G>
		</Svg>
	);
};

/** Assemble an episode from scene boundaries; the last scene runs to `total`. */
export const Episode: React.FC<{vo: string; music: string; voEnd: number; total: number; sfx: SfxCue[]; dips?: number[]; scenes: [number, React.FC][]}> = ({
	vo,
	music,
	voEnd,
	total,
	sfx,
	dips = [],
	scenes,
}) => {
	const {fps} = useVideoConfig();
	return (
		<AbsoluteFill style={{background: C.paper}}>
			<Audio src={staticFile(vo)} />
			<Soundtrack music={music} sfx={[...sfx, [voEnd + 0.2, 'sting', 0.5]]} voEnd={voEnd} dips={dips} />
			{scenes.map(([a, Comp], i) => {
				const b = i + 1 < scenes.length ? scenes[i + 1][0] : total;
				return (
					<Sequence key={i} from={Math.round(a * fps)} durationInFrames={Math.round((b - a) * fps)}>
						<Comp />
					</Sequence>
				);
			})}
		</AbsoluteFill>
	);
};
