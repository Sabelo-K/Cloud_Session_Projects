import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, getStaticFiles, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SfxCue, Soundtrack} from '../lib/sound';
import TMAP from './timemap.json';

/** Map a v1-voiceover time to the current voiceover (piecewise linear over matched sentences). */
const m = (t: number): number => {
	const P = TMAP as number[][];
	if (t <= P[0][0]) return t;
	for (let i = 1; i < P.length; i++) {
		if (t <= P[i][0]) {
			const [a0, b0] = P[i - 1];
			const [a1, b1] = P[i];
			return a1 === a0 ? b1 : b0 + ((t - a0) / (a1 - a0)) * (b1 - b0);
		}
	}
	return t - P[P.length - 1][0] + P[P.length - 1][1];
};

/**
 * Episode 9, POV Finance look: full-bleed illustrated plates (public/ep09/plates/NN.png|jpg)
 * with slow Ken Burns moves, crossfades, and clean white number / chat overlays.
 * Same VO and timings as Ep09 (timing_ep09.json); all times are global seconds.
 */
export const VO9P_SECONDS = m(301.0);
export const EP09P_SECONDS = VO9P_SECONDS + 12;
const FADE = 0.4;
const SANS = 'Arial, Helvetica, sans-serif';
const RED = '#E5484D';
const GREEN = '#3DDC84';
const YELLOW = '#FFC83D';

const SHOTS_V1: number[] = [
	0, 3.22, 7.45, 11.95, 15.64, 23.13, 27.93, 32.15, 36.0, 48.59, 56.62, 63.59, 74.13, 78.74, 87.24, 93.26, 103.75, 109.38, 116.02, 127.06, 138.88,
	142.16, 149.05, 150.29, 159.4, 164.17, 175.96, 188.58, 200.7, 206.67, 216.59, 219.67, 237.84, 259.78, 283.81,
];

/** Find plate NN as png, jpg, jpeg or webp, whichever exists. */
const SHOTS = SHOTS_V1.map(m);

const plateFor = (n: number) => {
	const id = String(n).padStart(2, '0');
	const files = getStaticFiles().map((f) => f.name);
	for (const ext of ['png', 'jpg', 'jpeg', 'webp']) {
		const name = `ep09/plates/${id}.${ext}`;
		if (files.includes(name)) return staticFile(name);
	}
	return staticFile(`ep09/plates/${id}.png`);
};

const Plate: React.FC<{n: number; dur: number; dim?: number}> = ({n, dur, dim = 0}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const k = Math.min(1, t / dur);
	const zoomIn = n % 2 === 1;
	const scale = zoomIn ? 1.04 + 0.1 * k : 1.14 - 0.1 * k;
	const dir = n % 4 < 2 ? 1 : -1;
	const tx = dir * (k - 0.5) * 40;
	const ty = (n % 3 === 0 ? -1 : 1) * (k - 0.5) * 16;
	const opacity = n === 1 ? 1 : interpolate(t, [0, FADE], [0, 1], {extrapolateRight: 'clamp'});
	return (
		<AbsoluteFill style={{opacity}}>
			<Img src={plateFor(n)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `translate(${tx}px, ${ty}px) scale(${scale})`}} />
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)'}} />
			{dim > 0 && <AbsoluteFill style={{background: `rgba(10,12,20,${dim})`}} />}
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- overlay vocabulary
type Pos = {x: number; y: number}; // 0..1 of frame
type Ov =
	| {k: 'num'; at: number; to: number; text: string; pos: Pos; color?: string; size?: number; count?: [number, number, string?]}
	| {k: 'chapter'; at: number; to: number; tag: string; title: string}
	| {k: 'title'; at: number; to: number; text: string; sub?: string; color?: string}
	| {k: 'bubble'; at: number; to: number; text: string; pos: Pos; me?: boolean; warn?: boolean}
	| {k: 'label'; at: number; to: number; text: string; color?: string}
	| {k: 'stat'; at: number; to: number; value: string; sub: string; pos: Pos; color?: string; count?: [number, number, string?]}
	| {k: 'quote'; at: number; to: number; text: string}
	| {k: 'list'; at: number; to: number; items: {at: number; text: string}[]; pos: Pos}
	| {k: 'you'; at: number; to: number; pos: Pos};

