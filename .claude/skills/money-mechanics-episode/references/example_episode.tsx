import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Penny} from '../lib/characters';
import {Card, Cash, Coin, Gear, Paper, PawnShop, PriceTag, Tick} from '../lib/props';
import {C, G, R, T, countUp, useP} from '../lib/rough';
import {SfxCue, Soundtrack} from '../lib/sound';

/**
 * Episode 3 (uploads 2nd): How Credit Card Companies Make Money Off You.
 * Cue times are GLOBAL seconds from timing_ep03.json (exact Kokoro timings).
 */
export const VO3_SECONDS = 253.01;
export const EP03_SECONDS = VO3_SECONDS + 12;

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

// ---------------------------------------------------------------- Episode props
export const CreditCard: React.FC<{draw?: number; glow?: boolean}> = ({draw = 1, glow = false}) => {
	const frame = useCurrentFrame();
	return (
		<g>
			<R
				s={{kind: 'rect', x: -170, y: -105, w: 340, h: 210}}
				o={{fill: C.blue, fillStyle: 'cross-hatch', stroke: glow ? C.red : C.ink, strokeWidth: glow ? 4 + Math.abs(Math.sin(frame / 5)) * 5 : 3.5}}
				draw={draw}
				seed={2000}
			/>
			<R s={{kind: 'rect', x: -130, y: -55, w: 70, h: 52}} o={{fill: C.gold, fillStyle: 'solid'}} draw={draw} seed={2001} />
			<T x={0} y={55} size={34} font="marker" color={C.white} scale={Math.min(1, draw)}>
				**** 1234
			</T>
		</g>
	);
};

