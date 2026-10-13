import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Penny} from '../lib/characters';
import {Card, Cash, Coin, Gear, Paper, Phone, Tick} from '../lib/props';
import {CasinoSign, Warehouse} from '../lib/props2';
import {C, G, R, T, countUp, useP} from '../lib/rough';
import {SfxCue, Soundtrack} from '../lib/sound';

/**
 * Episode 4: How Casinos Make Money (The Math Is Brutal).
 * Cue times are GLOBAL seconds from timing_ep04.json (exact Kokoro timings).
 */
export const VO4_SECONDS = 254.97;
export const EP04_SECONDS = VO4_SECONDS + 12;

const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
	<svg viewBox="0 0 1920 1080" width="100%" height="100%">
		<Paper />
		{children}
	</svg>
);

const useCue = (sceneStart: number) => {
	const h = useP();
	return {
		...h,
		t: h.t + sceneStart,
		p: (g: number, d?: number) => h.p(g - sceneStart, d),
		pop: (g: number, d?: number) => h.pop(g - sceneStart, d),
		after: (g: number) => h.t + sceneStart >= g,
	};
};

const money = (n: number) => '$' + n.toLocaleString('en-US');

// ---------------------------------------------------------------- Episode props
const FELT = '#1F7A4D';

/** Slot machine, origin at base centre. ~560 tall. */
export const SlotMachine: React.FC<{spin?: boolean; draw?: number; reels?: string[]}> = ({spin = false, draw = 1, reels = ['7', '$', '7']}) => {
	const frame = useCurrentFrame();
	const syms = ['7', '$', 'BAR', '7', '$'];
	return (
		<g>
			<R s={{kind: 'rect', x: -170, y: -560, w: 340, h: 560}} o={{fill: C.red, fillStyle: 'solid'}} draw={draw} seed={3000} />
			<R s={{kind: 'rect', x: -150, y: -620, w: 300, h: 70}} o={{fill: C.yellow, fillStyle: 'solid'}} draw={draw} seed={3001} />
			<T x={0} y={-584} size={44} font="marker" scale={Math.min(1, draw)}>
				JACKPOT
			</T>
			<R s={{kind: 'rect', x: -140, y: -500, w: 280, h: 150}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={3002} />
			{[0, 1, 2].map((i) => (
				<React.Fragment key={i}>
					{i > 0 && <R s={{kind: 'line', x1: -140 + i * 93, y1: -500, x2: -140 + i * 93, y2: -350}} o={{strokeWidth: 3}} draw={draw} seed={3003 + i} boil={false} />}
					{(() => {
						const sym = spin ? syms[(Math.floor(frame / 2) + i * 2) % syms.length] : reels[i];
						return (
							<T x={-93 + i * 93} y={-425} size={sym === 'BAR' ? 34 : 64} font="marker" color={C.ink} scale={Math.min(1, draw)}>
								{sym}
							</T>
						);
					})()}
				</React.Fragment>
			))}
			<R s={{kind: 'rect', x: -60, y: -300, w: 120, h: 24}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={3008} />
			<R s={{kind: 'rect', x: -120, y: -150, w: 240, h: 60}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={3009} />
			<R s={{kind: 'line', x1: 170, y1: -380, x2: 230, y2: spin ? -330 : -480}} o={{strokeWidth: 10}} draw={draw} seed={3010} />
			<R s={{kind: 'circle', x: 230, y: spin ? -330 : -480, d: 46}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={3011} />
		</g>
	);
};

/** Roulette strip of 38 pockets, origin top-left of strip. */
const RouletteStrip: React.FC<{highlight?: number; ballAt?: number; draw?: number; zeros?: 1 | 2; cell?: number}> = ({
	highlight = -1,
	ballAt = -1,
	draw = 1,
	zeros = 2,
	cell = 44,
}) => {
	const labels = [...(zeros === 2 ? ['0', '00'] : ['0']), ...Array.from({length: 36}, (_, i) => String(i + 1))];
	return (
		<g>
			{labels.map((l, i) => {
				const green = i < zeros;
				const red = !green && i % 2 === 0;
				const fill = green ? C.green : red ? C.red : C.ink;
				return (
					<g key={l}>
						<R s={{kind: 'rect', x: i * cell, y: 0, w: cell - 4, h: 90}} o={{fill, fillStyle: 'solid', stroke: i === highlight ? C.yellow : C.ink, strokeWidth: i === highlight ? 7 : 2}} draw={draw} seed={3100 + i} boil={false} />
						<T x={i * cell + cell / 2 - 2} y={45} size={l.length > 1 ? 18 : 24} color={C.white} scale={Math.min(1, draw)}>
							{l}
						</T>
						{i === ballAt && <R s={{kind: 'circle', x: i * cell + cell / 2 - 2, y: -30, d: 34}} o={{fill: C.white, fillStyle: 'solid'}} seed={3190} />}
					</g>
				);
			})}
		</g>
	);
};

/** Round roulette wheel, origin centre. */
const Wheel: React.FC<{zeros: 1 | 2; rot?: number; r?: number}> = ({zeros, rot = 0, r = 200}) => {
	const n = zeros === 2 ? 38 : 37;
	return (
		<g>
			<R s={{kind: 'circle', x: 0, y: 0, d: r * 2 + 30}} o={{fill: C.brown, fillStyle: 'solid'}} seed={3200 + zeros} />
			<g transform={`rotate(${rot})`}>
				{Array.from({length: n}).map((_, i) => {
					const a0 = (i / n) * Math.PI * 2;
					const a1 = ((i + 1) / n) * Math.PI * 2;
					const fill = i < zeros ? C.green : i % 2 ? C.red : C.ink;
					return (
						<path
							key={i}
							d={`M 0 0 L ${Math.cos(a0) * r} ${Math.sin(a0) * r} A ${r} ${r} 0 0 1 ${Math.cos(a1) * r} ${Math.sin(a1) * r} Z`}
							fill={fill}
							stroke={C.ink}
							strokeWidth={1.5}
						/>
					);
				})}
			</g>
			<R s={{kind: 'circle', x: 0, y: 0, d: r * 0.9}} o={{fill: C.gold, fillStyle: 'solid'}} seed={3210 + zeros} />
			<R s={{kind: 'circle', x: 0, y: 0, d: 40}} o={{fill: C.ink, fillStyle: 'solid'}} seed={3220} />
		</g>
	);
};

const Chip: React.FC<{color?: string; seed?: number}> = ({color = C.red, seed = 1}) => (
	<g>
		<R s={{kind: 'circle', x: 0, y: 0, d: 70}} o={{fill: color, fillStyle: 'solid'}} seed={3300 + seed} />
		<R s={{kind: 'circle', x: 0, y: 0, d: 40}} o={{stroke: C.white, strokeWidth: 4, strokeLineDash: [8, 6]}} seed={3310 + seed} boil={false} />
	</g>
);

const Drink: React.FC = () => (
	<g>
		<R s={{kind: 'polygon', pts: [[-60, -140], [60, -140], [0, -50]]}} o={{fill: '#9BE7B4', fillStyle: 'solid'}} seed={3400} />
		<R s={{kind: 'line', x1: 0, y1: -50, x2: 0, y2: 0}} o={{strokeWidth: 6}} seed={3401} />
		<R s={{kind: 'line', x1: -40, y1: 0, x2: 40, y2: 0}} o={{strokeWidth: 6}} seed={3402} />
		<R s={{kind: 'circle', x: 30, y: -150, d: 30}} o={{fill: C.red, fillStyle: 'solid'}} seed={3403} />
	</g>
);

const KeyCard: React.FC = () => (
	<g>
		<R s={{kind: 'rect', x: -110, y: -70, w: 220, h: 140}} o={{fill: C.blue, fillStyle: 'solid'}} seed={3410} />
		<R s={{kind: 'rect', x: -110, y: -40, w: 220, h: 26}} o={{fill: C.ink, fillStyle: 'solid'}} seed={3411} />
		<T x={0} y={36} size={34} font="marker" color={C.white}>
			ROOM 777
		</T>
	</g>
);

const Plate: React.FC = () => (
	<g>
		<R s={{kind: 'ellipse', x: 0, y: 0, w: 240, h: 90}} o={{fill: C.white, fillStyle: 'solid'}} seed={3420} />
		<R s={{kind: 'ellipse', x: -30, y: -20, w: 90, h: 50}} o={{fill: C.brown, fillStyle: 'hachure'}} seed={3421} />
		<R s={{kind: 'ellipse', x: 50, y: -15, w: 60, h: 40}} o={{fill: C.green, fillStyle: 'hachure'}} seed={3422} />
	</g>
);

const LoyaltyCard: React.FC<{glow?: boolean}> = ({glow = false}) => {
	const frame = useCurrentFrame();
	return (
		<g>
			<R
				s={{kind: 'rect', x: -170, y: -105, w: 340, h: 210}}
				o={{fill: C.gold, fillStyle: 'solid', stroke: glow ? C.red : C.ink, strokeWidth: glow ? 4 + Math.abs(Math.sin(frame / 5)) * 5 : 3.5}}
				seed={3430}
			/>
			<T x={0} y={-40} size={40} font="marker">
				PLAYERS CLUB
			</T>
			<T x={0} y={40} size={30}>
				PENNY  ****  777
			</T>
		</g>
	);
};

const Title: React.FC<{text: string; at: number; S: number}> = ({text, at, S}) => {
	const {pop} = useCue(S);
	return (
		<T x={960} y={100} size={74} font="marker" scale={pop(at)}>
			{text}
		</T>
	);
};

const BetCounter: React.FC<{value: number; label?: string}> = ({value, label = 'TOTAL BET'}) => (
	<Card w={600} h={220} seed={1} fill={C.yellow}>
		<T x={0} y={-55} size={40} font="marker">
			{label}
		</T>
		<T x={0} y={35} size={100} font="marker" color={C.red}>
			{money(value)}
		</T>
	</Card>
);

// ---------------------------------------------------------------- 1. Hook (0 – 16.88)
const S1 = 0;
const Hook: React.FC = () => {
	const {p, pop, after, t} = useCue(S1);
	const bill = 1 - p(8, 5);
	return (
		<Svg>
			<G x={560} y={960}>
				<SlotMachine spin={after(7.08) && t < 13.4} draw={p(0.1, 0.8)} />
			</G>
			<G x={880} y={980}>
				<Penny mood={after(13.42) ? 'shocked' : after(7.08) ? 'worried' : 'happy'} draw={p(0.3, 0.8)} look={-1} />
			</G>
			{bill > 0.02 && (
				<G x={1000} y={520} s={pop(1) * (0.4 + bill)}>
					<Cash thick />
					<T x={0} y={70} size={44} font="marker">
						$100
					</T>
				</G>
			)}
			{after(3.73) && (
				<G x={1500} y={260} s={pop(3.8)}>
					<Card w={420} h={110} seed={2}>
						<T x={0} y={6} size={50} font="marker">
							$1 per spin
						</T>
					</Card>
				</G>
			)}
			{after(7.08) && (
				<G x={1500} y={560} s={pop(7.1)}>
					<BetCounter value={Math.round(100 + 1289 * p(8, 5))} />
				</G>
			)}
			{after(13.42) && (
				<T x={1500} y={850} size={56} font="marker" color={C.green} scale={pop(13.6)}>
					no cheating required
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 2. Promise + title (16.88 – 32.81)
const S2 = 16.88;
const Promise_: React.FC = () => {
	const {p, pop, t} = useCue(S2);
	const rot = t * 40;
	if (t < 21.09) {
		return (
			<Svg>
				<G x={0} y={60} s={0.85}>
					<Warehouse draw={p(16.9, 0.8)} />
				</G>
				<T x={1450} y={560} size={110} font="marker" color={C.blue} scale={pop(18.2)}>
					= BELONGING
				</T>
			</Svg>
		);
	}
	if (t < 26.38) {
		return (
			<Svg>
				<G x={960} y={470} s={pop(21.09, 0.6)}>
					<G x={-420} y={0}>
						<Gear r={110} rot={rot * 2} fill={C.yellow} seed={4} />
					</G>
					<G x={420} y={0}>
						<Gear r={110} rot={-rot * 2} fill={C.yellow} seed={5} />
					</G>
					<T x={0} y={-40} size={130} font="marker">
						MONEY
					</T>
					<T x={0} y={90} size={130} font="marker" color={C.yellow} stroke={C.ink}>
						MECHANICS
					</T>
				</G>
				<T x={960} y={820} size={54} scale={pop(22)}>
					How casinos make money
				</T>
			</Svg>
		);
	}
	return (
		<Svg>
			<G x={960} y={330} s={pop(26.38) * 1.1}>
				<CasinoSign />
			</G>
			{['EDGE', 'CHURN', 'FREEBIES'].map((l, i) => (
				<G key={l} x={460 + i * 500} y={700} s={pop(27.5 + i * 0.7)}>
					<Card w={380} h={120} seed={2 + i} fill={i === 1 ? C.red : C.white}>
						<T x={0} y={6} size={58} font="marker" color={i === 1 ? C.white : C.ink}>
							{l}
						</T>
					</Card>
				</G>
			))}
			<T x={960} y={930} size={84} font="marker" color={C.green} scale={pop(30)}>
				$78 BILLION A YEAR
			</T>
		</Svg>
	);
};

// ---------------------------------------------------------------- 3. Engine 1: the edge (32.81 – 93.68)
const S3 = 32.81;
const Edge: React.FC = () => {
	const {p, pop, after, t} = useCue(S3);
	const part = t < 50.01 ? 1 : t < 65.97 ? 2 : t < 75.92 ? 3 : 4;
	const stripX = 960 - (38 * 44) / 2;
	// ball hops along strip while the 38 spins play
	const spins = Math.min(38, Math.floor(Math.max(0, t - 55.65) / 0.12));
	const wins = spins >= 20 ? 1 : 0;
	return (
		<Svg>
			<Title text="ENGINE #1: THE EDGE" at={32.81} S={S3} />
			{(part === 1 || part === 2) && (
				<G x={stripX} y={330} o={1}>
					<RouletteStrip highlight={after(44.07) ? 8 : -1} draw={p(36.1, 1.2)} ballAt={part === 2 ? (spins * 7) % 38 : -1} />
				</G>
			)}
			{part === 1 && (
				<>
					{after(38.08) && (
						<T x={960} y={520} size={90} font="marker" scale={pop(38.2)}>
							38 POCKETS
						</T>
					)}
					{after(40.68) && (
						<T x={960} y={620} size={48} color={C.green} scale={pop(42.2)}>
							36 numbers + two green zeros
						</T>
					)}
					{after(44.07) && (
						<>
							<G x={stripX + 8 * 44 + 20} y={280} s={pop(44.2) * 0.7}>
								<Chip />
							</G>
							<G x={420} y={1010} s={0.7}>
								<Penny mood="happy" />
							</G>
							<G x={1300} y={820} s={pop(46.5)}>
								<Card w={700} h={170} seed={3} fill={C.yellow}>
									<T x={0} y={-30} size={40}>
										bet $1, win and you get
									</T>
									<T x={0} y={40} size={64} font="marker" color={C.green}>
										$35
									</T>
								</Card>
							</G>
						</>
					)}
				</>
			)}
			{part === 2 && (
				<>
					<T x={480} y={540} size={52} font="marker" scale={pop(50.1)}>
						fair payout: $37
					</T>
					<T x={1440} y={540} size={52} font="marker" color={C.red} scale={pop(52.8)}>
						actual: $35
					</T>
					{after(55.65) && (
						<G x={960} y={790} s={pop(55.7)}>
							<Card w={1100} h={260} seed={4}>
								<T x={-300} y={-60} size={40}>
									spins: {spins} / 38
								</T>
								<T x={300} y={-60} size={40} color={C.green}>
									wins: {wins}  (+$35)
								</T>
								<T x={-300} y={20} size={40} color={C.red}>
									losses: {spins - wins}  (-${spins - wins})
								</T>
								<T x={300} y={40} size={84} font="marker" color={spins >= 38 ? C.red : C.ink}>
									{spins >= 38 ? '-$2' : '...'}
								</T>
							</Card>
						</G>
					)}
					{after(60.74) && (
						<T x={960} y={1010} size={56} font="marker" color={C.red} scale={pop(60.8)}>
							= 5.26 cents of every $1, gone
						</T>
					)}
				</>
			)}
			{part === 3 && (
				<>
					{['BLACKJACK', 'CRAPS', 'BACCARAT'].map((l, i) => (
						<G key={l} x={420 + i * 540} y={460} s={pop(69.11 + i * 0.6)}>
							<Card w={440} h={180} seed={5 + i} fill={FELT}>
								<T x={0} y={6} size={56} font="marker" color={C.white}>
									{l}
								</T>
							</Card>
						</G>
					))}
					{after(71.56) && (
						<G x={960} y={790}>
							<R s={{kind: 'line', x1: -500, y1: 0, x2: -500 + 1000 * p(72.5, 1.2), y2: 0}} o={{strokeWidth: 14, stroke: C.red}} seed={9} />
							<R s={{kind: 'polygon', pts: [[-500 + 1000 * p(72.5, 1.2), -40], [-500 + 1000 * p(72.5, 1.2) + 60, 0], [-500 + 1000 * p(72.5, 1.2), 40]]}} o={{fill: C.red, fillStyle: 'solid', stroke: C.red}} seed={10} />
							<T x={0} y={-70} size={56} font="marker" scale={pop(72)}>
								always toward the house
							</T>
						</G>
					)}
				</>
			)}
			{part === 4 && (
				<>
					<G x={560} y={560} s={pop(78.8)}>
						<Wheel zeros={1} rot={t * 30} />
						<T x={0} y={290} size={56} font="marker" color={C.green}>
							ONE ZERO: 2.7 CENTS
						</T>
					</G>
					{after(81) && (
						<G x={1360} y={560} s={pop(83)}>
							<Wheel zeros={2} rot={-t * 30} />
							<T x={0} y={290} size={56} font="marker" color={C.red}>
								TWO ZEROS: 5.26 CENTS
							</T>
						</G>
					)}
					{after(91.79) && (
						<T x={960} y={1010} size={72} font="marker" color={C.red} scale={pop(91.8)}>
							TWICE THE EDGE
						</T>
					)}
					{t < 91.79 && after(89) && (
						<G x={960} y={1050} s={0.5}>
							<Penny mood="shocked" />
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 4. Engine 2: the churn (93.68 – 164.28)
const S4 = 93.68;
const Churn: React.FC = () => {
	const {p, pop, after, t} = useCue(S4);
	const part = t < 114.85 ? 1 : t < 144.28 ? 2 : 3;
	return (
		<Svg>
			{part !== 3 && <Title text="ENGINE #2: THE CHURN" at={93.68} S={S4} />}
			{part === 1 && (
				<>
					<G x={380} y={1000} s={pop(97.07) * 0.9}>
						<SlotMachine spin />
					</G>
					{after(98.72) && (
						<G x={1200} y={330} s={pop(100.5)}>
							<Card w={860} h={190} seed={11} fill={C.yellow}>
								<T x={0} y={-45} size={38}>
									Nevada slot win, 2024
								</T>
								<T x={0} y={35} size={90} font="marker" color={C.green}>
									${(10.5 * p(100.5, 1.5)).toFixed(1)} BILLION
								</T>
							</Card>
						</G>
					)}
					{after(104.65) && (
						<G x={1000} y={720} s={pop(104.7)}>
							<R s={{kind: 'circle', x: 0, y: 0, d: 260}} o={{fill: C.white, fillStyle: 'solid'}} seed={12} />
							<path
								d={`M 0 0 L 0 -130 A 130 130 0 1 1 ${Math.cos(-Math.PI / 2 + 0.67 * 2 * Math.PI * p(105, 1)) * 130} ${Math.sin(-Math.PI / 2 + 0.67 * 2 * Math.PI * p(105, 1)) * 130} Z`}
								fill={C.red}
								opacity={p(105, 0.2)}
								stroke={C.ink}
								strokeWidth={3}
							/>
							<T x={0} y={180} size={40}>
								~2/3 of all casino win
							</T>
						</G>
					)}
					{after(109.04) && (
						<G x={1550} y={720} s={pop(111.5)}>
							<Coin />
							<T x={0} y={90} size={64} font="marker" color={C.red}>
								7 CENTS
							</T>
							<T x={0} y={150} size={36}>
								kept per $1 played
							</T>
						</G>
					)}
				</>
			)}
			{part === 2 && (
				<>
					<G x={520} y={1000} s={0.9}>
						<SlotMachine spin={after(118.91)} />
					</G>
					<G x={850} y={1010} s={0.75}>
						<Penny mood={after(130.66) ? 'worried' : 'happy'} look={-1} />
					</G>
					{/* loop of coins going round */}
					{after(121.87) &&
						[0, 1, 2, 3].map((i) => {
							const k = ((t - 121.87 + i * 0.6) % 2.4) / 2.4;
							const a = k * Math.PI * 2;
							return (
								<G key={i} x={700 + Math.cos(a) * 200} y={470 + Math.sin(a) * 120} s={0.8 - Math.min(0.5, (t - 121.87) * 0.02)}>
									<Coin seed={i} />
								</G>
							);
						})}
					{after(124.13) && (
						<T x={700} y={250} size={48} font="marker" color={C.red} scale={pop(127)}>
							-7 cents every spin
						</T>
					)}
					{after(114.85) && (
						<G x={1450} y={300} s={pop(114.9) * 0.8}>
							<Card w={760} h={140} seed={13}>
								<T x={0} y={6} size={52} font="marker">
									KEPT PER SPIN: 7 CENTS
								</T>
							</Card>
						</G>
					)}
					{after(130.66) && (
						<G x={1450} y={600} s={pop(130.7) * 0.9}>
							<BetCounter value={Math.round(100 + 1289 * p(131, 6))} />
						</G>
					)}
					{after(130.66) && (
						<G x={1450} y={880} s={pop(131) * 0.8}>
							<Card w={560} h={130} seed={14}>
								<T x={0} y={6} size={50} font="marker" color={C.green}>
									Penny&apos;s $100: ${Math.round(100 * (1 - p(131, 6)))}
								</T>
							</Card>
						</G>
					)}
					{after(140.41) && (
						<rect x={0} y={0} width={1920} height={1080} fill={C.paper} opacity={0.85 * p(140.41, 0.3)} />
					)}
					{after(140.41) && (
						<>
							{Array.from({length: 60}).map((_, i) =>
								after(140.5 + i * 0.03) ? (
									<G key={i} x={260 + (i % 15) * 100} y={420 + Math.floor(i / 15) * 90} s={0.35}>
										<Coin seed={i % 5} />
									</G>
								) : null,
							)}
							<T x={960} y={850} size={64} font="marker" color={C.red} scale={pop(140.5)}>
								a thousand tiny losses
							</T>
						</>
					)}
				</>
			)}
			{part === 3 && (
				<>
					<T x={960} y={110} size={64} font="marker" scale={pop(144.3)}>
						no building required
					</T>
					<G x={560} y={590} s={pop(144.5)}>
						<Phone>
							<G x={0} y={60} s={0.3}>
								<SlotMachine spin />
							</G>
							<T x={0} y={130} size={30} font="marker" color={C.red}>
								SPIN NOW
							</T>
						</Phone>
					</G>
					{after(147.63) && (
						<G x={1340} y={430} s={pop(149.5)}>
							<Card w={760} h={180} seed={15} fill={C.yellow}>
								<T x={0} y={-40} size={38}>
									sportsbooks, 2025
								</T>
								<T x={0} y={35} size={80} font="marker" color={C.red}>
									$16.9 BILLION
								</T>
							</Card>
						</G>
					)}
					{after(152) && (
						<G x={1340} y={680} s={pop(153.3)}>
							<Card w={760} h={180} seed={16} fill={C.yellow}>
								<T x={0} y={-40} size={38}>
									online casino games, 2025
								</T>
								<T x={0} y={35} size={80} font="marker" color={C.red}>
									$10.7 BILLION
								</T>
							</Card>
						</G>
					)}
					{after(156) && (
						<T x={1340} y={890} size={50} font="marker" color={C.green} scale={pop(156.5)}>
							both up more than 20% in a year
						</T>
					)}
					{after(159.66) && (
						<G x={960} y={1060} s={0.45}>
							<Penny mood="worried" />
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 5. Engine 3: freebies (164.28 – 198.39)
const S5 = 164.28;
const Freebies: React.FC = () => {
	const {p, pop, after, t} = useCue(S5);
	const part = t < 188.48 ? 1 : 2;
	return (
		<Svg>
			<Title text="ENGINE #3: THE FREEBIES" at={164.28} S={S5} />
			{part === 1 && (
				<>
					<G x={960} y={1010} s={0.85}>
						<Penny mood={after(174.95) ? 'thinking' : 'happy'} />
					</G>
					<G x={interpolate(p(167.8, 0.8), [0, 1], [-200, 450])} y={600}>
						<Drink />
						<T x={0} y={60} size={40} font="marker">
							FREE
						</T>
					</G>
					{after(169.17) && (
						<G x={interpolate(p(169.2, 0.8), [0, 1], [2100, 1480])} y={560}>
							<KeyCard />
							<T x={0} y={120} size={40} font="marker">
								FREE
							</T>
						</G>
					)}
					{after(170.58) && (
						<G x={interpolate(p(170.6, 0.8), [0, 1], [2100, 1480])} y={830}>
							<Plate />
							<T x={0} y={90} size={40} font="marker">
								FREE
							</T>
						</G>
					)}
					{after(174.95) && (
						<G x={600} y={760} s={pop(175) * 0.8} r={-8}>
							<LoyaltyCard glow={after(177)} />
						</G>
					)}
					{after(177) && (
						<G x={960} y={250} s={pop(177.2)}>
							<Card w={760} h={120} seed={17}>
								<T x={0} y={6} size={44}>
									bets: {money(countUp(p(177.2, 3), 1389))}   time: {countUp(p(177.2, 3), 3)}h {countUp(p(177.2, 3), 12)}m
								</T>
							</Card>
						</G>
					)}
					{after(180.69) && (
						<G x={960} y={250 + 140} s={pop(182)}>
							<T x={0} y={0} size={48} font="marker" color={C.red}>
								expected loss  = slice back as gifts
							</T>
						</G>
					)}
				</>
			)}
			{part === 2 && (
				<>
					<G x={760} y={600} s={pop(188.5)}>
						<R s={{kind: 'rect', x: -300, y: -330, w: 600, h: 660}} o={{fill: C.white, fillStyle: 'solid'}} seed={18} />
						<T x={0} y={-260} size={52} font="marker">
							YOUR FREE ROOM
						</T>
						{[0, 1, 2].map((i) => (
							<R key={i} s={{kind: 'line', x1: -240, y1: -150 + i * 70, x2: 240 - i * 70, y2: -150 + i * 70}} o={{stroke: C.shadow, strokeWidth: 4}} seed={19 + i} boil={false} />
						))}
						<T x={0} y={140} size={40}>
							Paid for by:
						</T>
						<T x={0} y={230} size={90} font="marker" color={C.red} scale={pop(191.4)}>
							YOU
						</T>
					</G>
					{after(191.34) && (
						<G x={1450} y={460} s={pop(191.4)}>
							<Card w={620} h={130} seed={22} fill={C.yellow}>
								<T x={0} y={6} size={52} font="marker">
									a rebate on your losses
								</T>
							</Card>
						</G>
					)}
					{after(194) && (
						<G x={1450} y={1000} s={0.7}>
							<Penny mood="shocked" />
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 6. So-what (198.39 – 239.02)
const S6 = 198.39;
const Machine: React.FC = () => {
	const {p, pop, after, t} = useCue(S6);
	const rot = t * 50;
	if (t < 216.68) {
		const lit = (at: number) => (after(at) ? C.yellow : C.white);
		return (
			<Svg>
				<T x={960} y={100} size={74} font="marker" scale={pop(198.4)}>
					THE CASINO MACHINE
				</T>
				{[
					['EDGE', 200.42],
					['CHURN', 204.39],
					['FREEBIES', 207.4],
				].map(([l, at], i) => (
					<G key={l as string} x={460 + i * 500} y={430} s={pop(198.6 + i * 0.3)}>
						<Gear r={150} rot={after(at as number) ? (i % 2 ? -rot : rot) : 0} fill={lit(at as number)} seed={30 + i} />
						<T x={0} y={230} size={58} font="marker">
							{l as string}
						</T>
					</G>
				))}
				{after(211.04) && (
					<T x={960} y={870} size={60} font="marker" scale={pop(211.1)}>
						not &quot;lose big&quot;...
					</T>
				)}
				{after(214.18) && (
					<T x={960} y={970} size={72} font="marker" color={C.red} scale={pop(214.2)}>
						KEEP PLAYING
					</T>
				)}
			</Svg>
		);
	}
	const rules = [
		{text: 'Set a budget. Leave the cards at home.', at: 222.91},
		{text: 'When you win, walk away with it.', at: 228.43},
		{text: 'Skip keno and double-zero roulette.', at: 233.66},
	];
	return (
		<Svg>
			<G x={260} y={1000} s={0.85}>
				<Penny mood="confident" />
			</G>
			<G x={1100} y={190} s={pop(216.7)}>
				<Card w={1000} h={120} seed={23} fill={C.yellow}>
					<T x={0} y={6} size={50} font="marker">
						a ticket to a show, not a paycheck
					</T>
				</Card>
			</G>
			{rules.map((r, i) =>
				after(r.at - 1.2) ? (
					<G key={r.text} x={1100} y={420 + i * 190} s={pop(r.at - 1.2)}>
						<Card w={1000} h={150} seed={24 + i}>
							<T x={-440} y={4} size={64} font="marker" color={C.blue}>
								{i + 1}
							</T>
							<T x={30} y={4} size={44}>
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

// ---------------------------------------------------------------- 7. Payoff + bridge (239.02 – 254.97)
const S7 = 239.02;
const Payoff: React.FC = () => {
	const {pop, after, t} = useCue(S7);
	if (t < 245.42) {
		return (
			<Svg>
				<T x={960} y={200} size={90} font="marker" scale={pop(239.1)}>
					NOT LUCK.
				</T>
				{after(241.73) && (
					<T x={960} y={330} size={90} font="marker" color={C.red} scale={pop(241.8)}>
						MATH.
					</T>
				)}
				<G x={interpolate(t, [239.1, 244], [500, 1300], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})} y={1000}>
					<Penny walk={t < 244} mood="happy" look={1} />
				</G>
				<G x={1650} y={900} s={0.7}>
					<Chip seed={2} />
				</G>
			</Svg>
		);
	}
	const apps = [C.red, C.blue, C.green, C.gold, C.ink, C.red];
	return (
		<Svg>
			<G x={1250} y={560} s={pop(245.5)}>
				<Phone>
					{apps.map((col, i) => (
						<G key={i} x={-60 + (i % 2) * 120} y={-110 + Math.floor(i / 2) * 110}>
							<R s={{kind: 'rect', x: -42, y: -42, w: 84, h: 84}} o={{fill: col, fillStyle: 'solid'}} seed={40 + i} />
							{after(247 + i * 0.3) && (
								<G x={30} y={-36} s={pop(247 + i * 0.3)}>
									<R s={{kind: 'rect', x: -36, y: -16, w: 72, h: 32}} o={{fill: C.yellow, fillStyle: 'solid'}} seed={50 + i} />
									<T x={0} y={2} size={22} font="marker">
										FREE
									</T>
								</G>
							)}
						</G>
					))}
				</Phone>
			</G>
			<G x={600} y={1000}>
				<Penny mood="thinking" look={1} />
			</G>
			{after(250.73) && (
				<T x={1250} y={940} size={64} font="marker" color={C.red} scale={pop(250.8)}>
					NEXT: FREE APPS
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- End screen
const S8 = VO4_SECONDS;
const EndScreen: React.FC = () => {
	const {pop} = useCue(S8);
	return (
		<Svg>
			<T x={960} y={110} size={84} font="marker" scale={pop(S8)}>
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

const SFX: SfxCue[] = [
	[0.1, 'neon', 0.4],
	[1.0, 'pop', 0.45],
	[3.8, 'pop', 0.4],
	[7.1, 'whirr', 0.4],
	[8.5, 'coin', 0.35],
	[10.0, 'coin', 0.35],
	[11.5, 'coin', 0.35],
	[13.4, 'sting_dark', 0.45],
	[16.9, 'whoosh', 0.4],
	[18.2, 'chaching', 0.45],
	[21.09, 'sting', 0.6],
	[26.38, 'neon', 0.45],
	[27.5, 'pop', 0.4],
	[28.2, 'pop', 0.4],
	[28.9, 'pop', 0.4],
	[30.0, 'chaching', 0.5],
	[32.81, 'pop', 0.5],
	[38.2, 'pop', 0.45],
	[44.2, 'plink', 0.5],
	[46.5, 'chaching', 0.45],
	[50.1, 'pop', 0.4],
	[52.8, 'buzzer', 0.35],
	[55.7, 'whirr', 0.4],
	[60.4, 'sting_dark', 0.45],
	[69.11, 'pop', 0.4],
	[69.7, 'pop', 0.4],
	[70.3, 'pop', 0.4],
	[72.5, 'whoosh', 0.4],
	[78.8, 'whirr', 0.35],
	[83.0, 'whirr', 0.35],
	[91.8, 'stamp', 0.55],
	[93.68, 'pop', 0.5],
	[97.07, 'whirr', 0.4],
	[100.5, 'chaching', 0.5],
	[104.7, 'pop', 0.45],
	[111.5, 'coin', 0.45],
	[114.9, 'pop', 0.4],
	[118.9, 'whirr', 0.35],
	[122.0, 'coin', 0.3],
	[124.4, 'coin', 0.3],
	[126.8, 'coin', 0.3],
	[131.0, 'rise', 0.35],
	[137.5, 'sting_dark', 0.45],
	[140.5, 'scratch', 0.4],
	[144.3, 'whoosh', 0.4],
	[149.5, 'chaching', 0.45],
	[153.3, 'chaching', 0.45],
	[156.5, 'rise', 0.3],
	[164.28, 'pop', 0.5],
	[167.9, 'ding', 0.4],
	[169.3, 'ding', 0.4],
	[170.7, 'ding', 0.4],
	[175.0, 'beep', 0.45],
	[177.2, 'beep', 0.4],
	[182.0, 'pop', 0.45],
	[188.5, 'flip', 0.45],
	[191.4, 'stamp', 0.6],
	[198.4, 'pop', 0.5],
	[200.42, 'whirr', 0.35],
	[204.39, 'whirr', 0.35],
	[207.4, 'whirr', 0.35],
	[214.2, 'sting_dark', 0.45],
	[216.7, 'pop', 0.45],
	[221.7, 'pop', 0.45],
	[227.2, 'pop', 0.45],
	[232.5, 'pop', 0.45],
	[224.4, 'tick', 0.5],
	[229.9, 'tick', 0.5],
	[235.2, 'tick', 0.5],
	[239.1, 'slap', 0.45],
	[241.8, 'stamp', 0.5],
	[245.5, 'whoosh', 0.4],
	[247.0, 'plink', 0.35],
	[248.0, 'plink', 0.35],
	[250.8, 'sting_dark', 0.5],
	[VO4_SECONDS + 0.2, 'sting', 0.5],
];

const scenes: [number, number, React.FC][] = [
	[S1, S2, Hook],
	[S2, S3, Promise_],
	[S3, S4, Edge],
	[S4, S5, Churn],
	[S5, S6, Freebies],
	[S6, S7, Machine],
	[S7, S8, Payoff],
	[S8, EP04_SECONDS, EndScreen],
];

export const Ep04: React.FC = () => {
	const {fps} = useVideoConfig();
	return (
		<AbsoluteFill style={{background: C.paper}}>
			<Audio src={staticFile('ep04_vo.mp3')} />
			<Soundtrack music="music_lofi_ep04.mp3" sfx={SFX} voEnd={VO4_SECONDS} dips={[60.74, 188.48]} />
			{scenes.map(([a, b, Comp], i) => (
				<Sequence key={i} from={Math.round(a * fps)} durationInFrames={Math.round((b - a) * fps)}>
					<Comp />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