const shadow = '0 4px 18px rgba(0,0,0,0.75), 0 2px 3px rgba(0,0,0,0.9)';

const useAppear = (at: number, to: number) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const o = interpolate(t, [at, at + 0.25, to - 0.25, to], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const s = interpolate(t, [at, at + 0.25], [0.85, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return {t, o, s, on: t >= at && t <= to};
};

const counted = (t: number, at: number, c?: [number, number, string?]) => {
	if (!c) return null;
	const k = interpolate(t, [at, at + 1.6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const eased = 1 - Math.pow(1 - k, 3);
	const v = c[0] + (c[1] - c[0]) * eased;
	const suffix = c[2] ?? '';
	return '$' + (Math.abs(c[1]) < 20 ? v.toFixed(1) : Math.round(v).toLocaleString('en-US')) + suffix;
};

const Abs: React.FC<{pos: Pos; o: number; s: number; children: React.ReactNode; align?: 'center' | 'left'}> = ({pos, o, s, children, align = 'center'}) => (
	<div
		style={{
			position: 'absolute',
			left: `${pos.x * 100}%`,
			top: `${pos.y * 100}%`,
			transform: `translate(${align === 'center' ? '-50%' : '0'}, -50%) scale(${s})`,
			opacity: o,
			textAlign: align,
		}}
	>
		{children}
	</div>
);

const Overlay: React.FC<{ov: Ov}> = ({ov}) => {
	const {t, o, s, on} = useAppear(ov.at, ov.to);
	if (!on) return null;
	switch (ov.k) {
		case 'num':
			return (
				<Abs pos={ov.pos} o={o} s={s}>
					<div style={{fontFamily: SANS, fontWeight: 900, fontSize: ov.size ?? 92, color: ov.color ?? 'white', textShadow: shadow, whiteSpace: 'nowrap', letterSpacing: -1}}>
						{counted(t, ov.at, ov.count) ?? ov.text}
					</div>
				</Abs>
			);
		case 'chapter':
			return (
				<Abs pos={{x: 0.045, y: 0.13}} o={o} s={s} align="left">
					<div style={{display: 'inline-block', background: RED, color: 'white', fontFamily: SANS, fontWeight: 900, fontSize: 54, padding: '6px 22px', borderRadius: 6, boxShadow: '0 6px 20px rgba(0,0,0,0.5)'}}>
						{ov.tag}
					</div>
					<div style={{fontFamily: SANS, fontWeight: 800, fontSize: 56, color: 'white', textShadow: shadow, marginTop: 12, whiteSpace: 'nowrap'}}>{ov.title}</div>
				</Abs>
			);
		case 'title':
			return (
				<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: o}}>
					<div style={{transform: `scale(${s})`, textAlign: 'center'}}>
						<div style={{fontFamily: SANS, fontWeight: 900, fontSize: 110, color: ov.color ?? 'white', textShadow: shadow, letterSpacing: -2}}>{ov.text}</div>
						{ov.sub && <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 52, color: 'white', textShadow: shadow, marginTop: 18}}>{ov.sub}</div>}
					</div>
				</AbsoluteFill>
			);
		case 'bubble':
			return (
				<Abs pos={ov.pos} o={o} s={s}>
					<div
						style={{
							maxWidth: 760,
							background: ov.warn ? '#FFE3E3' : ov.me ? '#DCF8C6' : 'white',
							border: ov.warn ? `4px solid ${RED}` : 'none',
							color: '#111',
							fontFamily: SANS,
							fontSize: 48,
							fontWeight: 600,
							padding: '22px 34px',
							borderRadius: 34,
							borderBottomLeftRadius: ov.me ? 34 : 6,
							borderBottomRightRadius: ov.me ? 6 : 34,
							boxShadow: '0 10px 30px rgba(0,0,0,0.45)',
						}}
					>
						{ov.text}
					</div>
				</Abs>
			);
		case 'label':
			return (
				<Abs pos={{x: 0.5, y: 0.86}} o={o} s={s}>
					<div style={{background: 'rgba(12,14,22,0.82)', color: ov.color ?? YELLOW, fontFamily: SANS, fontWeight: 900, fontSize: 56, padding: '14px 36px', borderRadius: 10, whiteSpace: 'nowrap'}}>
						{ov.text}
					</div>
				</Abs>
			);
		case 'stat':
			return (
				<Abs pos={ov.pos} o={o} s={s}>
					<div style={{fontFamily: SANS, fontWeight: 900, fontSize: 150, color: ov.color ?? YELLOW, textShadow: shadow, letterSpacing: -3, whiteSpace: 'nowrap'}}>
						{counted(t, ov.at, ov.count) ?? ov.value}
					</div>
					<div style={{fontFamily: SANS, fontWeight: 700, fontSize: 44, color: 'white', textShadow: shadow, whiteSpace: 'nowrap'}}>{ov.sub}</div>
				</Abs>
			);
		case 'quote':
			return (
				<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: o}}>
					<div style={{transform: `scale(${s})`, maxWidth: 1400, background: 'rgba(255,255,255,0.95)', padding: '40px 60px', borderRadius: 18, borderLeft: `16px solid ${RED}`, boxShadow: '0 20px 50px rgba(0,0,0,0.5)'}}>
						<div style={{fontFamily: SANS, fontWeight: 900, fontSize: 64, color: '#111', lineHeight: 1.2}}>{ov.text}</div>
					</div>
				</AbsoluteFill>
			);
		case 'list':
			return (
				<Abs pos={ov.pos} o={o} s={1} align="left">
					{ov.items.map((it, i) =>
						t >= it.at ? (
							<div
								key={it.text}
								style={{
									display: 'flex',
									alignItems: 'center',
									gap: 22,
									margin: '18px 0',
									background: 'rgba(12,14,22,0.82)',
									padding: '16px 30px',
									borderRadius: 12,
									opacity: interpolate(t, [it.at, it.at + 0.3], [0, 1], {extrapolateRight: 'clamp'}),
								}}
							>
								<div style={{fontFamily: SANS, fontWeight: 900, fontSize: 60, color: YELLOW}}>{i + 1}</div>
								<div style={{fontFamily: SANS, fontWeight: 700, fontSize: 48, color: 'white', whiteSpace: 'nowrap'}}>{it.text}</div>
							</div>
						) : null,
					)}
				</Abs>
			);
		case 'you':
			return (
				<Abs pos={ov.pos} o={o} s={s}>
					<svg width={300} height={220} viewBox="0 0 300 220" style={{overflow: 'visible'}}>
						<text x={20} y={80} fontFamily={SANS} fontWeight={900} fontSize={96} fill={RED} stroke="white" strokeWidth={6} paintOrder="stroke">
							YOU
						</text>
						<path d="M 150 100 Q 180 160 250 190" fill="none" stroke="white" strokeWidth={22} strokeLinecap="round" />
						<path d="M 150 100 Q 180 160 250 190" fill="none" stroke={RED} strokeWidth={12} strokeLinecap="round" />
						<polygon points="270,200 222,206 244,166" fill={RED} stroke="white" strokeWidth={4} />
					</svg>
				</Abs>
			);
	}
};

