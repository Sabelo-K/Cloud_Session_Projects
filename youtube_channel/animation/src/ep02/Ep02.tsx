import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {Penny} from '../lib/characters';
import {Bubble, Card, Coin, Gear, Paper, PriceTag, Tick, Cash} from '../lib/props';
import {CasinoSign, Calculator, Cart, Chicken, HotDog, Kayak, MemberCard, PaperTowels, Receipt, TV, Vault, Warehouse} from '../lib/props2';
import {C, G, R, T, countUp, useP} from '../lib/rough';
import {SfxCue, Soundtrack} from '../lib/sound';

/**
 * Episode 2: How Costco Makes Money (It's Not What You Buy).
 * Cue times are GLOBAL seconds from timing_ep02.json (exact, generated with the Kokoro voiceover).
 */
export const VO2_SECONDS = 252.71;
export const EP02_SECONDS = VO2_SECONDS + 12;

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

// ---------------------------------------------------------------- 1. Hook (0 – 14.28)
const S1 = 0;
const Hook: React.FC = () => {
	const {p, pop, after, t} = useCue(S1);
	const year = Math.round(interpolate(t, [1.2, 6.5], [1985, 2025], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
	return (
		<Svg>
			{/* food court sign */}
			<G x={960} y={250} s={pop(0.2)}>
				<R s={{kind: 'rect', x: -420, y: -110, w: 840, h: 220}} o={{fill: C.red, fillStyle: 'solid'}} seed={1} />
				<T x={0} y={-40} size={58} font="marker" color={C.white}>
					HOT DOG + SODA
				</T>
				<T x={0} y={45} size={100} font="marker" color={C.yellow} stroke={C.ink}>
					$1.50
				</T>
			</G>
			<G x={760} y={680}>
				<HotDog draw={p(0.6, 1)} />
			</G>
			{/* calendar flipping years */}
			<G x={1400} y={680} s={pop(1)}>
				<Card w={300} h={260} seed={1}>
					<R s={{kind: 'rect', x: -150, y: -130, w: 300, h: 60}} o={{fill: C.ink, fillStyle: 'solid'}} seed={2} />
					<T x={0} y={-100} size={34} font="marker" color={C.white}>
						YEAR
					</T>
					<T x={0} y={40} size={96} font="marker">
						{year}
					</T>
				</Card>
			</G>
			{after(7.1) && (
				<T x={960} y={930} size={64} font="marker" color={C.green} scale={pop(7.1)}>
					SAME PRICE.
				</T>
			)}
			{after(10.5) && (
				<G x={1650} y={330} s={pop(10.5)}>
					<T x={0} y={0} size={120} font="marker" color={C.red}>
						?!
					</T>
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 2. Promise + title (14.28 – 28.22)
const S2 = 14.28;
const Promise_: React.FC = () => {
	const {p, pop, after, t} = useCue(S2);
	const rot = t * 40;
	const title = after(22.62);
	return (
		<Svg>
			{!title ? (
				<>
					<G x={560} y={560}>
						<Gear r={160} rot={rot} fill={C.blue} seed={1} draw={p(14.4, 1)} label="FOOD" />
					</G>
					<G x={1360} y={560}>
						<Gear r={160} rot={-rot} fill={C.green} seed={2} draw={p(15, 1)} label="STUFF" />
					</G>
					<G x={960} y={680} s={after(18.87) ? 1 + 0.15 * pop(18.87) : 0.9}>
						<Gear r={150} rot={rot * 1.2} fill={after(18.87) ? C.red : C.shadow} seed={3} draw={p(15.6, 1)} label="?" />
					</G>
					<T x={960} y={170} size={60} scale={pop(14.4)}>
						Costco sells... everything.
					</T>
				</>
			) : (
				<>
					<G x={960} y={470} s={pop(22.62, 0.6)}>
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
					<T x={960} y={820} size={54} scale={pop(23.4)}>
						Ep. 2 · How Costco makes money
					</T>
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 3. Setup (28.22 – 43.7)
const S3 = 28.22;
const Setup: React.FC = () => {
	const {p, pop, after} = useCue(S3);
	return (
		<Svg>
			<Warehouse draw={p(28.22, 1.2)} />
			<R s={{kind: 'rect', x: 1150, y: 520, w: 520, h: 490}} o={{fill: '#E6DFD0', fillStyle: 'solid'}} seed={3} />
			<R s={{kind: 'line', x1: 1410, y1: 680, x2: 1410, y2: 1010}} o={{strokeWidth: 5}} seed={4} />
			<G x={1410} y={600} s={pop(29.6)}>
				<Card w={460} h={120} seed={2} fill={C.red}>
					<T x={0} y={4} size={52} font="marker" color={C.white}>
						MEMBERS ONLY
					</T>
				</Card>
			</G>
			<G x={700} y={980}>
				<Penny mood={after(37.08) ? 'worried' : 'neutral'} draw={p(28.5, 0.8)} look={1} />
			</G>
			<G x={1060} y={430} s={pop(31.5)}>
				<Card w={260} h={130} seed={3}>
					<T x={0} y={-25} size={30}>
						per year
					</T>
					<T x={0} y={25} size={70} font="marker" color={C.red}>
						$65
					</T>
				</Card>
			</G>
			{after(34.5) && (
				<G x={interpolate(p(34.5, 0.6), [0, 1], [1060, 800])} y={interpolate(p(34.5, 0.6), [0, 1], [430, 700])} s={0.5}>
					<MemberCard />
				</G>
			)}
			{after(40.3) && (
				<T x={1410} y={820} size={60} font="marker" color={C.red} scale={pop(41.5)}>
					= THE TRICK
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 4. Membership machine (43.7 – 101.65)
const S4 = 43.7;
const Machine: React.FC = () => {
	const {p, pop, after, t} = useCue(S4);
	const part = t < 54.53 ? 1 : t < 69.35 ? 2 : t < 88.99 ? 3 : 4;
	return (
		<Svg>
			<T x={960} y={100} size={74} font="marker" scale={pop(43.7)}>
				THE MEMBERSHIP MACHINE
			</T>
			{part === 1 && (
				<>
					{Array.from({length: 24}).map((_, i) => (
						<G key={i} x={260 + (i % 8) * 200} y={330 + Math.floor(i / 8) * 170} s={0.5 * pop(45.6 + i * 0.05)} r={((i * 37) % 20) - 10}>
							<MemberCard seed={i % 5} />
						</G>
					))}
					<G x={960} y={870} s={pop(45.6)}>
						<Card w={960} h={130} seed={4} fill={C.yellow}>
							<T x={0} y={6} size={64} font="marker">
								{countUp(p(45.6, 1.4), 81)} MILLION MEMBERS
							</T>
						</Card>
					</G>
					{after(48.86) && (
						<G x={960} y={1010} s={pop(50.5)}>
							<T x={0} y={0} size={50} font="marker" color={C.green}>
								fees: $5.3 BILLION / year
							</T>
						</G>
					)}
				</>
			)}
			{part === 2 && (
				<>
					<R s={{kind: 'line', x1: 520, y1: 900, x2: 1400, y2: 900}} o={{strokeWidth: 5}} seed={10} />
					{p(54.6, 1) > 0 && <R s={{kind: 'rect', x: 1080, y: 900 - 600 * p(54.6, 1), w: 240, h: 600 * p(54.6, 1)}} o={{fill: C.blue, fillStyle: 'hachure'}} seed={11} />}
					{p(61.2, 1) > 0 && <R s={{kind: 'rect', x: 600, y: 900 - 394 * p(61.2, 1), w: 240, h: 394 * p(61.2, 1)}} o={{fill: C.green, fillStyle: 'hachure'}} seed={12} />}
					<T x={1200} y={950} size={42} scale={pop(55)}>
						total profit
					</T>
					<T x={1200} y={250} size={70} font="marker" color={C.blue} scale={pop(58.8)}>
						$8.1B
					</T>
					<T x={720} y={950} size={42} scale={pop(61.2)}>
						membership fees
					</T>
					<T x={720} y={450} size={70} font="marker" color={C.green} scale={pop(62)}>
						$5.3B
					</T>
					{after(62.8) && (
						<G x={1650} y={520} s={pop(62.8)}>
							<T x={0} y={0} size={110} font="marker" color={C.red}>
								~ 2/3
							</T>
						</G>
					)}
					{after(65.62) && (
						<T x={1650} y={680} size={44} scale={pop(66.5)}>
							cost to collect: ~$0
						</T>
					)}
				</>
			)}
			{part === 3 && (
				<>
					<G x={1300} y={560} s={pop(69.4)}>
						<Vault />
					</G>
					{/* money flowing into the vault, before the hot dog appears */}
					{[0, 1, 2, 3, 4].map((i) => {
						const k = ((t - 71.5 + i * 0.6) % 3) / 3;
						return t > 71.5 ? (
							<G key={i} x={interpolate(k, [0, 1], [300, 1200])} y={interpolate(k, [0, 1], [420 + i * 60, 560])} s={0.6} o={k < 0.9 ? 1 : 0}>
								<Cash />
							</G>
						) : null;
					})}
					<G x={420} y={850} s={after(71.46) ? pop(71.46) : 0}>
						<HotDog />
						<T x={0} y={130} size={40}>
							(not sold yet)
						</T>
					</G>
					<T x={760} y={260} size={56} font="marker" color={C.green} scale={pop(75)}>
						PAID UP FRONT
					</T>
					{after(81.66) && (
						<G x={1300} y={900} s={pop(82.5)}>
							<T x={0} y={0} size={52} font="marker">
								so: razor-thin margins on everything else
							</T>
						</G>
					)}
				</>
			)}
			{part === 4 && (
				<>
					<G x={960} y={560}>
						<g transform={`rotate(${(t - 89) * 90})`}>
							<R s={{kind: 'arc', x: 0, y: 0, w: 560, h: 560, start: 0.2, stop: Math.PI * 1.75}} o={{stroke: C.green, strokeWidth: 14}} seed={20} />
							<R s={{kind: 'polygon', pts: [[280, -20], [320, 60], [235, 50]]}} o={{fill: C.green, fillStyle: 'solid', stroke: C.green}} seed={21} />
						</g>
						<G s={0.8}>
							<MemberCard />
						</G>
					</G>
					<G x={960} y={920} s={pop(92.5)}>
						<T x={0} y={0} size={80} font="marker" color={C.green}>
							92% RENEW
						</T>
					</G>
					<T x={330} y={420} size={46} scale={pop(97.76)}>
						not a store...
					</T>
					{after(99.53) && (
						<G x={1600} y={420} s={pop(99.53)}>
							<Card w={420} h={120} seed={5} fill={C.yellow}>
								<T x={0} y={6} size={52} font="marker">
									SUBSCRIPTION
								</T>
							</Card>
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 5. Bait (101.65 – 133.71)
const S5 = 101.65;
const Bait: React.FC = () => {
	const {p, pop, after, t} = useCue(S5);
	const chickenPart = after(114.14);
	const walk = interpolate(t, [125.6, 131.5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const items: [number, React.FC<{draw?: number}>][] = [
		[127.6, TV],
		[129.0, PaperTowels],
		[130.6, Kayak],
	];
	return (
		<Svg>
			{!chickenPart && (
				<>
					<G x={700} y={560} s={1.3}>
						<HotDog draw={p(101.7, 0.6)} />
					</G>
					<G x={760} y={230} s={pop(104.27)}>
						<T x={0} y={0} size={110} font="marker" color={C.red}>
							BAIT
						</T>
					</G>
					{after(105.94) && (
						<G x={1400} y={500} s={pop(108.5)} r={-6}>
							<Card w={480} h={240} seed={6}>
								<T x={0} y={-70} size={34}>
									with inflation it&apos;d be
								</T>
								<T x={0} y={20} size={110} font="marker" color={C.red}>
									$4+
								</T>
							</Card>
						</G>
					)}
					{after(110) && (
						<T x={1400} y={800} size={44} scale={pop(110.5)}>
							&quot;The price will not change.&quot;
						</T>
					)}
				</>
			)}
			{chickenPart && (
				<>
					<G x={1600} y={420} s={pop(114.2)}>
						<Chicken glow />
						<G x={-20} y={150}>
							<PriceTag text="$4.99" seed={1} />
						</G>
					</G>
					{after(122.22) && (
						<T x={960} y={140} size={56} font="marker" color={C.green} scale={pop(122.22)}>
							&quot;The membership pays for itself!&quot;
						</T>
					)}
					{/* winding path to the chicken */}
					{after(125.6) && (
						<R s={{kind: 'curve', pts: [[200, 900], [500, 700], [800, 900], [1100, 650], [1400, 600]]}} o={{stroke: C.shadow, strokeWidth: 6, strokeLineDash: [16, 14]}} draw={p(125.6, 1.5)} seed={30} />
					)}
					<G x={interpolate(walk, [0, 1], [200, 1250])} y={1000}>
						<Penny walk={walk > 0 && walk < 1} mood="happy" />
						<G x={-260} y={-60} s={0.8}>
							<Cart>
								{items.map(([at, Item], i) =>
									after(at) ? (
										<G key={i} x={-60 + i * 60} y={-220 - i * 50} s={0.45 * pop(at)}>
											<Item />
										</G>
									) : null,
								)}
							</Cart>
						</G>
					</G>
					{items.map(([at, Item], i) =>
						after(at - 1) && !after(at) ? (
							<G key={i} x={500 + i * 300} y={420} s={pop(at - 1)}>
								<Item />
							</G>
						) : null,
					)}
					{after(131.6) && (
						<G x={360} y={180}>
							<Receipt p={p(131.6, 0.8)} lines={['chicken ... 4.99', 'TV ... 279.99', 'towels ... 24.99', 'kayak ... 102.90']} total="$412.87" />
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 6. Math (133.71 – 159.47)
const S6 = 133.71;
const Math_: React.FC = () => {
	const {p, pop, after, t} = useCue(S6);
	const display = t < 138.5 ? '65' : t < 141 ? '65 / 10%' : '650';
	return (
		<Svg>
			<T x={960} y={100} size={74} font="marker" scale={pop(133.71)}>
				PENNY&apos;S MATH
			</T>
			<G x={420} y={980}>
				<Penny mood="thinking" draw={p(133.8, 0.6)} />
			</G>
			<G x={820} y={560} s={pop(135.67)}>
				<Calculator display={display} />
			</G>
			{after(141.5) && (
				<G x={1420} y={360} s={pop(141.5)}>
					<Card w={560} h={180} seed={7}>
						<T x={0} y={-40} size={36}>
							spend to break even
						</T>
						<T x={0} y={30} size={80} font="marker" color={C.green}>
							$650 / yr
						</T>
					</Card>
				</G>
			)}
			{after(146.17) && (
				<G x={1420} y={660} s={pop(149.5)}>
					<Card w={560} h={200} seed={8} fill={C.yellow}>
						<T x={0} y={-45} size={36}>
							actual sales per member
						</T>
						<T x={0} y={35} size={90} font="marker" color={C.red}>
							${countUp(p(149.5, 1.2), 3300).toLocaleString('en-US')}+
						</T>
					</Card>
				</G>
			)}
			{after(156.24) && (
				<T x={1420} y={890} size={46} font="marker" scale={pop(156.24)}>
					whole shopping life moves in
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 7. Upgrade (159.47 – 190.15)
const S7 = 159.47;
const Upgrade: React.FC = () => {
	const {p, pop, after, t} = useCue(S7);
	const pieP = p(181, 1.2);
	return (
		<Svg>
			<T x={960} y={100} size={74} font="marker" scale={pop(159.47)}>
				THE UPGRADE
			</T>
			{t < 179.9 ? (
				<>
					<G x={560} y={500} s={pop(159.8)}>
						<MemberCard />
						<T x={0} y={150} size={60} font="marker">
							$65
						</T>
					</G>
					<G x={1360} y={500} s={pop(161.5) * 1.3}>
						<MemberCard exec />
						<T x={0} y={150} size={60} font="marker" color={C.red}>
							$130
						</T>
					</G>
					<T x={960} y={500} size={90} font="marker" scale={pop(162)}>
						{'>>'}
					</T>
					{after(165.5) && (
						<G x={1360} y={800} s={pop(166)}>
							<T x={0} y={0} size={48} font="marker" color={C.green}>
								+ rewards on what you spend
							</T>
						</G>
					)}
					{after(173.57) && (
						<G x={960} y={950} s={pop(174)}>
							<T x={0} y={0} size={50}>
								to make it pay off... shop at Costco even more
							</T>
						</G>
					)}
				</>
			) : (
				<>
					<G x={620} y={580}>
						<R s={{kind: 'circle', x: 0, y: 0, d: 480}} o={{fill: C.white, fillStyle: 'solid'}} seed={40} />
						{pieP > 0 && <R s={{kind: 'arc', x: 0, y: 0, w: 480, h: 480, start: -Math.PI / 2, stop: -Math.PI / 2 + Math.PI * 2 * 0.478 * pieP, closed: true}} o={{fill: C.gold, fillStyle: 'hachure'}} seed={41} />}
						<T x={0} y={300} size={44} scale={pop(181)}>
							38.7M of 81M members
						</T>
					</G>
					{after(183.59) && (
						<G x={1340} y={580}>
							<R s={{kind: 'circle', x: 0, y: 0, d: 480}} o={{fill: C.white, fillStyle: 'solid'}} seed={42} />
							{p(185, 1.2) > 0 && (
								<R s={{kind: 'arc', x: 0, y: 0, w: 480, h: 480, start: -Math.PI / 2, stop: -Math.PI / 2 + Math.PI * 2 * 0.736 * p(185, 1.2), closed: true}} o={{fill: C.red, fillStyle: 'hachure'}} seed={43} />
							)}
							<T x={0} y={300} size={44} font="marker" color={C.red} scale={pop(186)}>
								~74% OF ALL SALES
							</T>
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 8. Machine reveal (190.15 – 216.38)
const S8 = 190.15;
const Reveal: React.FC = () => {
	const {pop, after, t} = useCue(S8);
	const rot = t * 40;
	const steps = [
		{at: 192.17, text: 'thin margins'},
		{at: 196.7, text: 'low prices'},
		{at: 200.09, text: 'members renew'},
		{at: 202.8, text: 'real money'},
	];
	return (
		<Svg>
			<G x={960} y={560} s={after(202.8) ? 1 + 0.1 * pop(202.8) : 1}>
				<Gear r={220} rot={rot} fill={C.red} seed={6} />
				<Card w={420} h={96} seed={30} fill={C.yellow}>
					<T x={0} y={4} size={50} font="marker">
						MEMBERSHIPS
					</T>
				</Card>
			</G>
			{steps.map((s, i) => {
				const a = (i / 4) * Math.PI * 2 - Math.PI / 2;
				return (
					<G key={s.text} x={960 + Math.cos(a) * 560} y={560 + Math.sin(a) * 330} s={pop(s.at)}>
						<Card w={380} h={100} seed={10 + i} fill={i === 3 ? C.yellow : C.white}>
							<T x={0} y={4} size={46} font="marker">
								{s.text}
							</T>
						</Card>
					</G>
				);
			})}
			{after(206.23) && (
				<T x={960} y={1000} size={50} font="marker" scale={pop(206.23)}>
					the warehouse = a showroom for the subscription
				</T>
			)}
			{after(209.9) && (
				<G x={300} y={140} s={pop(213.27)}>
					<Bubble w={460} h={150} draw={1} tail="right">
						<T x={0} y={4} size={42} font="marker">
							See you next year!
						</T>
					</Bubble>
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 9. Advice (216.38 – 237.46)
const S9 = 216.38;
const Advice: React.FC = () => {
	const {p, pop, after} = useCue(S9);
	const rules = [
		{at: 221.77, text: "Count only things you'd buy anyway"},
		{at: 226.66, text: 'Bulk only wins if you use it all'},
		{at: 231.65, text: 'Upgrade only if rewards cover it'},
	];
	return (
		<Svg>
			<G x={340} y={980}>
				<Penny mood={after(221.77) ? 'confident' : 'thinking'} />
			</G>
			<T x={1100} y={150} size={74} font="marker" scale={pop(216.38)}>
				Is a membership worth it?
			</T>
			<T x={1100} y={270} size={56} font="marker" color={C.green} scale={pop(218.77)}>
				It can be. Do the math:
			</T>
			{rules.map((r, i) => (
				<G key={r.text} x={1100} y={450 + i * 170} s={pop(r.at)}>
					<Card w={940} h={130} seed={20 + i}>
						<T x={-410} y={4} size={64} font="marker" color={C.blue}>
							{i + 1}
						</T>
						<T x={30} y={4} size={46}>
							{r.text}
						</T>
						<G x={420} y={0}>
							<Tick draw={p(r.at + 1.4, 0.4)} seed={4 + i} />
						</G>
					</Card>
				</G>
			))}
		</Svg>
	);
};

// ---------------------------------------------------------------- 10. Payoff + bridge (237.46 – 252.71)
const S10 = 237.46;
const Payoff: React.FC = () => {
	const {pop, after, t} = useCue(S10);
	return (
		<Svg>
			<G x={520} y={330} s={pop(237.46)}>
				<T x={0} y={0} size={60} font="marker" color={C.shadow}>
					Pawn shops sell TIME
				</T>
			</G>
			<G x={520} y={450} s={pop(239.75)}>
				<T x={0} y={0} size={60} font="marker" color={C.blue}>
					Costco sells BELONGING
				</T>
			</G>
			<G x={interpolate(t, [240, 246], [300, 900], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})} y={1000}>
				<Penny walk={t > 240 && t < 246} mood="happy" />
				<G x={-250} y={-60} s={0.7}>
					<Cart />
				</G>
			</G>
			{after(242.24) && (
				<G x={1450} y={380} s={pop(242.24)}>
					<CasinoSign />
				</G>
			)}
			{after(246.4) && (
				<T x={1450} y={620} size={52} font="marker" color={C.gold} scale={pop(246.4)}>
					&quot;...you might win&quot;
				</T>
			)}
			{after(248.71) && (
				<G x={1450} y={760} s={pop(248.71)}>
					<T x={0} y={0} size={64} font="marker" color={C.red}>
						NEXT: CASINOS
					</T>
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- End screen
const S11 = VO2_SECONDS;
const EndScreen: React.FC = () => {
	const {pop} = useCue(S11);
	return (
		<Svg>
			<T x={960} y={110} size={84} font="marker" scale={pop(S11)}>
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
	[0.2, 'pop', 0.5],
	[1.0, 'flip', 0.5],
	[7.1, 'ding', 0.5],
	[10.5, 'scratch', 0.45],
	[14.4, 'whirr', 0.45],
	[18.87, 'pop', 0.5],
	[22.62, 'sting', 0.6],
	[28.5, 'whoosh', 0.4],
	[29.6, 'pop', 0.45],
	[31.5, 'chaching', 0.5],
	[34.5, 'whoosh', 0.4],
	[41.5, 'sting_dark', 0.45],
	[43.7, 'pop', 0.5],
	[45.6, 'rise', 0.35],
	[50.5, 'chaching', 0.5],
	[54.6, 'rise', 0.3],
	[62.8, 'pop', 0.55],
	[66.5, 'ding', 0.4],
	[69.4, 'stamp', 0.5],
	[71.5, 'coin', 0.4],
	[72.7, 'coin', 0.4],
	[73.9, 'coin', 0.4],
	[75.0, 'chaching', 0.45],
	[89.0, 'whirr', 0.35],
	[92.5, 'ding', 0.5],
	[99.53, 'sting', 0.5],
	[104.27, 'sting_dark', 0.45],
	[108.5, 'flip', 0.5],
	[114.2, 'ding', 0.45],
	[125.6, 'whoosh', 0.35],
	[127.6, 'pop', 0.5],
	[129.0, 'pop', 0.5],
	[130.6, 'pop', 0.5],
	[131.6, 'rewind', 0.35],
	[133.71, 'pop', 0.5],
	[136.0, 'tick', 0.45],
	[138.6, 'tick', 0.45],
	[141.0, 'beep', 0.5],
	[149.5, 'rise', 0.3],
	[151.0, 'chaching', 0.5],
	[159.47, 'pop', 0.5],
	[161.5, 'sting', 0.45],
	[166.0, 'coin', 0.4],
	[181.0, 'rise', 0.3],
	[186.0, 'chaching', 0.45],
	[190.15, 'whirr', 0.4],
	[192.17, 'pop', 0.45],
	[196.7, 'pop', 0.45],
	[200.09, 'pop', 0.45],
	[202.8, 'chaching', 0.5],
	[213.27, 'ding', 0.4],
	[223.2, 'tick', 0.5],
	[228.1, 'tick', 0.5],
	[233.1, 'tick', 0.5],
	[242.24, 'neon', 0.5],
	[248.71, 'sting_dark', 0.5],
	[VO2_SECONDS + 0.2, 'sting', 0.5],
];

const scenes: [number, number, React.FC][] = [
	[S1, S2, Hook],
	[S2, S3, Promise_],
	[S3, S4, Setup],
	[S4, S5, Machine],
	[S5, S6, Bait],
	[S6, S7, Math_],
	[S7, S8, Upgrade],
	[S8, S9, Reveal],
	[S9, S10, Advice],
	[S10, S11, Payoff],
	[S11, EP02_SECONDS, EndScreen],
];

export const Ep02: React.FC = () => {
	const {fps} = useVideoConfig();
	return (
		<AbsoluteFill style={{background: C.paper}}>
			<Audio src={staticFile('ep02_vo.mp3')} />
			<Soundtrack music="music_lofi_ep02.mp3" sfx={SFX} voEnd={VO2_SECONDS} dips={[99.53]} />
			{scenes.map(([a, b, Comp], i) => (
				<Sequence key={i} from={Math.round(a * fps)} durationInFrames={Math.round((b - a) * fps)}>
					<Comp />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
