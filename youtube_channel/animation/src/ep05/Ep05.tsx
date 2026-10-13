import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Penny} from '../lib/characters';
import {Card, Cash, Phone, PriceTag} from '../lib/props';
import {CasinoSign} from '../lib/props2';
import {C, G, R, T} from '../lib/rough';
import {SfxCue} from '../lib/sound';
import {EndScreen, EngineLabels, Episode, Header, Label, MachineAndRules, Pie, Stat, Svg, TitleCard, useCue} from '../lib/kit';

/**
 * Episode 5: How "Free" Apps Make Billions.
 * Cue times are GLOBAL seconds from timing_ep05.json (exact Kokoro timings).
 */
export const VO5_SECONDS = 238.48;
export const EP05_SECONDS = VO5_SECONDS + 12;

// ---------------------------------------------------------------- Episode props
/** A scrolling social feed inside the phone screen; every 3rd card is a yellow AD. */
export const Feed: React.FC<{scroll: number}> = ({scroll}) => (
	<g>
		<clipPath id="feedclip">
			<rect x={-112} y={-205} width={224} height={400} />
		</clipPath>
		<g clipPath="url(#feedclip)">
			{Array.from({length: 12}).map((_, i) => {
				const y = -190 + i * 130 - (scroll % 390);
				const ad = i % 3 === 2;
				return (
					<g key={i}>
						<rect x={-100} y={y} width={200} height={115} rx={8} fill={ad ? C.yellow : '#E9E4DA'} stroke={C.ink} strokeWidth={3} />
						{ad ? (
							<text x={0} y={y + 64} textAnchor="middle" fontFamily="Permanent Marker" fontSize={36} fill={C.red}>
								AD
							</text>
						) : (
							<>
								<circle cx={-70} cy={y + 25} r={14} fill={C.blue} />
								<rect x={-45} y={y + 18} width={110} height={12} fill={C.shadow} />
								<rect x={-85} y={y + 50} width={170} height={50} fill={C.shadow} opacity={0.5} />
							</>
						)}
					</g>
				);
			})}
		</g>
	</g>
);

const Folder: React.FC<{label: string}> = ({label}) => (
	<g>
		<R s={{kind: 'polygon', pts: [[-170, -110], [-60, -110], [-40, -85], [170, -85], [170, 110], [-170, 110]]}} o={{fill: C.gold, fillStyle: 'solid'}} seed={5000} />
		<T x={0} y={20} size={50} font="marker">
			{label}
		</T>
	</g>
);

const Paddle: React.FC<{bid: string; color: string}> = ({bid, color}) => (
	<g>
		<R s={{kind: 'line', x1: 0, y1: 0, x2: 0, y2: 120}} o={{strokeWidth: 10, stroke: C.brown}} seed={5010} />
		<R s={{kind: 'circle', x: 0, y: -40, d: 130}} o={{fill: color, fillStyle: 'solid'}} seed={5011} />
		<T x={0} y={-36} size={50} font="marker" color={C.white}>
			{bid}
		</T>
	</g>
);

const Globe: React.FC<{rot: number}> = ({rot}) => (
	<g>
		<R s={{kind: 'circle', x: 0, y: 0, d: 340}} o={{fill: C.blue, fillStyle: 'solid'}} seed={5020} />
		<g transform={`translate(${((rot % 200) - 100) * 0.6} 0)`}>
			<R s={{kind: 'ellipse', x: -40, y: -50, w: 120, h: 80}} o={{fill: C.green, fillStyle: 'solid', stroke: 'none'}} seed={5021} />
			<R s={{kind: 'ellipse', x: 60, y: 50, w: 90, h: 110}} o={{fill: C.green, fillStyle: 'solid', stroke: 'none'}} seed={5022} />
		</g>
		<R s={{kind: 'circle', x: 0, y: 0, d: 340}} o={{strokeWidth: 5}} seed={5023} />
	</g>
);

const Clock: React.FC<{t: number}> = ({t}) => (
	<g>
		<R s={{kind: 'circle', x: 0, y: 0, d: 260}} o={{fill: C.white, fillStyle: 'solid'}} seed={5030} />
		<R s={{kind: 'line', x1: 0, y1: 0, x2: Math.cos(t * 3) * 100, y2: Math.sin(t * 3) * 100}} o={{strokeWidth: 8, stroke: C.red}} seed={5031} />
		<R s={{kind: 'line', x1: 0, y1: 0, x2: Math.cos(t / 3) * 60, y2: Math.sin(t / 3) * 60}} o={{strokeWidth: 10}} seed={5032} />
	</g>
);