// ---------------------------------------------------------------- the overlay script
const OVS_V1: Ov[] = [
	{k: 'chapter', at: 0.3, to: 7.2, tag: 'DAY 90', title: 'Thursday, 11:48 PM'},
	{k: 'num', at: 7.6, to: 15.5, text: '', pos: {x: 0.5, y: 0.78}, color: GREEN, size: 120, count: [0, 184000]},
	{k: 'num', at: 15.7, to: 23.0, text: 'PAY 15% TAX TO WITHDRAW', pos: {x: 0.5, y: 0.7}, color: 'white', size: 70},
	{k: 'num', at: 20.05, to: 23.0, text: '$27,600', pos: {x: 0.5, y: 0.82}, color: RED, size: 130},
	{k: 'num', at: 23.2, to: 27.8, text: 'Already put in: everything', pos: {x: 0.5, y: 0.82}, size: 70},
	{k: 'you', at: 28.0, to: 32.0, pos: {x: 0.6, y: 0.2}},
	{k: 'title', at: 32.2, to: 35.9, text: '90 days earlier...'},
	{k: 'title', at: 36.05, to: 43.3, text: 'FRIDAY SPECIAL', color: YELLOW},
	{k: 'num', at: 39.3, to: 43.3, text: 'The story is made up.', pos: {x: 0.5, y: 0.66}, size: 60},
	{k: 'num', at: 41.4, to: 43.3, text: 'The playbook is real.', pos: {x: 0.5, y: 0.76}, size: 60, color: YELLOW},
	{k: 'title', at: 43.5, to: 48.5, text: 'PIG BUTCHERING', sub: 'a Money Mechanics POV', color: '#F4A7B9'},
	{k: 'num', at: 48.7, to: 52.9, text: '1. Fatten the pig', pos: {x: 0.5, y: 0.72}, size: 76},
	{k: 'num', at: 50.8, to: 52.9, text: '2. Take everything', pos: {x: 0.5, y: 0.84}, size: 76, color: RED},
	{k: 'title', at: 53.1, to: 56.5, text: 'How it works', sub: '...and how you saw it coming'},
	{k: 'chapter', at: 56.7, to: 62.8, tag: 'DAY 1', title: 'The wrong number'},
	{k: 'bubble', at: 63.6, to: 73.9, text: 'Hi Anna, are we still on for golf on Saturday?', pos: {x: 0.5, y: 0.5}},
	{k: 'bubble', at: 74.2, to: 78.6, text: 'Sorry, wrong number!', pos: {x: 0.62, y: 0.32}, me: true},
	{k: 'num', at: 76.95, to: 78.6, text: 'You: no reply', pos: {x: 0.3, y: 0.8}, size: 64, color: YELLOW},
	{k: 'chapter', at: 78.8, to: 86.9, tag: 'MECHANISM #1', title: 'It’s a filter'},
	{k: 'label', at: 83.0, to: 87.1, text: 'Anyone who replies = a lead'},
	{k: 'chapter', at: 87.3, to: 92.5, tag: 'DAY 12', title: 'The friend'},
	{k: 'num', at: 91.3, to: 93.1, text: 'Grace', pos: {x: 0.5, y: 0.8}, size: 90, color: '#F4A7B9'},
	{k: 'bubble', at: 93.3, to: 100.2, text: 'good morning :)', pos: {x: 0.32, y: 0.3}},
	{k: 'bubble', at: 96.6, to: 103.6, text: 'how’s your sister doing?', pos: {x: 0.66, y: 0.5}},
	{k: 'num', at: 100.4, to: 103.6, text: 'Asked for money: $0', pos: {x: 0.5, y: 0.82}, size: 72, color: GREEN},
	{k: 'bubble', at: 103.8, to: 109.2, text: 'my uncle taught me to trade crypto...', pos: {x: 0.5, y: 0.25}},
	{k: 'bubble', at: 109.4, to: 115.9, text: 'can we chat on another app?', pos: {x: 0.5, y: 0.3}, warn: true},
	{k: 'label', at: 114.2, to: 115.95, text: 'Fewer people watching'},
	{k: 'chapter', at: 116.1, to: 126.9, tag: 'MECHANISM #2', title: 'They sell a person'},
	{k: 'label', at: 122.6, to: 126.95, text: 'Trust first. Money later.'},
	{k: 'chapter', at: 127.1, to: 132.8, tag: 'DAY 30', title: 'The app'},
	{k: 'num', at: 136.4, to: 138.8, text: '$500 in', pos: {x: 0.5, y: 0.8}, size: 110},
	{k: 'num', at: 138.9, to: 142.1, text: '', pos: {x: 0.5, y: 0.8}, size: 120, color: GREEN, count: [500, 640]},
	{k: 'num', at: 142.2, to: 148.9, text: '+$100 to his real bank', pos: {x: 0.5, y: 0.82}, size: 80, color: GREEN},
	{k: 'num', at: 149.1, to: 150.2, text: 'You: not convinced', pos: {x: 0.5, y: 0.82}, size: 72, color: YELLOW},
	{k: 'chapter', at: 150.35, to: 159.3, tag: 'MECHANISM #3', title: 'The stage set'},
	{k: 'label', at: 155.6, to: 159.3, text: 'The numbers are typed in by the scammers'},
	{k: 'label', at: 159.45, to: 164.0, text: 'The $100 is the bait', color: RED},
	{k: 'chapter', at: 164.2, to: 175.8, tag: 'DAY 60', title: 'The fattening'},
	{k: 'list', at: 165.7, to: 175.8, pos: {x: 0.58, y: 0.42}, items: [{at: 165.7, text: 'Savings'}, {at: 168.0, text: 'Retirement account'}, {at: 170.2, text: 'Loan against his car'}]},
	{k: 'num', at: 172.75, to: 175.8, text: '', pos: {x: 0.5, y: 0.84}, size: 120, color: RED, count: [0, 120000, ' in']},
	{k: 'num', at: 179.8, to: 188.4, text: 'Marcus: “busy”', pos: {x: 0.72, y: 0.3}, size: 72},
	{k: 'label', at: 181.8, to: 188.4, text: 'Silence is part of the design'},
	{k: 'chapter', at: 188.6, to: 192.3, tag: 'DAY 90', title: 'Back to Thursday night'},
	{k: 'quote', at: 195.75, to: 200.6, text: 'A real exchange never makes you pay to get your own money out.'},
	{k: 'num', at: 202.25, to: 206.5, text: 'He doesn’t pay.', pos: {x: 0.5, y: 0.8}, size: 100, color: YELLOW},
	{k: 'bubble', at: 203.8, to: 206.5, text: 'Grace: (no reply)', pos: {x: 0.7, y: 0.28}},
	{k: 'num', at: 207.0, to: 210.1, text: 'site not found', pos: {x: 0.5, y: 0.5}, size: 90, color: 'white'},
	{k: 'stat', at: 210.25, to: 216.4, value: '$120,000', sub: 'gone', pos: {x: 0.3, y: 0.5}, color: RED},
	{k: 'stat', at: 213.35, to: 216.4, value: '$27,600', sub: 'saved', pos: {x: 0.72, y: 0.5}, color: GREEN},
	{k: 'label', at: 216.6, to: 219.5, text: 'Most people don’t have someone on the couch'},
	{k: 'stat', at: 219.7, to: 237.7, value: '', sub: 'lost to crypto investment fraud, US, 2024 (FBI)', pos: {x: 0.5, y: 0.36}, count: [0, 5.8, ' BILLION']},
	{k: 'stat', at: 230.7, to: 237.7, value: '$2.8 BILLION+', sub: 'crypto scam losses reported by people 60+ (FBI)', pos: {x: 0.5, y: 0.7}, color: 'white'},
	{k: 'title', at: 237.9, to: 241.1, text: 'And Grace?', color: '#F4A7B9'},
	{k: 'stat', at: 241.3, to: 259.6, value: '120,000+', sub: 'Myanmar: may be held and forced to run scams', pos: {x: 0.5, y: 0.3}},
	{k: 'stat', at: 248.0, to: 259.6, value: '~100,000', sub: 'Cambodia (UN Human Rights Office estimate, 2023)', pos: {x: 0.5, y: 0.6}},
	{k: 'label', at: 255.65, to: 259.6, text: 'Some are prisoners too', color: RED},
	{k: 'chapter', at: 259.85, to: 283.6, tag: 'HOW TO JAM THE MACHINE', title: ''},
	{
		k: 'list',
		at: 262.2,
		to: 283.6,
		pos: {x: 0.05, y: 0.6},
		items: [
			{at: 263.5, text: 'Small talk drifts to investing? Red flag.'},
			{at: 271.3, text: 'Pay to withdraw? The money was never there.'},
			{at: 276.8, text: 'Tell one person. Or be that person.'},
		],
	},
	{k: 'num', at: 283.9, to: 294.3, text: 'It doesn’t hack your phone.', pos: {x: 0.5, y: 0.14}, size: 72},
	{k: 'num', at: 286.85, to: 294.3, text: 'It hacks loneliness and hope.', pos: {x: 0.5, y: 0.25}, size: 72, color: YELLOW},
	{k: 'you', at: 292.8, to: 300.9, pos: {x: 0.76, y: 0.5}},
	{k: 'label', at: 294.5, to: 300.95, text: 'NEXT: How airlines really make money', color: 'white'},
];

