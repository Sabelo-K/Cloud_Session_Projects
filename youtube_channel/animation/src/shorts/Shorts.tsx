import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Penny, Mood} from '../lib/characters';
import {Card, Paper} from '../lib/props';
import {C, G, T, useP} from '../lib/rough';
import {SfxCue, Soundtrack} from '../lib/sound';
import t1 from '../../timing_s01.json';
import t2 from '../../timing_s02.json';
import t3 from '../../timing_s03.json';
import t4 from '../../timing_s04.json';
import t5 from '../../timing_s05.json';

/**
 * Vertical (1080x1920) Shorts, driven by data: one big "beat" card per cue,
 * the spoken sentence burned in as a caption, and Penny reacting below.
 */
type Line = {start: number; end: number; text: string};
type Beat = {at: number; small?: string; big: string; color?: string; fill?: string; mood?: Mood};
export type ShortDef = {id: string; title: string; vo: string; timing: Line[]; beats: Beat[]};

const pop = (t: number, at: number, d = 0.35) => {
	if (t < at) return 0;
	const x = Math.min(1, (t - at) / d);
	return x < 0.7 ? (x / 0.7) * 1.12 : 1.12 - ((x - 0.7) / 0.3) * 0.12;
};

const Short: React.FC<{def: ShortDef}> = ({def}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	useP();
	const t = frame / fps;
	const voEnd = def.timing[def.timing.length - 1].end;
	const beatIdx = def.beats.reduce((acc, b, i) => (t >= b.at ? i : acc), 0);
	const beat = def.beats[beatIdx];
	const line = def.timing.find((l) => t >= l.start && t < l.end + 0.25);
	const sfx: SfxCue[] = def.beats.map((b, i) => [b.at + 0.05, i === def.beats.length - 1 ? 'sting' : i % 3 === 2 ? 'chaching' : 'pop', 0.4]);
	const big = beat.big.length > 12 ? 92 : beat.big.length > 8 ? 118 : 190;
	return (
		<AbsoluteFill style={{background: C.paper}}>
			<Audio src={staticFile(def.vo)} />
			<Soundtrack music="music_lofi_ep04.mp3" sfx={sfx} voEnd={voEnd} />
			<svg viewBox="0 0 1080 1920" width="100%" height="100%">
				<Paper />
				<rect x={0} y={0} width={1080} height={250} fill={C.ink} />
				<rect x={0} y={250} width={1080} height={16} fill={C.yellow} />
				<T x={540} y={80} size={46} font="marker" color={C.yellow}>
					MONEY MECHANICS
				</T>
				<T x={540} y={170} size={def.title.length > 22 ? 60 : 72} font="marker" color={C.white}>
					{def.title}
				</T>
				<G x={540} y={720} s={pop(t, beat.at)} r={beatIdx % 2 ? 2 : -2}>
					<Card w={960} h={beat.small ? 520 : 420} seed={10 + beatIdx} fill={beat.fill ?? C.white}>
						{beat.small && (
							<T x={0} y={-150} size={60}>
								{beat.small}
							</T>
						)}
						<T x={0} y={beat.small ? 40 : 10} size={big} font="marker" color={beat.color ?? C.ink}>
							{beat.big}
						</T>
					</Card>
				</G>
				{line && (
					<G x={540} y={1180}>
						<rect x={-500} y={-90} width={1000} height={180} rx={24} fill={C.ink} opacity={0.88} />
						<foreignObject x={-480} y={-85} width={960} height={170}>
							<div
								style={{
									height: 170,
									display: 'flex',
									alignItems: 'center',
									justifyContent: 'center',
									textAlign: 'center',
									color: 'white',
									fontFamily: 'Patrick Hand',
									fontSize: line.text.length > 60 ? 46 : 56,
									lineHeight: 1.1,
								}}
							>
								{line.text}
							</div>
						</foreignObject>
					</G>
				)}
				<G x={540} y={1840} s={1.25}>
					<Penny mood={beat.mood ?? 'neutral'} wave={beatIdx === def.beats.length - 1} />
				</G>
			</svg>
		</AbsoluteFill>
	);
};

const ts = (timing: Line[], i: number) => timing[i].start;
const FOLLOW = (tm: Line[]): Beat => ({at: ts(tm, tm.length - 1), small: 'follow for more', big: 'MONEY MECHANICS', color: C.ink, fill: C.yellow, mood: 'happy'});