const Statement: React.FC<{draw?: number; minGlow?: boolean}> = ({draw = 1, minGlow = false}) => {
	const frame = useCurrentFrame();
	return (
		<g>
			<R s={{kind: 'rect', x: -260, y: -330, w: 520, h: 660}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={2010} />
			<T x={0} y={-270} size={40} font="marker" scale={Math.min(1, draw)}>
				STATEMENT
			</T>
			<T x={-220} y={-170} size={34} anchor="start" scale={Math.min(1, draw)}>
				Balance
			</T>
			<T x={220} y={-170} size={52} font="marker" anchor="end" color={C.red} scale={Math.min(1, draw)}>
				$5,000.00
			</T>
			<T x={-220} y={-90} size={30} anchor="start" color={C.shadow} scale={Math.min(1, draw)}>
				APR 22%
			</T>
			{[0, 1, 2].map((i) => (
				<R key={i} s={{kind: 'line', x1: -220, y1: -20 + i * 50, x2: 220 - i * 60, y2: -20 + i * 50}} o={{stroke: C.shadow, strokeWidth: 4}} draw={draw} seed={2011 + i} boil={false} />
			))}
			<R
				s={{kind: 'rect', x: -220, y: 170, w: 440, h: 110}}
				o={{fill: minGlow ? C.yellow : '#FFF6D6', fillStyle: 'solid', stroke: minGlow ? C.red : C.ink, strokeWidth: minGlow ? 4 + Math.abs(Math.sin(frame / 6)) * 4 : 3}}
				draw={draw}
				seed={2015}
			/>
			<T x={0} y={200} size={28} scale={Math.min(1, draw)}>
				MINIMUM DUE
			</T>
			<T x={0} y={250} size={50} font="marker" scale={Math.min(1, draw)}>
				$141.67
			</T>
		</g>
	);
};

const Bank: React.FC<{draw?: number}> = ({draw = 1}) => (
	<g>
		<R s={{kind: 'polygon', pts: [[-220, -160], [0, -280], [220, -160]]}} o={{fill: C.shadow, fillStyle: 'hachure'}} draw={draw} seed={2020} />
		{[-160, -80, 0, 80, 160].map((x, i) => (
			<R key={x} s={{kind: 'rect', x: x - 18, y: -150, w: 36, h: 220}} o={{fill: C.white, fillStyle: 'solid'}} draw={draw} seed={2021 + i} />
		))}
		<R s={{kind: 'rect', x: -240, y: 70, w: 480, h: 40}} o={{fill: C.shadow, fillStyle: 'solid'}} draw={draw} seed={2030} />
		<T x={0} y={-190} size={44} font="marker" scale={Math.min(1, draw)}>
			$
		</T>
	</g>
);

const Padlock: React.FC<{open?: number; draw?: number}> = ({open = 0, draw = 1}) => (
	<g>
		<g transform={`translate(${open * 60} ${-open * 50}) rotate(${-open * 25})`}>
			<R s={{kind: 'arc', x: 0, y: -60, w: 140, h: 160, start: Math.PI, stop: Math.PI * 2}} o={{strokeWidth: 16, stroke: C.shadow}} draw={draw} seed={2040} />
		</g>
		<R s={{kind: 'rect', x: -100, y: -60, w: 200, h: 170}} o={{fill: open > 0.5 ? C.red : C.green, fillStyle: 'solid'}} draw={draw} seed={2041} />
		<R s={{kind: 'circle', x: 0, y: 20, d: 36}} o={{fill: C.ink, fillStyle: 'solid'}} draw={draw} seed={2042} />
	</g>
);

const Gauge: React.FC<{value: number; max?: number; label: string; color?: string}> = ({value, max = 30, label, color = C.red}) => {
	const a = Math.PI + (Math.min(value, max) / max) * Math.PI;
	return (
		<g>
			<R s={{kind: 'arc', x: 0, y: 0, w: 520, h: 520, start: Math.PI, stop: Math.PI * 2}} o={{strokeWidth: 10}} seed={2050} />
			{[0, 0.25, 0.5, 0.75, 1].map((k, i) => {
				const aa = Math.PI + k * Math.PI;
				return <R key={k} s={{kind: 'line', x1: Math.cos(aa) * 230, y1: Math.sin(aa) * 230, x2: Math.cos(aa) * 260, y2: Math.sin(aa) * 260}} o={{strokeWidth: 5}} seed={2051 + i} />;
			})}
			<R s={{kind: 'line', x1: 0, y1: 0, x2: Math.cos(a) * 220, y2: Math.sin(a) * 220}} o={{strokeWidth: 10, stroke: color}} seed={2060} />
			<R s={{kind: 'circle', x: 0, y: 0, d: 40}} o={{fill: C.ink, fillStyle: 'solid'}} seed={2061} />
			<T x={0} y={90} size={110} font="marker" color={color}>
				{label}
			</T>
		</g>
	);
};

const Treadmill: React.FC<{run: boolean}> = ({run}) => {
	const frame = useCurrentFrame();
	const off = run ? (frame * 6) % 60 : 0;
	return (
		<g>
			<R s={{kind: 'rect', x: -260, y: -20, w: 520, h: 50}} o={{fill: C.ink, fillStyle: 'solid'}} seed={2070} />
			{[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
				<R key={i} s={{kind: 'line', x1: -250 + ((i * 60 + 520 - off) % 520), y1: -10, x2: -250 + ((i * 60 + 520 - off) % 520), y2: 20}} o={{stroke: C.shadow, strokeWidth: 4}} seed={2071 + i} boil={false} />
			))}
			<R s={{kind: 'line', x1: 230, y1: -20, x2: 200, y2: -320}} o={{strokeWidth: 9}} seed={2080} />
			<R s={{kind: 'rect', x: 140, y: -360, w: 120, h: 50}} o={{fill: C.shadow, fillStyle: 'solid'}} seed={2081} />
		</g>
	);
};

const FeeTag: React.FC<{text: string; big?: boolean; seed: number}> = ({text, big = false, seed}) => (
	<g transform={`scale(${big ? 1.5 : 1})`}>
		<PriceTag text="" seed={seed} fill={big ? C.red : C.yellow} />
		<T x={140} y={4} size={34} font="marker" color={big ? C.white : C.ink}>
			{text}
		</T>
	</g>
);

const Scissors: React.FC<{snip: number}> = ({snip}) => (
	<g>
		<g transform={`rotate(${-12 + snip * 12})`}>
			<R s={{kind: 'line', x1: 0, y1: 0, x2: 200, y2: -10}} o={{strokeWidth: 10, stroke: C.shadow}} seed={2090} />
			<R s={{kind: 'circle', x: -40, y: -30, d: 60}} o={{stroke: C.red, strokeWidth: 10}} seed={2091} />
		</g>
		<g transform={`rotate(${12 - snip * 12})`}>
			<R s={{kind: 'line', x1: 0, y1: 0, x2: 200, y2: 10}} o={{strokeWidth: 10, stroke: C.shadow}} seed={2092} />
			<R s={{kind: 'circle', x: -40, y: 30, d: 60}} o={{stroke: C.red, strokeWidth: 10}} seed={2093} />
		</g>
	</g>
);