const SFX_V1: SfxCue[] = [
	[0.1, 'clock', 0.35],
	[0.3, 'stamp', 0.4],
	[7.6, 'rise', 0.35],
	[9.2, 'chaching', 0.4],
	[11.95, 'plink', 0.4],
	[15.7, 'buzzer', 0.4],
	[20.1, 'sting_dark', 0.5],
	[28.0, 'pop', 0.35],
	[32.2, 'rewind', 0.45],
	[36.1, 'stamp', 0.5],
	[43.5, 'sting', 0.55],
	[50.8, 'sting_dark', 0.45],
	[56.7, 'stamp', 0.45],
	[63.6, 'ding', 0.45],
	[74.2, 'bloop', 0.45],
	[78.8, 'flip', 0.4],
	[83.0, 'beep', 0.4],
	[87.3, 'stamp', 0.45],
	[93.3, 'ding', 0.35],
	[96.6, 'ding', 0.35],
	[100.4, 'coin', 0.35],
	[103.8, 'ding', 0.35],
	[109.4, 'buzzer', 0.35],
	[116.1, 'flip', 0.4],
	[122.6, 'chaching', 0.4],
	[127.1, 'stamp', 0.45],
	[136.4, 'coin', 0.4],
	[139.0, 'rise', 0.35],
	[142.2, 'chaching', 0.45],
	[150.35, 'flip', 0.4],
	[159.45, 'sting_dark', 0.45],
	[164.2, 'stamp', 0.45],
	[165.7, 'coin', 0.4],
	[168.0, 'coin', 0.4],
	[170.2, 'coin', 0.4],
	[172.8, 'rise', 0.35],
	[181.8, 'sting_dark', 0.4],
	[188.6, 'rewind', 0.4],
	[195.75, 'sting', 0.5],
	[202.25, 'slap', 0.45],
	[207.0, 'sputter', 0.4],
	[210.25, 'sting_dark', 0.45],
	[213.35, 'chaching', 0.45],
	[219.7, 'rise', 0.35],
	[221.3, 'chaching', 0.4],
	[230.7, 'coin', 0.4],
	[241.3, 'stamp', 0.4],
	[248.0, 'stamp', 0.4],
	[255.65, 'sting_dark', 0.45],
	[263.5, 'tick', 0.45],
	[271.3, 'tick', 0.45],
	[276.8, 'tick', 0.45],
	[294.5, 'sting', 0.45],
];