export const SHORTS: ShortDef[] = [
	{
		id: 'Short01',
		title: 'WHERE GIFT CARDS GO',
		vo: 's01_vo.mp3',
		timing: t1,
		beats: [
			{at: 0, small: 'birthday gift card', big: '$50', mood: 'happy'},
			{at: ts(t1, 1), small: 'goes in a drawer', big: 'FORGOTTEN', mood: 'neutral'},
			{at: ts(t1, 3), small: 'adults with an unused card', big: 'ALMOST 1/2', color: C.red, mood: 'shocked'},
			{at: ts(t1, 5), small: 'unused, on average', big: '$187', color: C.red, mood: 'shocked'},
			{at: ts(t1, 6), small: 'sitting in drawers', big: '$23 BILLION', color: C.green, fill: C.yellow, mood: 'shocked'},
			{at: ts(t1, 7), small: 'the store already has', big: 'YOUR MONEY', color: C.green, mood: 'worried'},
			{at: ts(t1, 8), small: 'unspent card =', big: 'FREE SALE', color: C.red, mood: 'worried'},
			{at: ts(t1, 9), small: 'so go', big: 'SPEND IT', color: C.green, mood: 'confident'},
			FOLLOW(t1),
		],
	},
	{
		id: 'Short02',
		title: 'HOW GYMS REALLY PROFIT',
		vo: 's02_vo.mp3',
		timing: t2,
		beats: [
			{at: 0, small: 'new year, new gym', big: 'JANUARY', mood: 'happy'},
			{at: ts(t2, 1), small: 'barely going', big: 'MARCH', mood: 'worried'},
			{at: ts(t2, 2), small: 'the gym', big: 'PLANNED IT', color: C.red, mood: 'shocked'},
			{at: ts(t2, 3), small: 'members paid, per month', big: '$70+', color: C.red},
			{at: ts(t2, 4), small: 'visits per month', big: 'UNDER 5', color: C.red, mood: 'worried'},
			{at: ts(t2, 5), small: 'per visit, vs a $10 pass', big: '$17+', color: C.red, fill: C.yellow, mood: 'shocked'},
			{at: ts(t2, 6), small: 'cheaper to pay', big: 'PER VISIT', color: C.green, mood: 'thinking'},
			{at: ts(t2, 7), small: 'members vs. room for', big: '1000s / 100s', color: C.blue},
			{at: ts(t2, 8), small: 'best customer', big: 'NEVER SHOWS', color: C.red, fill: C.yellow, mood: 'confident'},
			FOLLOW(t2),
		],
	},
	{
		id: 'Short03',
		title: 'THE PRINTER INK SCAM',
		vo: 's03_vo.mp3',
		timing: t3,
		beats: [
			{at: 0, small: 'new printer', big: 'CHEAP', color: C.green, mood: 'happy'},
			{at: ts(t3, 1), small: 'the ink', big: 'NOT CHEAP', color: C.red, mood: 'worried'},
			{at: ts(t3, 2), small: 'one brand, per ml (Which?)', big: '£1.78', color: C.red, mood: 'shocked'},
			{at: ts(t3, 3), small: 'Dom Perignon, per ml', big: '24p', color: C.blue, mood: 'thinking'},
			{at: ts(t3, 4), small: 'ink vs champagne', big: '7X PRICIER', color: C.red, fill: C.yellow, mood: 'shocked'},
			{at: ts(t3, 5), small: 'the printer is', big: 'THE BAIT', color: C.red},
			{at: ts(t3, 6), small: 'the ink is', big: 'THE BUSINESS', color: C.green, mood: 'confident'},
			{at: ts(t3, 7), small: 'third-party ink saves', big: '£180+/YR', color: C.green, fill: C.yellow, mood: 'happy'},
			FOLLOW(t3),
		],
	},
	{
		id: 'Short04',
		title: 'EXTENDED WARRANTY MATH',
		vo: 's04_vo.mp3',
		timing: t4,
		beats: [
			{at: 0, small: 'new purchase', big: 'NEW TV', mood: 'happy'},
			{at: ts(t4, 1), small: 'at the till', big: 'WARRANTY?', mood: 'thinking'},
			{at: ts(t4, 3), small: 'of the product price', big: '~24%', color: C.red},
			{at: ts(t4, 4), small: 'TVs that actually failed', big: '5-8%', color: C.green, mood: 'thinking'},
			{at: ts(t4, 5), small: 'what buyers assumed', big: '13%', color: C.red, mood: 'worried'},
			{at: ts(t4, 6), small: 'that gap is', big: 'THE PROFIT', color: C.red, fill: C.yellow, mood: 'shocked'},
			{at: ts(t4, 7), small: 'estimated margins', big: '50%+', color: C.red, mood: 'shocked'},
			{at: ts(t4, 8), small: 'fear sells it', big: 'MATH WINS', color: C.green, mood: 'confident'},
			FOLLOW(t4),
		],
	},
	{
		id: 'Short05',
		title: 'AIRLINES SELL MILES',
		vo: 's05_vo.mp3',
		timing: t5,
		beats: [
			{at: 0, small: 'airline credit card', big: 'MILES', color: C.blue, mood: 'happy'},
			{at: ts(t5, 1), small: 'who pays for them?', big: '???', mood: 'thinking'},
			{at: ts(t5, 2), small: 'banks buy miles', big: 'BILLIONS', color: C.green},
			{at: ts(t5, 3), small: 'Delta from Amex, 2025', big: '$8.2 BILLION', color: C.green, fill: C.yellow, mood: 'shocked'},
			{at: ts(t5, 4), small: 'target per year', big: '$10 BILLION', color: C.green, mood: 'shocked'},
			{at: ts(t5, 5), small: 'each program could be worth', big: '$30 BILLION+', color: C.red, mood: 'shocked'},
			{at: ts(t5, 6), small: 'not really selling', big: 'SEATS', color: C.ink, mood: 'thinking'},
			{at: ts(t5, 7), small: "they're selling", big: 'MILES', color: C.red, fill: C.yellow, mood: 'confident'},
			FOLLOW(t5),
		],
	},
];

export const shortSeconds = (d: ShortDef) => d.timing[d.timing.length - 1].end + 1.5;
export const ShortComp: React.FC<{i: number}> = ({i}) => <Short def={SHORTS[i]} />;