const Title: React.FC<{text: string; at: number; S: number}> = ({text, at, S}) => {
	const {pop} = useCue(S);
	return (
		<T x={960} y={100} size={74} font="marker" scale={pop(at)}>
			{text}
		</T>
	);
};

// ---------------------------------------------------------------- 1. Hook (0 – 16.18)
const S1 = 0;
const Hook: React.FC = () => {
	const {p, pop, after} = useCue(S1);
	return (
		<Svg>
			<G x={520} y={560} s={pop(0.1)}>
				<Statement minGlow={after(3.67)} />
			</G>
			<G x={1050} y={980}>
				<Penny mood={after(8.7) ? 'shocked' : 'worried'} draw={p(0.3, 0.8)} />
			</G>
			{after(3.67) && (
				<G x={1500} y={380}>
					<R s={{kind: 'line', x1: -260, y1: 0, x2: -260 + 560 * p(5, 2.5), y2: 0}} o={{strokeWidth: 8, stroke: C.red}} seed={1} />
					<T x={0} y={-70} size={90} font="marker" color={C.red} scale={pop(6)}>
						{countUp(p(5, 2.5), 19)} YEARS
					</T>
				</G>
			)}
			{after(8.7) && (
				<G x={1500} y={640} s={pop(10.5)}>
					<Card w={560} h={200} seed={1} fill={C.yellow}>
						<T x={0} y={-45} size={38}>
							interest paid
						</T>
						<T x={0} y={35} size={90} font="marker" color={C.red}>
							${countUp(p(10.5, 1.5), 8100).toLocaleString('en-US')}
						</T>
					</Card>
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 2. Promise + title (16.18 – 30.85)
const S2 = 16.18;
const Promise_: React.FC = () => {
	const {p, pop, after, t} = useCue(S2);
	const rot = t * 40;
	if (t < 20.28) {
		return (
			<Svg>
				<G x={0} y={0} s={1}>
					<PawnShop draw={p(16.2, 0.8)} />
				</G>
				<T x={480} y={560} size={110} font="marker" color={C.red} scale={pop(17.5)}>
					= TIME
				</T>
			</Svg>
		);
	}
	if (t < 25.14) {
		return (
			<Svg>
				<G x={960} y={470} s={pop(20.28, 0.6)}>
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
				<T x={960} y={820} size={54} scale={pop(21)}>
					How credit card companies make money
				</T>
			</Svg>
		);
	}
	return (
		<Svg>
			<G x={960} y={420} s={pop(25.14) * 1.5}>
				<CreditCard />
			</G>
			{['SWIPE', 'INTEREST', 'FEES'].map((l, i) => (
				<G key={l} x={460 + i * 500} y={820} s={pop(26.5 + i * 0.8)}>
					<Card w={360} h={120} seed={2 + i} fill={i === 1 ? C.red : C.white}>
						<T x={0} y={6} size={58} font="marker" color={i === 1 ? C.white : C.ink}>
							{l}
						</T>
					</Card>
				</G>
			))}
		</Svg>
	);
};

// ---------------------------------------------------------------- 3. Engine 1: swipe (30.85 – 82.41)
const S3 = 30.85;
const Swipe: React.FC = () => {
	const {p, pop, after, t} = useCue(S3);
	const part = t < 49.48 ? 1 : t < 68.06 ? 2 : 3;
	return (
		<Svg>
			<Title text="ENGINE #1: THE SWIPE" at={30.85} S={S3} />
			{part === 1 && (
				<>
					<R s={{kind: 'rect', x: 200, y: 700, w: 900, h: 60}} o={{fill: C.brown, fillStyle: 'hachure'}} seed={10} />
					<G x={360} y={980}>
						<Penny mood="happy" draw={p(34.2, 0.6)} />
					</G>
					<G x={interpolate(p(35, 0.8), [0, 1], [500, 780])} y={560} s={0.5} r={-10}>
						<CreditCard />
					</G>
					<G x={900} y={600} s={pop(36)}>
						<Cash thick />
						<T x={0} y={60} size={44} font="marker">
							$100
						</T>
					</G>
					{after(38.78) && (
						<G x={interpolate(p(39.5, 1.2), [0, 1], [900, 1520])} y={interpolate(p(39.5, 1.2), [0, 1], [560, 480])} s={0.45}>
							<Cash />
						</G>
					)}
					<G x={1560} y={720} s={pop(38.9)}>
						<Bank />
						<T x={0} y={160} size={40} font="marker">
							BANKS + NETWORKS
						</T>
					</G>
					{after(42.52) && (
						<G x={900} y={300} s={pop(44.5)}>
							<Card w={500} h={140} seed={6} fill={C.yellow}>
								<T x={0} y={6} size={60} font="marker">
									~$2–3 per $100
								</T>
							</Card>
						</G>
					)}
				</>
			)}
			{part === 2 && (
				<>
					{Array.from({length: 40}).map((_, i) => {
						const row = Math.floor(Math.sqrt(i * 2));
						return after(51.25 + i * 0.08) ? (
							<G key={i} x={960 + ((i % 9) - 4) * 90 + (row % 2) * 30} y={920 - row * 60} s={0.5} r={((i * 29) % 30) - 15}>
								<Cash />
							</G>
						) : null;
					})}
					<T x={960} y={260} size={120} font="marker" color={C.green} scale={pop(54.5)}>
						$187 BILLION
					</T>
					<T x={960} y={360} size={44} scale={pop(55.5)}>
						US merchant card fees, 2024
					</T>
					{after(59.36) && (
						<>
							<rect x={0} y={420} width={1920} height={660} fill={C.paper} opacity={p(59.36, 0.3)} />
							{['milk', 'bread', 'shoes'].map((l, i) => (
								<G key={l} x={500 + i * 460} y={760} s={pop(62.2 + i * 0.4)}>
									<PriceTag text={`$${[4, 3, 60][i]}${t > 64 ? '.10' : '.00'}`} seed={10 + i} />
									<T x={140} y={-90} size={40}>
										{l}
									</T>
								</G>
							))}
							{after(65.5) && (
								<T x={960} y={980} size={48} font="marker" color={C.red} scale={pop(65.5)}>
									...even if you pay cash
								</T>
							)}
						</>
					)}
				</>
			)}
			{part === 3 && (
				<>
					<G x={1500} y={600}>
						<Bank />
					</G>
					<G x={420} y={980}>
						<Penny mood="happy" />
					</G>
					{/* big slice to the bank, small coin back to Penny */}
					{[0, 1, 2].map((i) => {
						const k = ((t - 72 + i * 1.3) % 3.9) / 3.9;
						return t > 72 ? (
							<React.Fragment key={i}>
								<G x={interpolate(k, [0, 1], [700, 1400])} y={460 - Math.sin(k * Math.PI) * 120} s={0.5}>
									<Cash thick />
								</G>
								<G x={interpolate(k, [0, 1], [1350, 560])} y={760 + Math.sin(k * Math.PI) * 80} s={0.4}>
									<Coin seed={i} />
								</G>
							</React.Fragment>
						) : null;
					})}
					<G x={960} y={260} s={pop(68.1)}>
						<Card w={560} h={130} seed={7} fill={C.yellow}>
							<T x={0} y={6} size={54} font="marker">
								CASH BACK &amp; POINTS
							</T>
						</Card>
					</G>
					{after(71.56) && (
						<T x={960} y={380} size={44} scale={pop(71.6)}>
							paid for, in part, by swipe fees
						</T>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 4. Engine 2: interest (82.41 – 141.68)
const S4 = 82.41;
const Interest: React.FC = () => {
	const {p, pop, after, t} = useCue(S4);
	const part = t < 101.68 ? 1 : t < 112.75 ? 2 : t < 127.7 ? 3 : 4;
	return (
		<Svg>
			<Title text="ENGINE #2: INTEREST" at={82.41} S={S4} />
			{part === 1 && (
				<>
					<G x={520} y={560} s={pop(89.2)}>
						<Card w={560} h={420} seed={8}>
							<R s={{kind: 'rect', x: -280, y: -210, w: 560, h: 70}} o={{fill: C.ink, fillStyle: 'solid'}} seed={20} />
							<T x={0} y={-174} size={40} font="marker" color={C.white}>
								THIS MONTH
							</T>
							<R s={{kind: 'rect', x: -240, y: -100, w: 480, h: 120}} o={{fill: '#9BE7B4', fillStyle: 'hachure'}} seed={21} />
							<T x={0} y={-40} size={44} font="marker">
								PAID IN FULL
							</T>
							<T x={0} y={110} size={60} font="marker" color={C.green}>
								$0 interest
							</T>
						</Card>
					</G>
					<G x={1350} y={600} s={pop(90)}>
						<Padlock open={p(97.8, 0.5)} />
					</G>
					{after(94.89) && t < 97.78 && (
						<T x={1350} y={850} size={50} font="marker" color={C.green} scale={pop(94.9)}>
							borrowing for free
						</T>
					)}
					{after(97.78) && (
						<T x={1350} y={850} size={50} font="marker" color={C.red} scale={pop(98.2)}>
							carry a balance...
						</T>
					)}
				</>
			)}
			{part === 2 && (
				<>
					<T x={960} y={240} size={56} font="marker" scale={pop(104.1)}>
						interest added EVERY DAY
					</T>
					{Array.from({length: 7}).map((_, i) => {
						const at = 104.6 + i * 0.9;
						const size = 120 + i * 22;
						return after(at) ? (
							<G key={i} x={300 + i * 220} y={700 - size / 2} s={pop(at)}>
								<R s={{kind: 'circle', x: 0, y: 0, d: size}} o={{fill: C.red, fillStyle: 'hachure'}} seed={30 + i} />
								<T x={0} y={size / 2 + 40} size={34}>
									day {i + 1}
								</T>
							</G>
						) : null;
					})}
					{after(109) && (
						<T x={960} y={960} size={46} font="marker" color={C.red} scale={pop(109)}>
							interest on last month&apos;s interest
						</T>
					)}
				</>
			)}
			{part === 3 && (
				<>
					<G x={620} y={700} s={pop(112.8)}>
						<Gauge value={22 * p(113.5, 1.2)} label={`${Math.round(22 * p(113.5, 1.2))}%`} />
						<T x={0} y={210} size={40}>
							avg rate if you carry a balance
						</T>
					</G>
					{after(121.24) && (
						<G x={1400} y={540} s={pop(121.3)}>
							<Card w={780} h={240} seed={9} fill={C.yellow}>
								<T x={0} y={-60} size={40}>
									Americans owe
								</T>
								<T x={0} y={30} size={84} font="marker" color={C.red}>
									$1.26 TRILLION
								</T>
							</Card>
						</G>
					)}
				</>
			)}
			{part === 4 && (
				<>
					<G x={620} y={600}>
						<R s={{kind: 'circle', x: 0, y: 0, d: 480}} o={{fill: C.white, fillStyle: 'solid'}} seed={40} />
						{p(128, 1.2) > 0 && (
							<R s={{kind: 'arc', x: 0, y: 0, w: 480, h: 480, start: -Math.PI / 2, stop: -Math.PI / 2 + Math.PI * 2 * 0.94 * p(128, 1.2), closed: true}} o={{fill: C.red, fillStyle: 'hachure'}} seed={41} />
						)}
						<T x={0} y={300} size={44} font="marker" color={C.red} scale={pop(131)}>
							94% paid by people carrying a balance
						</T>
					</G>
					{after(136.25) && (
						<>
							<G x={1500} y={420} s={pop(136.3)}>
								<Card w={640} h={120} seed={10} fill={C.green}>
									<T x={0} y={6} size={42} font="marker" color={C.white}>
										PAY IN FULL: rewards
									</T>
								</Card>
							</G>
							<R s={{kind: 'line', x1: 1500, y1: 800, x2: 1500, y2: 500}} o={{strokeWidth: 8, stroke: C.red}} draw={p(137, 0.6)} seed={42} />
							<G x={1500} y={860} s={pop(137.2)}>
								<Card w={640} h={120} seed={11} fill={C.red}>
									<T x={0} y={6} size={42} font="marker" color={C.white}>
										CARRY A BALANCE: pays
									</T>
								</Card>
							</G>
						</>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 5. Minimum trap (141.68 – 182.0)
const S5 = 141.68;
const Trap: React.FC = () => {
	const {p, pop, after, t} = useCue(S5);
	const split = after(163.37);
	return (
		<Svg>
			<Title text="THE MINIMUM-PAYMENT TRAP" at={141.68} S={S5} />
			{!split && (
				<>
					{t < 153.82 ? (
						<>
							<G x={560} y={600} s={pop(141.8) * 0.9}>
								<Statement minGlow />
							</G>
							{after(147.48) && (
								<G x={1350} y={560}>
									<R s={{kind: 'rect', x: -350, y: -60, w: 700 * (91.67 / 141.67), h: 120}} o={{fill: C.red, fillStyle: 'hachure'}} draw={p(149, 0.8)} seed={50} />
									<R s={{kind: 'rect', x: -350 + 700 * (91.67 / 141.67), y: -60, w: 700 * (50 / 141.67), h: 120}} o={{fill: C.green, fillStyle: 'hachure'}} draw={p(150, 0.8)} seed={51} />
									<T x={-350 + 350 * (91.67 / 141.67)} y={120} size={44} font="marker" color={C.red} scale={pop(150.5)}>
										$91.67 interest
									</T>
									<T x={-350 + 700 * (91.67 / 141.67) + 350 * (50 / 141.67)} y={120} size={36} color={C.green} scale={pop(151)}>
										$50 debt
									</T>
								</G>
							)}
						</>
					) : (
						<>
							<G x={900} y={900}>
								<Treadmill run />
								<G x={-40} y={-30}>
									<Penny walk mood="worried" />
								</G>
							</G>
							<G x={1550} y={500}>
								<R s={{kind: 'rect', x: -60, y: -300, w: 120, h: 600}} o={{stroke: C.ink}} seed={52} />
								<R s={{kind: 'rect', x: -60, y: -300 + 600 * 0.04 * p(154, 8), w: 120, h: 600 * (1 - 0.04 * p(154, 8))}} o={{fill: C.red, fillStyle: 'hachure', stroke: 'none'}} seed={53} />
								<T x={0} y={350} size={40}>
									balance
								</T>
							</G>
							{after(156.14) && (
								<T x={700} y={330} size={46} font="marker" scale={pop(156.2)}>
									balance shrinks, so the minimum shrinks
								</T>
							)}
						</>
					)}
				</>
			)}
			{split && (
				<>
					<R s={{kind: 'line', x1: 960, y1: 200, x2: 960, y2: 1000}} o={{strokeWidth: 5}} seed={54} />
					<T x={480} y={260} size={58} font="marker" color={C.red} scale={pop(163.4)}>
						MINIMUM ONLY
					</T>
					<T x={1440} y={260} size={58} font="marker" color={C.green} scale={pop(164.5)}>
						$200 / MONTH
					</T>
					<G x={480} y={560} s={pop(163.8)}>
						<T x={0} y={-60} size={110} font="marker" color={C.red}>
							19 yrs
						</T>
						<T x={0} y={80} size={70} font="marker">
							$8,100 interest
						</T>
					</G>
					<G x={1440} y={560} s={pop(168.9)}>
						<T x={0} y={-60} size={110} font="marker" color={C.green}>
							&lt; 3 yrs
						</T>
						<T x={0} y={80} size={70} font="marker">
							$1,750 interest
						</T>
					</G>
					{[176.66, 178.06, 179.45].map((at, i) => (
						<G key={at} x={960} y={820 + i * 70} s={pop(at)}>
							<T x={0} y={0} size={48} font={i === 2 ? 'marker' : 'hand'} color={i === 2 ? C.red : C.ink}>
								{['Same card.', 'Same rate.', 'Completely different outcome.'][i]}
							</T>
						</G>
					))}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 6. Engine 3: fees (182.0 – 207.5)
const S6 = 182.0;
const Fees: React.FC = () => {
	const {p, pop, after, t} = useCue(S6);
	const tags = [
		{at: 185.3, text: 'ANNUAL', x: 300, y: 380},
		{at: 186.5, text: 'CASH ADV.', x: 760, y: 300},
		{at: 188, text: 'FOREIGN', x: 1220, y: 380},
	];
	return (
		<Svg>
			<Title text="ENGINE #3: FEES" at={182} S={S6} />
			{tags.map((tg, i) => (
				<G key={tg.text} x={tg.x} y={interpolate(p(tg.at, 0.6), [0, 1], [-100, tg.y])} r={((i * 17) % 20) - 10}>
					<FeeTag text={tg.text} seed={20 + i} />
				</G>
			))}
			{after(191.07) && (
				<G x={640} y={interpolate(p(191.07, 0.5), [0, 1], [-200, 640])} r={-6}>
					<FeeTag text="LATE FEE" big seed={30} />
				</G>
			)}
			{after(192.47) && (
				<G x={1400} y={680} s={pop(195)}>
					<Card w={540} h={200} seed={12} fill={C.yellow}>
						<T x={0} y={-45} size={38}>
							late fees, one year
						</T>
						<T x={0} y={35} size={90} font="marker" color={C.red}>
							$14.5B
						</T>
					</Card>
				</G>
			)}
			{after(199.68) && (
				<>
					<rect x={0} y={180} width={1920} height={900} fill={C.paper} opacity={p(199.68, 0.3)} />
					<G x={960} y={760} s={pop(200)}>
						<Gauge value={22 + 7 * p(202.5, 1)} label={t > 203 ? 'PENALTY APR' : '22%'} />
					</G>
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 7. Machine + advice (207.5 – 240.41)
const S7 = 207.5;
const Machine: React.FC = () => {
	const {p, pop, after, t} = useCue(S7);
	const rot = t * 40;
	const advice = after(224.08);
	const engines = [
		{at: 209.53, label: 'SWIPE', sub: 'when you spend', color: C.blue},
		{at: 213.24, label: 'INTEREST', sub: "when you can't pay", color: C.red},
		{at: 216.25, label: 'FEES', sub: 'when you slip', color: C.gold},
	];
	const rules = [
		{at: 226.21, text: 'Pay the full statement balance'},
		{at: 231.37, text: 'Otherwise, pay WAY more than the minimum'},
		{at: 235.36, text: 'Set up autopay'},
	];
	return (
		<Svg>
			{!advice ? (
				<>
					<Title text="THE MACHINE" at={207.5} S={S7} />
					{engines.map((e, i) => (
						<G key={e.label} x={420 + i * 540} y={520} s={pop(e.at)}>
							<Gear r={170} rot={(i % 2 ? -1 : 1) * rot} fill={e.color} seed={10 + i} />
							<Card w={300} h={80} seed={13 + i}>
								<T x={0} y={4} size={46} font="marker">
									{e.label}
								</T>
							</Card>
							<T x={0} y={240} size={44}>
								{e.sub}
							</T>
						</G>
					))}
					{after(218.96) && (
						<G x={960} y={940} s={pop(219)}>
							<Card w={1100} h={110} seed={16} fill={C.yellow}>
								<T x={0} y={6} size={48} font="marker">
									best customer = spends a lot, pays slowly
								</T>
							</Card>
						</G>
					)}
				</>
			) : (
				<>
					<G x={340} y={980}>
						<Penny mood="confident" />
					</G>
					<T x={1100} y={160} size={70} font="marker" color={C.red} scale={pop(224.1)}>
						Don&apos;t be that customer:
					</T>
					{rules.map((r, i) => (
						<G key={r.text} x={1100} y={380 + i * 180} s={pop(r.at)}>
							<Card w={1000} h={140} seed={20 + i}>
								<T x={-440} y={4} size={64} font="marker" color={C.blue}>
									{i + 1}
								</T>
								<T x={30} y={4} size={46}>
									{r.text}
								</T>
								<G x={450} y={0}>
									<Tick draw={p(r.at + 1.5, 0.4)} seed={4 + i} />
								</G>
							</Card>
						</G>
					))}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 8. Payoff + bridge (240.41 – 253.01)
const S8 = 240.41;
const Payoff: React.FC = () => {
	const {p, pop, after, t} = useCue(S8);
	const snip = Math.abs(Math.sin(Math.max(0, t - 241) * 6));
	return (
		<Svg>
			{t < 244.23 ? (
				<>
					<G x={760} y={560} s={0.9}>
						<Statement minGlow />
					</G>
					<G x={1150} y={810} s={pop(240.5)}>
						<Scissors snip={snip} />
					</G>
					<T x={1450} y={400} size={56} font="marker" scale={pop(241)}>
						spend + wait = $$$
					</T>
				</>
			) : (
				<>
					<G x={1250} y={560} s={pop(244.3)}>
						<R s={{kind: 'rect', x: -300, y: -320, w: 600, h: 640}} o={{fill: '#E6DFD0', fillStyle: 'solid'}} seed={60} />
						<R s={{kind: 'line', x1: 0, y1: -200, x2: 0, y2: 320}} o={{strokeWidth: 5}} seed={61} />
						<Card w={460} h={110} seed={30} fill={C.red}>
							<T x={0} y={6} size={52} font="marker" color={C.white}>
								MEMBERS ONLY
							</T>
						</Card>
					</G>
					<G x={interpolate(t, [244.3, 248], [300, 700], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})} y={1000}>
						<Penny walk={t < 248} mood="thinking" look={1} />
					</G>
					{after(248.98) && (
						<G x={1250} y={980} s={pop(249)}>
							<T x={0} y={0} size={64} font="marker" color={C.red}>
								NEXT: COSTCO
							</T>
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- End screen
const S9 = VO3_SECONDS;
const EndScreen: React.FC = () => {
	const {pop} = useCue(S9);
	return (
		<Svg>
			<T x={960} y={110} size={84} font="marker" scale={pop(S9)}>
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
	[0.1, 'slap', 0.5],
	[3.67, 'ding', 0.4],
	[5.0, 'clock', 0.45],
	[10.5, 'rise', 0.35],
	[12.0, 'sting_dark', 0.45],
	[16.2, 'whoosh', 0.4],
	[17.5, 'chaching', 0.45],
	[20.28, 'sting', 0.6],
	[25.14, 'pop', 0.5],
	[26.5, 'pop', 0.4],
	[27.3, 'pop', 0.4],
	[28.1, 'pop', 0.4],
	[30.85, 'pop', 0.5],
	[35.4, 'beep', 0.5],
	[36.0, 'chaching', 0.5],
	[39.5, 'whoosh', 0.45],
	[44.5, 'pop', 0.45],
	[51.25, 'rise', 0.35],
	[54.5, 'chaching', 0.5],
	[62.2, 'pop', 0.4],
	[64.0, 'tick', 0.4],
	[65.5, 'bloop', 0.45],
	[68.1, 'ding', 0.45],
	[72.0, 'coin', 0.4],
	[75.9, 'coin', 0.4],
	[79.8, 'coin', 0.4],
	[82.41, 'pop', 0.5],
	[89.2, 'pop', 0.45],
	[97.8, 'stamp', 0.5],
	[104.6, 'tick', 0.35],
	[105.5, 'tick', 0.35],
	[106.4, 'tick', 0.35],
	[107.3, 'tick', 0.35],
	[108.2, 'tick', 0.35],
	[113.5, 'rise', 0.35],
	[121.3, 'chaching', 0.45],
	[128.0, 'rise', 0.3],
	[136.3, 'pop', 0.45],
	[141.68, 'pop', 0.5],
	[149.0, 'flip', 0.45],
	[153.82, 'whirr', 0.4],
	[155.4, 'whirr', 0.4],
	[163.4, 'whoosh', 0.45],
	[168.9, 'ding', 0.5],
	[179.45, 'sting', 0.45],
	[182.0, 'pop', 0.5],
	[185.3, 'slap', 0.45],
	[186.5, 'slap', 0.45],
	[188.0, 'slap', 0.45],
	[191.1, 'stamp', 0.6],
	[195.0, 'chaching', 0.45],
	[200.0, 'buzzer', 0.35],
	[203.0, 'sting_dark', 0.45],
	[207.5, 'whirr', 0.4],
	[209.53, 'pop', 0.45],
	[213.24, 'pop', 0.45],
	[216.25, 'pop', 0.45],
	[219.0, 'ding', 0.4],
	[227.8, 'tick', 0.5],
	[232.9, 'tick', 0.5],
	[236.9, 'tick', 0.5],
	[241.0, 'tick', 0.45],
	[241.5, 'tick', 0.45],
	[244.3, 'whoosh', 0.4],
	[248.98, 'sting_dark', 0.5],
	[VO3_SECONDS + 0.2, 'sting', 0.5],
];

const scenes: [number, number, React.FC][] = [
	[S1, S2, Hook],
	[S2, S3, Promise_],
	[S3, S4, Swipe],
	[S4, S5, Interest],
	[S5, S6, Trap],
	[S6, S7, Fees],
	[S7, S8, Machine],
	[S8, S9, Payoff],
	[S9, EP03_SECONDS, EndScreen],
];

export const Ep03: React.FC = () => {
	const {fps} = useVideoConfig();
	return (
		<AbsoluteFill style={{background: C.paper}}>
			<Audio src={staticFile('ep03_vo.mp3')} />
			<Soundtrack music="music_lofi_ep02.mp3" sfx={SFX} voEnd={VO3_SECONDS} dips={[176.66]} />
			{scenes.map(([a, b, Comp], i) => (
				<Sequence key={i} from={Math.round(a * fps)} durationInFrames={Math.round((b - a) * fps)}>
					<Comp />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