const remap = (o: Ov): Ov => {
	const r = {...o, at: m(o.at), to: m(o.to)} as Ov;
	if (r.k === 'list') r.items = r.items.map((it) => ({...it, at: m(it.at)}));
	return r;
};
/** Overlays added for the v2 script, already in current-voiceover seconds. */
const OVS_V2: Ov[] = [
	{k: 'num', at: 73.38, to: 77.39, text: 'Not deleted.', pos: {x: 0.3, y: 0.92}, size: 64, color: YELLOW},
	{k: 'num', at: 87.43, to: 91.0, text: '6:15 AM. Every day.', pos: {x: 0.5, y: 0.82}, size: 72},
	{k: 'num', at: 160.76, to: 163.57, text: '3 weeks', pos: {x: 0.72, y: 0.3}, size: 90, color: YELLOW},
	{k: 'chapter', at: 176.89, to: 182.46, tag: 'DAY 1', title: 'The text you never deleted'},
	{k: 'bubble', at: 182.61, to: 189.3, text: 'Hi Anna, are we still on for golf on Saturday?', pos: {x: 0.5, y: 0.42}},
	{k: 'num', at: 185.39, to: 189.3, text: 'Same opener. Different name.', pos: {x: 0.5, y: 0.8}, size: 76, color: YELLOW},
];
const OVS: Ov[] = [...OVS_V1.map(remap), ...OVS_V2];
const SFX: SfxCue[] = [...SFX_V1.map(([a, f, v]) => [m(a), f, v] as SfxCue), [182.61, 'ding', 0.45], [185.39, 'sting', 0.45]];

