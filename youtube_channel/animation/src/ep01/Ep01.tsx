import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {Broker, Guitar, Penny} from '../lib/characters';
import {Bubble, Car, Card, Cash, Coin, Cross, Gear, Jar, Paper, PawnShop, Phone, PriceTag, Tick} from '../lib/props';
import {C, G, R, T, countUp, useP} from '../lib/rough';

/**
 * Episode 1: How Pawn Shops ACTUALLY Make Money.
 * All cue times are GLOBAL seconds, taken from timing.json (voiceover sentence alignment).
 */
export const VO_SECONDS = 243.64;
export const END_SCREEN_SECONDS = 12;
export const EP01_SECONDS = VO_SECONDS + END_SCREEN_SECONDS;

const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
	<svg viewBox="0 0 1920 1080" width="100%" height="100%">
		<Paper />
		{children}
	</svg>
);

/** Wraps a scene so cue helpers can use global times. */
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

// ---------------------------------------------------------------- Scene 1: Hook
const S1 = 0;
const Hook: React.FC = () => {
	const {p, pop, after, t} = useCue(S1);
	const handoff = p(1.6, 1.2);
	const cashX = interpolate(handoff, [0, 1], [1230, 880]);
	const spin = countUp(p(5.9, 2), 500);
	return (
		<Svg>
			<PawnShop draw={p(0, 1.4)} />
			<G x={1430} y={760}>
				<Broker mood={after(4.1) ? 'grin' : 'smile'} draw={p(0.3, 1.2)} arm={handoff < 1 ? handoff : 1 - p(3.2, 0.5)} look={after(7.7) ? -1 : 0} />
			</G>
			<G x={780} y={960}>
				<Penny mood={after(3.2) ? 'happy' : 'neutral'} draw={p(0.5, 1.2)} holdGuitar={!after(1.6)} walk={t < 1.6} />
			</G>
			{after(1.6) && (
				<G x={cashX} y={600} r={-8}>
					<Cash />
				</G>
			)}
			<G x={300} y={430} s={pop(3.2)}>
				<Card w={460} h={150} fill={C.white} seed={1}>
					<T x={0} y={-36} size={34}>
						WHAT THEY PAID
					</T>
					<T x={0} y={26} size={78} font="marker" color={C.red}>
						$150
					</T>
				</Card>
			</G>
			<G x={300} y={630} s={pop(5.85)}>
				<Card w={460} h={150} fill={C.white} seed={2}>
					<T x={0} y={-36} size={34}>
						WHAT IT&apos;S WORTH
					</T>
					<T x={0} y={26} size={78} font="marker" color={C.green}>
						${spin}
					</T>
				</Card>
			</G>
			<G x={1600} y={380} s={pop(7.8)}>
				<T x={0} y={0} size={120} font="marker" color={C.red}>
					?!
				</T>
			</G>
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 2: Promise + title
const S2 = 11.3;
const Promise_: React.FC = () => {
	const {p, pop, t, after} = useCue(S2);
	const rot = t * 40;
	const feesGlow = after(21.9);
	const title = after(25.7);
	return (
		<Svg>
			{!title && (
				<>
					<T x={960} y={140} size={64} scale={pop(11.5)}>
						Buy low, sell high?
					</T>
					<G x={620} y={600}>
						<Gear r={170} teeth={12} rot={rot} fill={C.blue} seed={1} draw={p(11.6, 1)} label="LOANS" />
					</G>
					<G x={960} y={520} s={feesGlow ? 1 + 0.18 * pop(21.9) : 1}>
						<Gear r={150} teeth={11} rot={-rot * 1.1} fill={feesGlow ? C.red : C.shadow} seed={2} draw={p(12.2, 1)} label="FEES" />
					</G>
					<G x={1300} y={640} s={after(17.9) && !feesGlow ? 1.15 : 1}>
						<Gear r={170} teeth={12} rot={rot} fill={C.green} seed={3} draw={p(12.8, 1)} label="RESALE" />
					</G>
					{after(17.9) && !feesGlow && (
						<G x={1300} y={900}>
							<T x={0} y={0} size={48} color={C.green} scale={pop(17.9)}>
								part of it...
							</T>
						</G>
					)}
					{feesGlow && (
						<G x={960} y={250}>
							<T x={0} y={0} size={58} color={C.red} font="marker" scale={pop(22.2)}>
								THE REAL ENGINE
							</T>
							<R s={{kind: 'line', x1: 0, y1: 40, x2: 0, y2: 120}} o={{stroke: C.red, strokeWidth: 7}} draw={p(22.5, 0.4)} seed={2001} />
						</G>
					)}
				</>
			)}
			{title && (
				<>
					<G x={960} y={470} s={pop(25.7, 0.6)}>
						<G x={-420} y={0}>
							<Gear r={110} teeth={10} rot={rot * 2} fill={C.yellow} seed={4} />
						</G>
						<G x={420} y={0}>
							<Gear r={110} teeth={10} rot={-rot * 2} fill={C.yellow} seed={5} />
						</G>
						<T x={0} y={-40} size={130} font="marker" color={C.ink}>
							MONEY
						</T>
						<T x={0} y={90} size={130} font="marker" color={C.yellow} stroke={C.ink}>
							MECHANICS
						</T>
					</G>
					<T x={960} y={820} size={54} scale={pop(26.6)}>
						Ep. 1 · How pawn shops ACTUALLY make money
					</T>
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 3: Setup
const S3 = 29.7;
const Setup: React.FC = () => {
	const {p, pop, t, after} = useCue(S3);
	const atCounter = after(48.3);
	return (
		<Svg>
			{!atCounter && (
				<>
					{t < 31.6 && (
						<G x={960} y={540} s={pop(29.7)}>
							<T x={0} y={0} size={110} font="marker">
								{"<< REWIND A WEEK"}
							</T>
						</G>
					)}
					{after(31.6) && (
						<>
							<G x={520} y={820}>
								<Car draw={p(31.6, 0.8)} light />
							</G>
							{/* smoke puffs */}
							{[0, 1, 2].map((i) => (
								<G key={i} x={300 - i * 40} y={700 - ((t * 60 + i * 50) % 160)} o={0.6}>
									<R s={{kind: 'circle', x: 0, y: 0, d: 50 + i * 10}} o={{fill: C.shadow, fillStyle: 'solid', stroke: C.shadow}} seed={3000 + i} />
								</G>
							))}
							<G x={1000} y={300} s={pop(32.4)} r={-6}>
								<Card w={300} h={180} seed={3}>
									<T x={0} y={-45} size={36}>
										REPAIR BILL
									</T>
									<T x={0} y={30} size={84} font="marker" color={C.red}>
										${countUp(p(34.2, 0.6), 400)}
									</T>
								</Card>
							</G>
							<G x={1420} y={560} s={pop(35.5)}>
								<Phone>
									<T x={0} y={-150} size={34}>
										MY BANK
									</T>
									<T x={0} y={-60} size={30} color={C.shadow}>
										balance
									</T>
									<T x={0} y={10} size={70} font="marker" color={C.red} scale={pop(37.1)}>
										$62.18
									</T>
								</Phone>
							</G>
							{after(40.3) && (
								<>
									<G x={1000} y={620} s={pop(40.3)}>
										<Card w={260} h={90} seed={4}>
											<T x={0} y={4} size={38}>
												credit card
											</T>
										</Card>
										<Cross draw={p(40.6, 0.4)} seed={1} size={50} />
									</G>
									<G x={1000} y={760} s={pop(41.2)}>
										<Card w={260} h={90} seed={5}>
											<T x={0} y={4} size={38}>
												bank loan
											</T>
										</Card>
										<Cross draw={p(41.5, 0.4)} seed={2} size={50} />
									</G>
								</>
							)}
						</>
					)}
					{after(42.8) && (
						<>
							<rect x={0} y={0} width={1920} height={1080} fill={C.paper} opacity={p(42.8, 0.3)} />
							<G x={760} y={960}>
								<Penny mood="thinking" draw={p(42.9, 0.8)} look={1} />
							</G>
							<G x={1220} y={560} r={-12}>
								<Guitar draw={p(43.4, 0.8)} />
							</G>
							<G x={1000} y={330}>
								<Bubble w={200} h={110} draw={p(44.5, 0.4)}>
									<T x={0} y={4} size={70} font="marker">
										...
									</T>
								</Bubble>
							</G>
						</>
					)}
				</>
			)}
			{atCounter && (
				<>
					<PawnShop draw={1} />
					<G x={1430} y={760}>
						<Broker mood={after(56.2) ? 'smirk' : 'smile'} look={after(56.2) ? -1 : 0} />
					</G>
					<G x={300} y={960}>
						<Penny mood={after(54.8) ? 'confident' : 'neutral'} holdGuitar />
					</G>
					<G x={560} y={420} s={pop(51)} r={-4}>
						<Card w={300} h={130} seed={6}>
							<T x={0} y={6} size={64} font="marker" color={C.green}>
								SELL IT
							</T>
						</Card>
					</G>
					<G x={920} y={420} s={pop(51.8)} r={4}>
						<Card w={300} h={130} seed={7}>
							{!after(54.85) && (
								<T x={0} y={6} size={64} font="marker" color={C.blue}>
									PAWN IT
								</T>
							)}
						</Card>
					</G>
					{after(52.6) && (
						<T x={740} y={540} size={40} color={C.ink} scale={pop(52.6)}>
							(a short-term loan, with your stuff as collateral)
						</T>
					)}
					{after(54.85) && (
						<G x={920} y={420} s={interpolate(pop(54.85, 0.3), [0, 1], [2.4, 1])} r={-14}>
							<R s={{kind: 'rect', x: -170, y: -60, w: 340, h: 120}} o={{stroke: C.red, strokeWidth: 9}} seed={3100} />
							<T x={0} y={4} size={66} font="marker" color={C.red}>
								PAWNED!
							</T>
						</G>
					)}
					{after(56.2) && (
						<G x={1640} y={300}>
							<Bubble w={300} h={130} draw={p(56.4, 0.3)} tail="left">
								<T x={0} y={4} size={50} font="marker">
									...right?
								</T>
							</Bubble>
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 4a: Reveal 1, the lowball
const S4 = 58.45;
const Lowball: React.FC = () => {
	const {p, pop, after} = useCue(S4);
	const base = 860;
	const worthH = 560 * p(59.6, 1.2);
	const loanH = 168 * p(61.5, 1);
	const shopScene = after(72);
	return (
		<Svg>
			<T x={960} y={110} size={78} font="marker" scale={pop(58.45)}>
				TRICK #1: THE LOWBALL
			</T>
			{!shopScene && (
				<>
					<R s={{kind: 'line', x1: 520, y1: base, x2: 1400, y2: base}} o={{strokeWidth: 5}} draw={p(59, 0.6)} seed={4000} />
					{worthH > 2 && <R s={{kind: 'rect', x: 600, y: base - worthH, w: 220, h: worthH}} o={{fill: C.green, fillStyle: 'hachure'}} seed={4001} />}
					{loanH > 2 && <R s={{kind: 'rect', x: 1080, y: base - loanH, w: 220, h: loanH}} o={{fill: C.red, fillStyle: 'hachure'}} seed={4002} />}
					<T x={710} y={base + 50} size={44} scale={pop(60)}>
						resale value
					</T>
					<T x={1190} y={base + 50} size={44} scale={pop(61.5)}>
						your loan
					</T>
					<T x={710} y={base - worthH - 50} size={70} font="marker" color={C.green} scale={pop(60.5)}>
						$500
					</T>
					<T x={1190} y={base - loanH / 2} size={64} font="marker" color={C.white} stroke={C.red} scale={pop(62.3)}>
						$150
					</T>
					<T x={1640} y={520} size={60} font="marker" scale={pop(63.5)}>
						25–60%
					</T>
					<T x={1640} y={590} size={38} scale={pop(63.8)}>
						of resale value
					</T>
					{after(68.6) && (
						<>
							<R
								s={{kind: 'rect', x: 1080, y: base - 560, w: 220, h: 560 - 168}}
								o={{stroke: C.ink, strokeWidth: 3, strokeLineDash: [14, 10], fill: C.yellow, fillStyle: 'zigzag', hachureGap: 14}}
								draw={p(68.6, 0.8)}
								seed={4003}
							/>
							<T x={1190} y={base - 380} size={44} font="marker" scale={pop(69.2)}>
								SAFETY
							</T>
							<T x={1190} y={base - 330} size={44} font="marker" scale={pop(69.4)}>
								CUSHION
							</T>
						</>
					)}
					{after(70.4) && (
						<G x={300} y={480} s={pop(70.4)}>
							<R s={{kind: 'path', d: 'M 0 -110 L 90 -70 C 90 30 50 90 0 120 C -50 90 -90 30 -90 -70 Z'}} o={{fill: C.blue, fillStyle: 'hachure'}} seed={4004} />
							<T x={0} y={170} size={46} font="marker">
								INSURANCE
							</T>
						</G>
					)}
				</>
			)}
			{shopScene && (
				<>
					<PawnShop draw={1} />
					<G x={1430} y={760}>
						<Broker mood="grin" />
					</G>
					<G x={1500} y={420} r={-20} s={pop(72.2)}>
						<Guitar />
					</G>
					<G x={1560} y={480} s={pop(73)}>
						<PriceTag text="$450" seed={1} />
					</G>
					<G x={480} y={540} s={pop(74.2)}>
						<Card w={520} h={200} seed={8}>
							<T x={0} y={-50} size={40}>
								never comes back?
							</T>
							<T x={0} y={30} size={60} font="marker" color={C.green}>
								+$300 PROFIT
							</T>
						</Card>
					</G>
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 4b: Re-hook
const S5 = 77.0;
const ReHook: React.FC = () => {
	const {p, pop, t} = useCue(S5);
	const walkX = interpolate(t, [77, 81], [700, 300]);
	return (
		<Svg>
			<PawnShop draw={1} />
			<G x={1430} y={760}>
				<Broker mood="smile" arm={Math.abs(Math.sin(t * 4)) * 0.4} />
			</G>
			<G x={walkX} y={960}>
				<Penny walk mood="happy" />
			</G>
			<G x={1350} y={300}>
				<Bubble w={440} h={150} draw={p(77.3, 0.3)} tail="left">
					<T x={0} y={4} size={46} font="marker">
						Come back soon!
					</T>
				</Bubble>
			</G>
			<T x={760} y={560} size={96} font="marker" color={C.red} scale={pop(79.8)}>
				Here&apos;s why.
			</T>
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 4c: Reveal 2, fee engine
const S6 = 81.0;
const FeeEngine: React.FC = () => {
	const {p, pop, after, t} = useCue(S6);
	const part = t < 97 ? 1 : t < 127.1 ? 2 : 3;
	// coin drops at each "fee paid" beat
	const feeBeats = [112.6, 115.7, 117.1, 118.6];
	const paid = feeBeats.filter((b, i) => i > 0 && t >= b + 0.4).length;
	const level = paid / 4;
	return (
		<Svg>
			<T x={960} y={110} size={78} font="marker" scale={pop(81)}>
				TRICK #2: THE FEE ENGINE
			</T>
			{part === 1 && (
				<>
					<G x={560} y={420} s={pop(81.4)}>
						<Card w={460} h={150} seed={9}>
							<T x={0} y={4} size={64} font="marker" color={C.shadow}>
								INTEREST
							</T>
						</Card>
						<Cross draw={p(82.4, 0.5)} seed={3} size={70} />
					</G>
					<G x={1360} y={420} s={pop(84.6)}>
						<Card w={520} h={150} seed={10} fill={C.yellow}>
							<T x={0} y={4} size={60} font="marker">
								MONTHLY FEES
							</T>
						</Card>
					</G>
					{/* fee gauge 2% -> 25% */}
					<G x={960} y={760} o={p(87, 0.5)}>
						<R s={{kind: 'rect', x: -600, y: -40, w: 1200, h: 80}} o={{fill: C.white, fillStyle: 'solid'}} seed={6000} />
						{p(89, 4) > 0 && (
							<R s={{kind: 'rect', x: -600, y: -40, w: 1200 * p(89, 4), h: 80}} o={{fill: C.red, fillStyle: 'hachure', stroke: 'none'}} seed={6001} />
						)}
						<T x={-600} y={-90} size={50} font="marker" color={C.green} anchor="start">
							2%
						</T>
						<T x={600} y={-90} size={50} font="marker" color={C.red} anchor="end" scale={p(91, 0.4)}>
							25%
						</T>
						<T x={0} y={110} size={60} font="marker" scale={pop(93.5)}>
							...EVERY. SINGLE. MONTH.
						</T>
					</G>
				</>
			)}
			{part === 2 && (
				<>
					{/* calendar */}
					<G x={420} y={560}>
						<Card w={360} h={380} seed={11}>
							<R s={{kind: 'rect', x: -180, y: -190, w: 360, h: 80}} o={{fill: C.red, fillStyle: 'solid'}} seed={6002} />
							<T x={0} y={-150} size={46} font="marker" color={C.white}>
								MONTH
							</T>
							<T x={0} y={40} size={180} font="marker">
								{after(118.6) ? 3 : after(117.1) ? 2 : 1}
							</T>
						</Card>
					</G>
					<G x={420} y={860} s={pop(100.2)}>
						<T x={0} y={0} size={46}>
							20% a month
						</T>
					</G>
					{/* loan card */}
					<G x={960} y={330} s={pop(97)}>
						<Card w={360} h={140} seed={12}>
							<T x={0} y={-30} size={36}>
								Penny borrowed
							</T>
							<T x={0} y={28} size={64} font="marker" color={C.green}>
								$150
							</T>
						</Card>
					</G>
					<G x={960} y={520} s={pop(101.6)}>
						<T x={0} y={0} size={64} font="marker" color={C.red}>
							= $30 / month
						</T>
					</G>
					{after(104.7) && t < 110.6 && (
						<G x={960} y={680} s={pop(104.7)}>
							<T x={0} y={0} size={50}>
								owes after month 1:
							</T>
							<T x={0} y={70} size={84} font="marker" color={C.red}>
								$180
							</T>
						</G>
					)}
					{/* jar */}
					<G x={1500} y={960}>
						<Jar level={level} draw={p(98, 0.8)} />
					</G>
					{feeBeats.slice(1).map((b, i) =>
						after(b) && t < b + 0.5 ? (
							<G key={i} x={1500} y={interpolate(t, [b, b + 0.45], [380, 820])}>
								<Coin seed={i} />
							</G>
						) : null,
					)}
					{after(110.6) && t < 121.9 && (
						<G x={960} y={720}>
							<Bubble w={560} h={170} draw={p(110.7, 0.3)} tail="right">
								<T x={0} y={-18} size={40} font="marker">
									Just pay the $30 fee,
								</T>
								<T x={0} y={30} size={40} font="marker">
									we&apos;ll extend it!
								</T>
							</Bubble>
						</G>
					)}
					{after(121.9) && (
						<G x={960} y={760} s={pop(121.9)}>
							<Card w={560} h={220} seed={13}>
								<T x={0} y={-50} size={56} font="marker" color={C.red}>
									PAID: $90
								</T>
								<T x={0} y={40} size={56} font="marker">
									STILL OWES: $150
								</T>
							</Card>
						</G>
					)}
				</>
			)}
			{part === 3 && (
				<>
					<G x={560} y={960}>
						<Penny mood="shocked" draw={p(127.1, 0.5)} />
					</G>
					<G x={1200} y={540}>
						{/* badge flips: scaleX goes 1 -> 0 -> 1 */}
						<G s={1}>
							<g transform={`scale(${Math.abs(Math.cos(p(128.6, 0.8) * Math.PI))} 1)`}>
								<R s={{kind: 'circle', x: 0, y: 0, d: 440}} o={{fill: p(128.6, 0.8) > 0.5 ? C.red : C.yellow, fillStyle: 'solid'}} seed={6100} />
								{p(128.6, 0.8) <= 0.5 ? (
									<>
										<T x={0} y={-30} size={100} font="marker">
											10%
										</T>
										<T x={0} y={60} size={50} font="marker">
											a month
										</T>
									</>
								) : (
									<>
										<T x={0} y={-30} size={120} font="marker" color={C.white}>
											120%
										</T>
										<T x={0} y={65} size={52} font="marker" color={C.white}>
											a year
										</T>
									</>
								)}
							</g>
						</G>
					</G>
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 4d: Reveal 3, house always wins
const S7 = 132.57;
const HouseWins: React.FC = () => {
	const {p, pop, after, t} = useCue(S7);
	const part = t < 143.1 ? 1 : t < 150.2 ? 2 : t < 169.4 ? 3 : 4;
	const pieP = p(143.6, 1.4);
	const arc = (frac: number) => Math.PI * 2 * frac;
	return (
		<Svg>
			<T x={960} y={110} size={78} font="marker" scale={pop(132.57)}>
				TRICK #3: HEADS OR TAILS, THEY WIN
			</T>
			{part === 1 && (
				<>
					<R s={{kind: 'line', x1: 960, y1: 200, x2: 960, y2: 1000}} o={{strokeWidth: 5}} draw={p(133, 0.5)} seed={7000} />
					<T x={480} y={240} size={52} font="marker" color={C.green} scale={pop(134.2)}>
						PAYS IT BACK
					</T>
					<T x={1440} y={240} size={52} font="marker" color={C.red} scale={pop(137.7)}>
						DOESN&apos;T
					</T>
					{after(134.2) && (
						<>
							<G x={480} y={640} s={pop(134.5)}>
								<Card w={360} h={240} seed={14} fill={C.shadow}>
									<T x={0} y={-60} size={44} font="marker">
										REGISTER
									</T>
								</Card>
							</G>
							<G x={480} y={interpolate(p(135.4, 0.8), [0, 1], [380, 640])} s={0.8}>
								<Cash thick />
							</G>
							<T x={480} y={880} size={48} scale={pop(136)}>
								shop keeps the fees
							</T>
						</>
					)}
					{after(137.7) && (
						<>
							<G x={1440} y={600} r={-15} s={pop(138)}>
								<Guitar />
							</G>
							<G x={1500} y={660} s={pop(139.4)}>
								<PriceTag text="$450" seed={2} />
							</G>
							<T x={1440} y={880} size={48} scale={pop(140)}>
								shop keeps the guitar
							</T>
						</>
					)}
				</>
			)}
			{part === 2 && (
				<>
					<G x={760} y={580}>
						<R s={{kind: 'circle', x: 0, y: 0, d: 520}} o={{fill: C.white, fillStyle: 'solid'}} seed={7100} />
						{pieP > 0 && (
							<R s={{kind: 'arc', x: 0, y: 0, w: 520, h: 520, start: -Math.PI / 2, stop: -Math.PI / 2 + arc(0.655 * pieP), closed: true}} o={{fill: C.green, fillStyle: 'hachure'}} seed={7101} />
						)}
						{pieP >= 1 && (
							<R s={{kind: 'arc', x: 0, y: 0, w: 520, h: 520, start: -Math.PI / 2 + arc(0.655), stop: Math.PI * 1.5, closed: true}} o={{fill: C.red, fillStyle: 'hachure'}} seed={7102} />
						)}
					</G>
					<G x={1420} y={460} s={pop(144.5)}>
						<T x={0} y={0} size={64} font="marker" color={C.green}>
							~2 in 3 REDEEMED
						</T>
					</G>
					<G x={1420} y={600} s={pop(146.5)}>
						<T x={0} y={0} size={64} font="marker" color={C.red}>
							~1 in 3 FOR SALE
						</T>
					</G>
					<T x={1420} y={760} size={40} color={C.ink} scale={pop(143.5)}>
						Oregon pawn data, 2024
					</T>
				</>
			)}
			{part === 3 && (
				<>
					{/* laptop with sold listings */}
					<G x={560} y={600} s={pop(154.98)}>
						<R s={{kind: 'rect', x: -300, y: -220, w: 600, h: 380}} o={{fill: C.ink, fillStyle: 'solid'}} seed={7200} />
						<R s={{kind: 'rect', x: -275, y: -195, w: 550, h: 330}} o={{fill: C.white, fillStyle: 'solid'}} seed={7201} />
						<R s={{kind: 'polygon', pts: [[-360, 160], [360, 160], [400, 210], [-400, 210]]}} o={{fill: C.shadow, fillStyle: 'solid'}} seed={7202} />
						<T x={0} y={-150} size={40} font="marker">
							SOLD LISTINGS
						</T>
						{['Guitar ...... $480', 'Guitar ...... $455', 'Guitar ...... $510'].map((l, i) => (
							<T key={l} x={0} y={-80 + i * 65} size={40} scale={pop(156 + i * 0.5)}>
								{l}
							</T>
						))}
					</G>
					{after(159) && (
						<>
							<G x={1380} y={760}>
								<R s={{kind: 'rect', x: -200, y: -40, w: 400, h: 120}} o={{fill: C.shadow, fillStyle: 'solid'}} draw={p(159, 0.5)} seed={7300} />
								<R s={{kind: 'rect', x: -160, y: -60, w: 320, h: 30}} o={{fill: C.ink, fillStyle: 'solid'}} draw={p(159.2, 0.5)} seed={7301} />
								<R s={{kind: 'rect', x: -90, y: 0, w: 180, h: 60}} o={{fill: '#9BE7B4', fillStyle: 'solid'}} draw={p(159.4, 0.5)} seed={7302} />
								<T x={0} y={32} size={46} font="marker" scale={pop(161.8)}>
									6.2 g
								</T>
							</G>
							<G x={1380} y={interpolate(p(161.7, 0.4), [0, 1], [420, 670])}>
								<R s={{kind: 'circle', x: 0, y: 0, d: 90}} o={{stroke: C.gold, strokeWidth: 16}} seed={7303} />
								<R s={{kind: 'polygon', pts: [[-20, -50], [20, -50], [0, -80]]}} o={{fill: C.blue, fillStyle: 'solid'}} seed={7304} />
							</G>
							<G x={1500} y={480} s={pop(163.4)}>
								<PriceTag text="$$$" seed={3} fill={C.green} />
							</G>
							<T x={1380} y={980} size={42} scale={pop(164)}>
								gold has a price per gram
							</T>
						</>
					)}
				</>
			)}
			{part === 4 && (
				<G x={960} y={560} o={(t * 30) % 23 < 2 ? 0.4 : 1}>
					<R s={{kind: 'rect', x: -620, y: -150, w: 1240, h: 300}} o={{stroke: C.green, strokeWidth: 8}} draw={p(169.4, 0.5)} seed={7400} />
					<T x={0} y={8} size={128} font="marker" color={C.green} scale={pop(169.6)}>
						THE HOUSE WINS
					</T>
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 5a: Scale + what they sell
const S8 = 171.87;
const BigPicture: React.FC = () => {
	const {p, pop, after, t} = useCue(S8);
	const sells = after(185.5);
	// deterministic pseudo-random dots
	const dots = Array.from({length: 90}).map((_, i) => ({
		x: 260 + ((i * 337) % 1000),
		y: 330 + ((i * 211) % 520),
		at: 172 + (i / 90) * 3,
	}));
	return (
		<Svg>
			{!sells && (
				<>
					{/* rough US-ish blob */}
					<R
						s={{kind: 'path', d: 'M 220 360 C 400 280 900 260 1250 330 C 1300 420 1260 520 1180 600 C 1100 700 1050 860 980 880 C 800 820 600 860 420 820 C 300 760 200 560 220 360 Z'}}
						o={{fill: '#E6DFD0', fillStyle: 'solid'}}
						draw={p(172, 1)}
						seed={8000}
					/>
					{dots.map((d, i) =>
						after(d.at) ? <R key={i} s={{kind: 'circle', x: d.x, y: d.y, d: 18}} o={{fill: C.red, fillStyle: 'solid', stroke: 'none'}} seed={8100 + i} boil={false} /> : null,
					)}
					{after(174.5) && (
						<G x={1560} y={940}>
							<R s={{kind: 'rect', x: -150, y: -620 * p(174.5, 1.2), w: 300, h: 620 * p(174.5, 1.2)}} o={{fill: C.blue, fillStyle: 'hachure'}} seed={8200} />
							{p(174.5, 1.2) >= 1 &&
								Array.from({length: 12}).map((_, i) => (
									<R key={i} s={{kind: 'rect', x: -110 + (i % 3) * 80, y: -560 + Math.floor(i / 3) * 120, w: 50, h: 70}} o={{fill: C.yellow, fillStyle: 'solid'}} seed={8210 + i} />
								))}
							<T x={0} y={-680} size={60} font="marker" scale={pop(176)}>
								FirstCash
							</T>
						</G>
					)}
					<G x={720} y={180} s={pop(179)}>
						<T x={0} y={0} size={84} font="marker" color={C.red}>
							3,300+ STORES
						</T>
					</G>
					<G x={720} y={980} s={pop(181.5)}>
						<T x={0} y={0} size={46}>
							(publicly traded)
						</T>
					</G>
				</>
			)}
			{sells && (
				<>
					<PawnShop draw={1} neon="YES!" neonColor={C.green} />
					<G x={1430} y={760}>
						<Broker mood="grin" />
					</G>
					{['10 minutes', 'no paperwork', 'no awkward questions'].map((l, i) => (
						<G key={l} x={180} y={460 + i * 110} s={pop(190.3 + i * 0.8)}>
							<Tick seed={10 + i} />
							<T x={50} y={0} size={60} font="marker" color={C.green} anchor="start">
								{l}
							</T>
						</G>
					))}
					{after(193.5) && (
						<G x={460} y={860} s={pop(193.5)}>
							<Card w={560} h={130} seed={15} fill={C.yellow}>
								<T x={0} y={4} size={58} font="marker">
									CONVENIENCE
								</T>
							</Card>
							<G x={200} y={-90} s={pop(195.9)} r={12}>
								<PriceTag text="$$$" seed={4} fill={C.red} />
							</G>
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 5b: Advice
const S9 = 198.36;
const Advice: React.FC = () => {
	const {p, pop, after} = useCue(S9);
	const list = after(207.5);
	const rules = [
		{at: 210.0, text: 'Know the MONTHLY fee'},
		{at: 212.9, text: 'Borrow as little as you can'},
		{at: 216.5, text: 'Pay it off in month one'},
	];
	return (
		<Svg>
			<G x={380} y={960}>
				<Penny mood={list ? 'confident' : 'thinking'} />
			</G>
			<T x={1100} y={150} size={76} font="marker" scale={pop(198.4)}>
				Is pawning always bad?
			</T>
			{!list && (
				<>
					<T x={1100} y={300} size={60} color={C.green} font="marker" scale={pop(200.85)}>
						Not necessarily.
					</T>
					<G x={1100} y={500} s={pop(202.6)}>
						<Card w={720} h={120} seed={16}>
							<G x={-300} y={0}>
								<Tick draw={p(203, 0.4)} seed={1} />
							</G>
							<T x={30} y={4} size={50}>
								no credit check
							</T>
						</Card>
					</G>
					<G x={1100} y={680} s={pop(204.8)}>
						<Card w={720} h={120} seed={17}>
							<G x={-300} y={0}>
								<Tick draw={p(205.2, 0.4)} seed={2} />
							</G>
							<T x={30} y={4} size={50}>
								credit score untouched
							</T>
						</Card>
					</G>
				</>
			)}
			{list && (
				<>
					<G x={1100} y={330} s={pop(207.5)}>
						<T x={0} y={0} size={56} font="marker" color={C.red}>
							IF YOU EVER DO IT:
						</T>
					</G>
					{rules.map((r, i) => (
						<G key={r.text} x={1100} y={480 + i * 160} s={pop(r.at)}>
							<Card w={820} h={130} seed={18 + i}>
								<T x={-340} y={4} size={64} font="marker" color={C.blue}>
									{i + 1}
								</T>
								<T x={30} y={4} size={50}>
									{r.text}
								</T>
								<G x={360} y={0}>
									<Tick draw={p(r.at + 1.2, 0.4)} seed={3 + i} />
								</G>
							</Card>
						</G>
					))}
					{after(219.6) && (
						<G x={1780} y={1000} s={0.45}>
							<Jar level={0.5} />
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- Scene 6: Payoff + bridge
const S10 = 222.79;
const Payoff: React.FC = () => {
	const {p, pop, after, t} = useCue(S10);
	const exit = after(234.5);
	return (
		<Svg>
			{!exit && (
				<>
					<G x={960} y={300} s={pop(222.8)}>
						<T x={0} y={0} size={84} font="marker" color={C.shadow}>
							BUYING &amp; SELLING
						</T>
						<R s={{kind: 'line', x1: -420, y1: 10, x2: 420, y2: -10}} o={{stroke: C.red, strokeWidth: 12}} draw={p(224.5, 0.4)} seed={9000} />
					</G>
					<G x={960} y={640} s={pop(226.2)}>
						<R s={{kind: 'circle', x: 0, y: 0, d: 300}} o={{fill: C.white, fillStyle: 'solid'}} seed={9001} />
						<R s={{kind: 'line', x1: 0, y1: 0, x2: 0, y2: -110}} o={{strokeWidth: 8}} seed={9002} />
						<g transform={`rotate(${t * 220})`}>
							<R s={{kind: 'line', x1: 0, y1: 0, x2: 0, y2: -130}} o={{strokeWidth: 5, stroke: C.red}} seed={9003} />
						</g>
						<T x={0} y={220} size={84} font="marker" color={C.red}>
							TIME
						</T>
					</G>
					{after(229.6) &&
						[0, 1, 2, 3].map((i) => {
							const a = (t * 1.5 + i * 1.57) % (Math.PI * 2);
							return (
								<G key={i} x={960 + Math.cos(a) * 260} y={640 + Math.sin(a) * 260} s={pop(229.6 + i * 0.3)}>
									<Coin seed={i + 5} />
								</G>
							);
						})}
				</>
			)}
			{exit && (
				<>
					<G x={interpolate(t, [234.5, 238], [200, 560])} y={960}>
						<Penny walk={t < 238} holdGuitar mood="happy" />
					</G>
					{after(237.5) && (
						<G x={1300} y={420} r={-8} s={pop(237.5)}>
							<R s={{kind: 'rect', x: -230, y: -140, w: 460, h: 280}} o={{fill: C.blue, fillStyle: 'cross-hatch', stroke: C.red, strokeWidth: 3.5 + Math.abs(Math.sin(t * 5)) * 5}} seed={9100} />
							<R s={{kind: 'rect', x: -170, y: -70, w: 80, h: 60}} o={{fill: C.gold, fillStyle: 'solid'}} seed={9101} />
							<T x={0} y={80} size={46} font="marker" color={C.white}>
								**** **** ****
							</T>
						</G>
					)}
					{after(241.7) && (
						<G x={1300} y={820} s={pop(241.7)}>
							<T x={0} y={0} size={64} font="marker" color={C.red}>
								NEXT: CREDIT CARDS
							</T>
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- End screen
const S11 = VO_SECONDS;
const EndScreen: React.FC = () => {
	const {pop} = useCue(S11);
	return (
		<Svg>
			<T x={960} y={110} size={84} font="marker" scale={pop(VO_SECONDS)}>
				MONEY <tspan fill={C.yellow} stroke={C.ink} strokeWidth={8} paintOrder="stroke">MECHANICS</tspan>
			</T>
			{/* Placeholders where YouTube's end-screen elements go */}
			<R s={{kind: 'rect', x: 1010, y: 260, w: 760, h: 428}} o={{strokeLineDash: [18, 12], stroke: C.shadow, strokeWidth: 4}} seed={9500} boil={false} />
			<T x={1390} y={474} size={44} color={C.shadow}>
				(watch next)
			</T>
			<R s={{kind: 'circle', x: 520, y: 520, d: 300}} o={{strokeLineDash: [18, 12], stroke: C.shadow, strokeWidth: 4}} seed={9501} boil={false} />
			<T x={520} y={720} size={44} color={C.shadow}>
				(subscribe)
			</T>
			<G x={250} y={1000} s={0.75}>
				<Penny wave mood="happy" />
			</G>
		</Svg>
	);
};


// ---------------------------------------------------------------- Sound design
// All SFX and music are synthesised by scripts/synth_audio.py (original, no licences).
const SFX: [number, string, number][] = [
	// [global seconds, file, volume]
	[1.6, 'whoosh', 0.5],
	[3.2, 'chaching', 0.6],
	[5.9, 'rise', 0.35],
	[7.7, 'scratch', 0.5],
	[11.6, 'whirr', 0.5],
	[12.2, 'whirr', 0.4],
	[21.9, 'pop', 0.6],
	[25.7, 'sting', 0.6],
	[29.7, 'rewind', 0.5],
	[31.6, 'sputter', 0.5],
	[32.4, 'slap', 0.6],
	[35.5, 'pop', 0.5],
	[37.1, 'bloop', 0.5],
	[40.6, 'buzzer', 0.35],
	[41.5, 'buzzer', 0.35],
	[44.5, 'pop', 0.4],
	[51.0, 'whoosh', 0.45],
	[51.8, 'whoosh', 0.45],
	[54.85, 'stamp', 0.7],
	[58.45, 'pop', 0.5],
	[59.6, 'rise', 0.35],
	[68.6, 'pop', 0.45],
	[70.4, 'pop', 0.45],
	[73.0, 'chaching', 0.5],
	[79.8, 'sting_dark', 0.5],
	[81.0, 'pop', 0.5],
	[82.4, 'buzzer', 0.3],
	[89.0, 'rise', 0.3],
	[97.0, 'pop', 0.45],
	[101.6, 'coin', 0.45],
	[110.7, 'pop', 0.4],
	[116.1, 'coin', 0.55],
	[117.5, 'coin', 0.55],
	[119.0, 'coin', 0.55],
	[121.9, 'bloop', 0.5],
	[127.1, 'gasp', 0.5],
	[128.6, 'flip', 0.6],
	[129.0, 'sting_dark', 0.45],
	[132.57, 'pop', 0.5],
	[135.4, 'chaching', 0.55],
	[139.4, 'chaching', 0.55],
	[143.6, 'rise', 0.3],
	[156.0, 'tick', 0.4],
	[156.5, 'tick', 0.4],
	[157.0, 'tick', 0.4],
	[161.8, 'beep', 0.5],
	[163.4, 'chaching', 0.45],
	[169.4, 'neon', 0.6],
	[172.0, 'plink', 0.4],
	[173.0, 'plink', 0.4],
	[174.0, 'plink', 0.4],
	[174.5, 'rise', 0.3],
	[190.3, 'ding', 0.4],
	[191.1, 'ding', 0.4],
	[191.9, 'ding', 0.4],
	[195.9, 'chaching', 0.4],
	[203.0, 'tick', 0.5],
	[205.2, 'tick', 0.5],
	[211.2, 'tick', 0.5],
	[214.1, 'tick', 0.5],
	[217.7, 'tick', 0.5],
	[219.6, 'coin', 0.5],
	[224.5, 'whoosh', 0.45],
	[226.2, 'clock', 0.45],
	[229.6, 'coin', 0.4],
	[237.5, 'hum', 0.5],
	[241.7, 'sting_dark', 0.5],
	[VO_SECONDS + 0.2, 'sting', 0.5],
];

const MUSIC_BED = 0.14;
const musicVolume = (sec: number) => {
	// Drop out for the beat before "Either way, the house wins", swell on the end screen.
	if (sec > 168.4 && sec < 169.4) return interpolate(sec, [168.4, 168.7, 169.1, 169.4], [MUSIC_BED, 0, 0, MUSIC_BED]);
	if (sec > VO_SECONDS - 0.5) return interpolate(sec, [VO_SECONDS - 0.5, VO_SECONDS + 1], [MUSIC_BED, 0.4], {extrapolateRight: 'clamp'});
	return MUSIC_BED;
};

const Soundtrack: React.FC = () => {
	const {fps} = useVideoConfig();
	return (
		<>
			<Audio src={staticFile('sfx/music_lofi.mp3')} volume={(f) => musicVolume(f / fps)} />
			{SFX.map(([at, file, vol], i) => (
				<Sequence key={i} from={Math.round(at * fps)} durationInFrames={Math.round(3.5 * fps)}>
					<Audio src={staticFile(`sfx/${file}.wav`)} volume={vol} />
				</Sequence>
			))}
		</>
	);
};

const scenes: [number, number, React.FC][] = [
	[S1, S2, Hook],
	[S2, S3, Promise_],
	[S3, S4, Setup],
	[S4, S5, Lowball],
	[S5, S6, ReHook],
	[S6, S7, FeeEngine],
	[S7, S8, HouseWins],
	[S8, S9, BigPicture],
	[S9, S10, Advice],
	[S10, S11, Payoff],
	[S11, EP01_SECONDS, EndScreen],
];

export const Ep01: React.FC = () => {
	const {fps} = useVideoConfig();
	return (
		<AbsoluteFill style={{background: C.paper}}>
			<Audio src={staticFile('ep01_vo.mp3')} />
			<Soundtrack />
			{scenes.map(([a, b, Comp], i) => (
				<Sequence key={i} from={Math.round(a * fps)} durationInFrames={Math.round((b - a) * fps)}>
					<Comp />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
