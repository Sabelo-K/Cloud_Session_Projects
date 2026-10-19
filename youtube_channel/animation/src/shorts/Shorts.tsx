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
		title: 'THE PAWN SHOP TRICK',
		vo: 's01_vo.mp3',
		timing: t1,
		beats: [
			{at: 0, small: 'guitar pawned for', big: '$150', mood: 'thinking'},
			{at: ts(t1, 1), small: 'fee every month', big: '20%', color: C.red, mood: 'worried'},
			{at: ts(t1, 2), small: 'just to keep the loan', big: '$30/MO', color: C.red, mood: 'worried'},
			{at: ts(t1, 3), small: 'pay the fee and extend', big: 'AGAIN...', mood: 'worried'},
			{at: ts(t1, 6), small: 'fees paid after 3 months', big: '$90', color: C.red, fill: C.yellow, mood: 'shocked'},
			{at: ts(t1, 7), small: 'still owes', big: '$150', color: C.red, mood: 'shocked'},
			{at: ts(t1, 8), small: 'she pays?', big: 'SHOP WINS', color: C.green},
			{at: ts(t1, 9), small: "she doesn't?", big: 'SHOP WINS', color: C.green},
			{at: ts(t1, 10), big: 'THE HOUSE WINS', color: C.red, fill: C.yellow, mood: 'confident'},
			FOLLOW(t1),
		],
	},
	{
		id: 'Short02',
		title: "COSTCO'S $1.50 SECRET",
		vo: 's02_vo.mp3',
		timing: t2,
		beats: [
			{at: 0, small: 'hot dog + soda since 1985', big: '$1.50', color: C.red, fill: C.yellow, mood: 'happy'},
			{at: ts(t2, 1), small: 'same price for', big: '40 YEARS', mood: 'shocked'},
			{at: ts(t2, 3), small: 'so how does it profit?', big: '???', mood: 'thinking'},
			{at: ts(t2, 4), small: 'membership, every year', big: '$65', color: C.blue},
			{at: ts(t2, 5), small: 'paid members', big: '81 MILLION', color: C.blue},
			{at: ts(t2, 6), small: 'membership fees in a year', big: '$5.3 BILLION', color: C.green, fill: C.yellow, mood: 'shocked'},
			{at: ts(t2, 7), small: 'of its entire profit', big: 'ALMOST 2/3', color: C.red},
			{at: ts(t2, 8), small: 'the hot dog is', big: 'THE BAIT', color: C.red, mood: 'confident'},
			{at: ts(t2, 10), small: 'the real business', big: 'MEMBERSHIP', color: C.green, mood: 'confident'},
			FOLLOW(t2),
		],
	},
	{
		id: 'Short03',
		title: "DON'T PAY THE MINIMUM",
		vo: 's03_vo.mp3',
		timing: t3,
		beats: [
			{at: 0, small: 'credit card balance', big: '$5,000', mood: 'worried'},
			{at: ts(t3, 1), small: 'minimum payments only', big: '19 YEARS', color: C.red, mood: 'shocked'},
			{at: ts(t3, 2), small: 'interest paid', big: '$8,000+', color: C.red, fill: C.yellow, mood: 'shocked'},
			{at: ts(t3, 3), small: 'first minimum payment', big: '~$140', mood: 'worried'},
			{at: ts(t3, 4), small: 'of that is interest', big: '$90+', color: C.red, mood: 'worried'},
			{at: ts(t3, 6), small: 'pay a flat amount', big: '$200/MO', color: C.green, mood: 'thinking'},
			{at: ts(t3, 7), small: 'debt-free in', big: '< 3 YEARS', color: C.green, mood: 'happy'},
			{at: ts(t3, 8), small: 'interest paid', big: '~$1,700', color: C.green, fill: C.yellow, mood: 'happy'},
			{at: ts(t3, 9), small: 'the minimum is', big: 'THE TRAP', color: C.red, mood: 'confident'},
			FOLLOW(t3),
		],
	},
	{
		id: 'Short04',
		title: 'THE CASINO MATH',
		vo: 's04_vo.mp3',
		timing: t4,
		beats: [
			{at: 0, small: 'walks in with', big: '$100', mood: 'happy'},
			{at: ts(t4, 1), small: 'max bet', big: '$1 A SPIN', mood: 'happy'},
			{at: ts(t4, 2), small: 'total bet before it is gone', big: '~$1,400', color: C.red, fill: C.yellow, mood: 'shocked'},
			{at: ts(t4, 3), big: "HERE'S WHY", mood: 'thinking'},
			{at: ts(t4, 4), small: 'slots keep, per dollar', big: '~7 CENTS', color: C.red},
			{at: ts(t4, 5), small: 'winnings go', big: 'BACK IN', color: C.blue, mood: 'happy'},
			{at: ts(t4, 6), small: 'every spin, a slice', big: 'ROUND & ROUND', color: C.red, mood: 'worried'},
			{at: ts(t4, 7), small: 'not one big loss', big: '1,000 TINY ONES', color: C.red, fill: C.yellow, mood: 'worried'},
			FOLLOW(t4),
		],
	},
	{
		id: 'Short05',
		title: 'THE $34 OVERDRAFT',
		vo: 's05_vo.mp3',
		timing: t5,
		beats: [
			{at: 0, small: 'lunch', big: '$24', mood: 'happy'},
			{at: ts(t5, 1), small: 'balance', big: '-$3', color: C.red, mood: 'worried'},
			{at: ts(t5, 2), small: 'overdraft fee', big: '$34', color: C.red, fill: C.yellow, mood: 'shocked'},
			{at: ts(t5, 3), small: 'paid back in', big: '3 DAYS', mood: 'worried'},
			{at: ts(t5, 4), small: 'as a yearly rate', big: '~17,000%', color: C.red, fill: C.yellow, mood: 'shocked'},
			{at: ts(t5, 6), small: 'of accounts pay most fees', big: '~8%', color: C.red},
			{at: ts(t5, 7), small: 'being broke is', big: 'EXPENSIVE', color: C.red, mood: 'worried'},
			FOLLOW(t5),
		],
	},
];

export const shortSeconds = (d: ShortDef) => d.timing[d.timing.length - 1].end + 1.5;
export const ShortComp: React.FC<{i: number}> = ({i}) => <Short def={SHORTS[i]} />;