// ---------------------------------------------------------------- 1. Hook (0 – 15.41)
const S1 = 0;
const Hook: React.FC = () => {
	const {p, pop, after, t} = useCue(S1);
	return (
		<Svg>
			<G x={560} y={600} s={pop(0.1) * 1.1}>
				<Phone>
					<Feed scroll={t * 60} />
				</Phone>
			</G>
			<G x={300} y={1000} s={0.75}>
				<Penny mood={after(12.37) ? 'thinking' : 'happy'} look={1} />
			</G>
			<G x={830} y={320} s={pop(1.5)} r={-12}>
				<PriceTag text="$0" fill={C.green} />
			</G>
			{after(4.65) && (
				<G x={1400} y={480} s={pop(8.2)}>
					<Stat label="Meta revenue, 2025" value="$201 BILLION" w={800} />
				</G>
			)}
			{after(12.37) && (
				<T x={1400} y={800} size={100} font="marker" color={C.red} scale={pop(12.6)}>
					WHO PAYS?
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 2. Promise (15.41 – 30.1)
const S2 = 15.41;
const Promise_: React.FC = () => {
	const {pop, t} = useCue(S2);
	if (t < 19.55) {
		return (
			<Svg>
				<G x={700} y={430} s={pop(15.5)}>
					<CasinoSign />
				</G>
				<T x={1450} y={460} size={90} font="marker" color={C.green} scale={pop(16.8)}>
					= FREE DRINKS
				</T>
			</Svg>
		);
	}
	if (t < 23.37) {
		return (
			<Svg>
				<TitleCard S={S2} at={19.55} subtitle='How "free" apps make billions' />
			</Svg>
		);
	}
	return (
		<Svg>
			<G x={960} y={360} s={pop(23.4) * 0.8}>
				<Phone>
					<Feed scroll={t * 60} />
				</Phone>
			</G>
			<EngineLabels S={S2} at={25.5} labels={['ATTENTION', 'DATA', 'AUCTION']} y={850} />
		</Svg>
	);
};

// ---------------------------------------------------------------- 3. Engine 1: attention (30.1 – 97.97)
const S3 = 30.1;
const Attention: React.FC = () => {
	const {p, pop, after, t} = useCue(S3);
	const part = t < 42.39 ? 1 : t < 51.83 ? 2 : t < 65.72 ? 3 : t < 76.52 ? 4 : 5;
	return (
		<Svg>
			<Header text="ENGINE #1: ATTENTION" at={30.1} S={S3} />
			{part === 1 && (
				<>
					<G x={620} y={620}>
						<Phone>
							<Feed scroll={(t - 30) * 90} />
						</Phone>
					</G>
					<G x={300} y={1010} s={0.65}>
						<Penny mood="happy" look={1} />
					</G>
					{after(37.63) && (
						<G x={1350} y={500} s={pop(37.7)}>
							<Stat label="ADS SEEN" value={String(Math.floor(Math.max(0, t - 37.6) * 3))} w={520} />
						</G>
					)}
					{after(39.02) && (
						<G x={1350} y={780} s={pop(39.1)}>
							<Label text="advertisers pay per view" w={720} size={44} />
						</G>
					)}
				</>
			)}
			{part === 2 && (
				<>
					<G x={620} y={580} s={pop(42.4)}>
						<Pie pct={0.98 * p(42.8, 1.6)} r={220} />
						<T x={0} y={290} size={56} font="marker" color={C.red}>
							ADS: {Math.round(98 * p(42.8, 1.6))}%
						</T>
					</G>
					<T x={620} y={240} size={44} scale={pop(42.6)}>
						Meta&apos;s money, 2025
					</T>
					{after(48.04) && (
						<G x={1380} y={560} s={pop(48.1)}>
							<Stat label="advertising revenue" value="$196 BILLION" w={760} />
						</G>
					)}
				</>
			)}
			{part === 3 && (
				<>
					<T x={960} y={260} size={60} font="marker" scale={pop(51.9)}>
						TWO LEVERS
					</T>
					<G x={560} y={580} s={pop(54.4)}>
						<Stat label="more ads" value={after(60.02) ? '+12%' : '?'} w={560} color={C.green} />
					</G>
					<G x={1360} y={580} s={pop(55.6)}>
						<Stat label="price per ad" value={after(62.5) ? '+9%' : '?'} w={560} color={C.green} />
					</G>
					{after(57.52) && (
						<T x={960} y={860} size={56} font="marker" color={C.red} scale={pop(57.6)}>
							Meta pulled both
						</T>
					)}
				</>
			)}
			{part === 4 && (
				<>
					<G x={560} y={560} s={pop(65.8)}>
						<Clock t={t} />
					</G>
					<T x={1250} y={480} size={64} font="marker" scale={pop(66.5)}>
						the product = your hours
					</T>
					{after(71.97) && (
						<T x={1250} y={620} size={48} color={C.red} scale={pop(72)}>
							every extra minute = more ads to sell
						</T>
					)}
				</>
			)}
			{part === 5 && (
				<>
					<G x={560} y={520} s={pop(76.6)}>
						<R s={{kind: 'rect', x: -300, y: -60, w: 600, h: 120}} o={{fill: C.white, fillStyle: 'solid'}} seed={51} />
						<R s={{kind: 'circle', x: -240, y: 0, d: 60}} o={{strokeWidth: 6}} seed={52} />
						<R s={{kind: 'line', x1: -218, y1: 22, x2: -190, y2: 50}} o={{strokeWidth: 8}} seed={53} />
						<T x={20} y={4} size={40} color={C.shadow}>
							search...
						</T>
					</G>
					<G x={560} y={780} s={pop(77.5)}>
						<R s={{kind: 'rect', x: -130, y: -90, w: 260, h: 180}} o={{fill: C.red, fillStyle: 'solid'}} seed={54} />
						<R s={{kind: 'polygon', pts: [[-30, -45], [50, 0], [-30, 45]]}} o={{fill: C.white, fillStyle: 'solid'}} seed={55} />
					</G>
					{after(83.62) && (
						<G x={1350} y={430} s={pop(86)}>
							<Stat label="Google ads, last 3 months of 2025" value="$82.3 BILLION" w={860} />
						</G>
					)}
					{after(89.7) && (
						<G x={1350} y={700} s={pop(89.8)}>
							<Stat label="from YouTube alone" value="$11.4 BILLION" w={760} color={C.red} fill={C.white} />
						</G>
					)}
					{after(95.23) && (
						<T x={1350} y={920} size={52} font="marker" color={C.green} scale={pop(95.3)}>
							free to watch, not free to run
						</T>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 4. Engine 2: data (97.97 – 130.4)
const S4 = 97.97;
const tags = ['likes dogs', 'searched: running shoes', 'lives near the beach', 'up at 1 a.m.', 'paused on a sneaker ad'];
const Data: React.FC = () => {
	const {p, pop, after, t} = useCue(S4);
	return (
		<Svg>
			<Header text="ENGINE #2: DATA" at={97.97} S={S4} />
			{t < 115.96 ? (
				<>
					<G x={360} y={1000} s={0.8}>
						<Penny mood="happy" />
					</G>
					<G x={1450} y={680} s={pop(100.1)}>
						<Folder label="PENNY" />
					</G>
					{tags.map((tg, i) => {
						const at = 101.3 + i * 2.2;
						if (!after(at)) return null;
						const k = p(at + 0.8, 1.4);
						return (
							<G key={tg} x={interpolate(k, [0, 1], [480, 1450])} y={interpolate(k, [0, 1], [300 + i * 110, 620])} s={1 - k * 0.5}>
								<Label text={tg} w={tg.length * 24 + 80} size={40} seed={10 + i} />
							</G>
						);
					})}
				</>
			) : (
				<>
					<G x={480} y={560} s={pop(116)}>
						<Card w={620} h={420} seed={20}>
							<T x={0} y={-150} size={46} font="marker">
								RANDOM AD
							</T>
							{Array.from({length: 12}).map((_, i) => (
								<R key={i} s={{kind: 'circle', x: -220 + (i % 6) * 88, y: -40 + Math.floor(i / 6) * 100, d: 50}} o={{fill: C.shadow, fillStyle: 'solid'}} seed={21 + i} boil={false} />
							))}
							<T x={0} y={160} size={56} font="marker" color={C.shadow}>
								$
							</T>
						</Card>
					</G>
					<G x={1440} y={560} s={pop(117)}>
						<Card w={620} h={420} seed={30} fill={C.yellow}>
							<T x={0} y={-150} size={46} font="marker">
								TARGETED AD
							</T>
							<R s={{kind: 'circle', x: 0, y: 0, d: 120}} o={{fill: C.red, fillStyle: 'solid'}} seed={31} />
							<R s={{kind: 'circle', x: 0, y: 0, d: 50}} o={{fill: C.white, fillStyle: 'solid'}} seed={32} />
							<T x={0} y={160} size={56} font="marker" color={C.green}>
								$$$
							</T>
						</Card>
					</G>
					{after(119.93) && (
						<T x={960} y={890} size={50} font="marker" scale={pop(120)}>
							customers: the advertisers
						</T>
					)}
					{after(124.84) && (
						<T x={960} y={990} size={58} font="marker" color={C.red} scale={pop(124.9)}>
							the product: Penny
						</T>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 5. Engine 3: auction (130.4 – 193.27)
const S5 = 130.4;
const Auction: React.FC = () => {
	const {p, pop, after, t} = useCue(S5);
	const part = t < 151.4 ? 1 : t < 171.76 ? 2 : 3;
	const bids = ['$2', '$3', '$5'];
	return (
		<Svg>
			<Header text="ENGINE #3: THE AUCTION" at={130.4} S={S5} />
			{part === 1 && (
				<>
					<G x={960} y={520} s={pop(133.8)}>
						<Card w={680} h={260} seed={40}>
							<T x={0} y={-70} size={40}>
								AD SLOT ON PENNY&apos;S SCREEN
							</T>
							<T x={0} y={30} size={90} font="marker" color={C.red}>
								{after(146.12) ? '$5' : after(140) ? '$3' : after(136.54) ? '$2' : '?'}
							</T>
						</Card>
					</G>
					{bids.map((b, i) =>
						after(136.54 + i * 2.5) ? (
							<G key={b} x={420 + i * 540} y={900} s={pop(136.6 + i * 2.5)} r={Math.sin(t * 6 + i) * 6}>
								<Paddle bid={b} color={[C.blue, C.green, C.red][i]} />
							</G>
						) : null,
					)}
					{after(143) && (
						<T x={960} y={250} size={46} color={C.green} scale={pop(143)}>
							decided in a fraction of a second
						</T>
					)}
				</>
			)}
			{part === 2 && (
				<>
					<G x={520} y={580} s={pop(151.5)}>
						<Globe rot={t * 20} />
					</G>
					{after(154.23) && (
						<G x={1350} y={360} s={pop(156)}>
							<Stat label="people on Meta apps, every day" value="3.58 BILLION" w={820} />
						</G>
					)}
					{after(159.87) && (
						<G x={1350} y={650} s={pop(160)}>
							<Card w={820} h={200} seed={42}>
								<T x={0} y={-45} size={44}>
									$196B / 3.58B people
								</T>
								<T x={0} y={40} size={80} font="marker" color={C.green}>
									= ~$55 a year each
								</T>
							</Card>
						</G>
					)}
					{after(168.93) && (
						<T x={1350} y={900} size={56} font="marker" color={C.red} scale={pop(169)}>
							somebody pays for Penny
						</T>
					)}
				</>
			)}
			{part === 3 && (
				<>
					<G x={560} y={560} s={pop(176)}>
						<Card w={620} h={300} seed={43}>
							<T x={0} y={-80} size={50} font="marker">
								WITH ADS
							</T>
							<T x={0} y={40} size={110} font="marker" color={C.green}>
								FREE
							</T>
						</Card>
					</G>
					{after(183.66) && (
						<G x={1360} y={560} s={pop(184.9)}>
							<Card w={620} h={300} seed={44} fill={C.yellow}>
								<T x={0} y={-80} size={50} font="marker">
									NO ADS (EUROPE)
								</T>
								<T x={0} y={40} size={84} font="marker" color={C.red}>
									9.99 EUR/mo
								</T>
							</Card>
						</G>
					)}
					{after(188.48) && (
						<T x={960} y={900} size={54} font="marker" scale={pop(188.5)}>
							the price of your attention
						</T>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 6. Machine (193.27 – 228.68)
const S6 = 193.27;
const Machine: React.FC = () => (
	<MachineAndRules
		S={S6}
		labels={['ATTENTION', 'DATA', 'AUCTION']}
		gearAt={[195.3, 197.97, 200.16]}
		punch={[
			{text: 'it doesn\u2019t need your money...', at: 203.24},
			{text: 'IT NEEDS YOUR TIME', at: 205.63},
		]}
		rulesAt={207.46}
		banner="spend your time on purpose"
		rules={[
			{text: 'Turn off notifications you didn’t ask for.', at: 211.0},
			{text: 'Check your ad and tracking settings.', at: 218.6},
			{text: 'Set a daily screen-time limit.', at: 223.87},
		]}
	/>
);

// ---------------------------------------------------------------- 7. Payoff + bridge (228.68 – 238.48)
const S7 = 228.68;
const Payoff: React.FC = () => {
	const {pop, after, t} = useCue(S7);
	const frame = useCurrentFrame();
	return (
		<Svg>
			<G x={960} y={620} s={0.9} r={after(230.96) ? Math.sin(frame) * 2 : 0}>
				<R s={{kind: 'rect', x: -240, y: -130, w: 480, h: 260}} o={{fill: C.ink, fillStyle: 'solid'}} seed={60} />
			</G>
			<G x={400} y={1000} s={0.8}>
				<Penny mood={after(230.96) ? 'worried' : 'happy'} look={1} />
			</G>
			{after(230.96) && (
				<G x={1000} y={380} s={pop(231)}>
					<Label text="Your free trial ends tomorrow" w={900} size={48} fill={C.yellow} />
				</G>
			)}
			{t < 230.96 && (
				<T x={960} y={330} size={64} font="marker" scale={pop(228.8)}>
					free apps sell your time
				</T>
			)}
			{after(234.78) && (
				<T x={1000} y={930} size={64} font="marker" color={C.red} scale={pop(234.8)}>
					NEXT: THE SUBSCRIPTION TRAP
				</T>
			)}
			<G x={1500} y={700} s={0.5}>
				<Cash />
			</G>
		</Svg>
	);
};

const End: React.FC = () => <EndScreen S={VO5_SECONDS} />;

const SFX: SfxCue[] = [
	[0.1, 'pop', 0.45],
	[1.5, 'ding', 0.4],
	[8.2, 'chaching', 0.5],
	[12.6, 'sting_dark', 0.45],
	[15.5, 'neon', 0.4],
	[16.8, 'pop', 0.4],
	[19.55, 'sting', 0.6],
	[23.4, 'whoosh', 0.4],
	[25.5, 'pop', 0.4],
	[26.2, 'pop', 0.4],
	[26.9, 'pop', 0.4],
	[30.1, 'pop', 0.5],
	[37.7, 'beep', 0.4],
	[39.1, 'chaching', 0.4],
	[42.8, 'rise', 0.35],
	[48.1, 'chaching', 0.5],
	[54.4, 'pop', 0.4],
	[55.6, 'pop', 0.4],
	[60.02, 'ding', 0.4],
	[62.5, 'ding', 0.4],
	[65.8, 'clock', 0.4],
	[76.6, 'whoosh', 0.4],
	[86.0, 'chaching', 0.5],
	[89.8, 'chaching', 0.45],
	[97.97, 'pop', 0.5],
	[101.3, 'plink', 0.35],
	[103.5, 'plink', 0.35],
	[105.7, 'plink', 0.35],
	[107.9, 'plink', 0.35],
	[110.1, 'plink', 0.35],
	[116.0, 'flip', 0.4],
	[117.0, 'pop', 0.4],
	[124.9, 'sting_dark', 0.45],
	[130.4, 'pop', 0.5],
	[136.6, 'slap', 0.4],
	[139.1, 'slap', 0.4],
	[141.6, 'slap', 0.4],
	[146.12, 'chaching', 0.45],
	[151.5, 'whoosh', 0.4],
	[156.0, 'rise', 0.35],
	[160.0, 'chaching', 0.5],
	[169.0, 'sting_dark', 0.45],
	[176.0, 'pop', 0.4],
	[184.9, 'stamp', 0.5],
	[193.4, 'pop', 0.5],
	[195.3, 'whirr', 0.35],
	[197.97, 'whirr', 0.35],
	[200.16, 'whirr', 0.35],
	[205.63, 'sting_dark', 0.45],
	[207.46, 'pop', 0.45],
	[210.1, 'pop', 0.45],
	[217.7, 'pop', 0.45],
	[223.0, 'pop', 0.45],
	[212.5, 'tick', 0.5],
	[220.1, 'tick', 0.5],
	[225.4, 'tick', 0.5],
	[231.0, 'buzzer', 0.4],
	[234.8, 'sting_dark', 0.5],
];

export const Ep05: React.FC = () => (
	<Episode
		vo="ep05_vo.mp3"
		music="music_lofi_ep04.mp3"
		voEnd={VO5_SECONDS}
		total={EP05_SECONDS}
		sfx={SFX}
		dips={[12.37, 159.87]}
		scenes={[
			[S1, Hook],
			[S2, Promise_],
			[S3, Attention],
			[S4, Data],
			[S5, Auction],
			[S6, Machine],
			[S7, Payoff],
			[VO5_SECONDS, End],
		]}
	/>
);