const EndCard: React.FC = () => {
	const {o, s} = useAppear(VO9P_SECONDS, EP09P_SECONDS + 1);
	return (
		<AbsoluteFill style={{opacity: o}}>
			<div style={{position: 'absolute', top: 70, width: '100%', textAlign: 'center', transform: `scale(${s})`, fontFamily: SANS, fontWeight: 900, fontSize: 96, color: 'white', textShadow: shadow}}>
				MONEY <span style={{color: YELLOW}}>MECHANICS</span>
			</div>
			<div style={{position: 'absolute', left: 1010, top: 260, width: 760, height: 428, border: '5px dashed rgba(255,255,255,0.6)', borderRadius: 12}} />
			<div style={{position: 'absolute', left: 370, top: 370, width: 300, height: 300, border: '5px dashed rgba(255,255,255,0.6)', borderRadius: '50%'}} />
		</AbsoluteFill>
	);
};

export const Ep09Pov: React.FC = () => {
	const {fps} = useVideoConfig();
	return (
		<AbsoluteFill style={{background: '#0c0e16'}}>
			<Audio src={staticFile('ep09_vo.mp3')} />
			<Soundtrack music="music_lofi_ep09.mp3" sfx={[...SFX, [VO9P_SECONDS + 0.2, 'sting', 0.5]]} voEnd={VO9P_SECONDS} dips={[20.1, 210.25, 255.65].map(m)} />
			{SHOTS.map((start, i) => {
				const from = i === 0 ? 0 : start - FADE;
				const end = i + 1 < SHOTS.length ? SHOTS[i + 1] : EP09P_SECONDS;
				const dur = end - from;
				return (
					<Sequence key={i} from={Math.round(from * fps)} durationInFrames={Math.round(dur * fps)}>
						<Plate n={i + 1} dur={dur} dim={[30, 32, 33].includes(i + 1) ? 0.45 : 0} />
					</Sequence>
				);
			})}
			<Sequence from={Math.round(VO9P_SECONDS * fps)}>
				<AbsoluteFill style={{background: 'rgba(10,12,20,0.55)'}} />
			</Sequence>
			{OVS.map((ov, i) => (
				<Overlay key={i} ov={ov} />
			))}
			<EndCard />
		</AbsoluteFill>
	);
};
