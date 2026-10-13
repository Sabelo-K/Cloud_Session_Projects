import React from 'react';
import {interpolate} from 'remotion';
import {Penny} from '../lib/characters';
import {Bubble, Card, Coin, Cross, Phone, Tick} from '../lib/props';
import {C, G, R, T, countUp} from '../lib/rough';
import {SfxCue} from '../lib/sound';
import {EndScreen, EngineLabels, Episode, Header, Label, MachineAndRules, Stat, Svg, TitleCard, money, useCue} from '../lib/kit';
import {Feed} from '../ep05/Ep05';

/**
 * Episode 6: The Subscription Trap, Explained.
 * Cue times are GLOBAL seconds from timing_ep06.json (exact Kokoro timings).
 */
export const VO6_SECONDS = 231.16;
export const EP06_SECONDS = VO6_SECONDS + 12;

// ---------------------------------------------------------------- Episode props
const CalendarPage: React.FC<{day: number; stamp?: number}> = ({day, stamp = 0}) => (
	<g>
		<R s={{kind: 'rect', x: -180, y: -200, w: 360, h: 400}} o={{fill: C.white, fillStyle: 'solid'}} seed={6000} />
		<R s={{kind: 'rect', x: -180, y: -200, w: 360, h: 90}} o={{fill: C.red, fillStyle: 'solid'}} seed={6001} />
		<T x={0} y={-152} size={44} font="marker" color={C.white}>
			DAY
		</T>
		<T x={0} y={40} size={170} font="marker">
			{day}
		</T>
		{stamp > 0 && (
			<g transform={`rotate(-14) scale(${1 + (1 - stamp) * 1.5})`} opacity={stamp}>
				<rect x={-170} y={60} width={340} height={90} fill="none" stroke={C.red} strokeWidth={8} />
				<text x={0} y={122} textAnchor="middle" fontFamily="Permanent Marker" fontSize={52} fill={C.red}>
					AUTO-RENEW
				</text>
			</g>
		)}
	</g>
);

const AppTile: React.FC<{price: string; color: string; grey?: boolean}> = ({price, color, grey = false}) => (
	<g opacity={grey ? 0.45 : 1}>
		<R s={{kind: 'rect', x: -80, y: -80, w: 160, h: 160}} o={{fill: grey ? C.shadow : color, fillStyle: 'solid'}} seed={6010} />
		<T x={0} y={130} size={44} font="marker" color={grey ? C.shadow : C.ink}>
			{price}
		</T>
	</g>
);

const Bucket: React.FC<{level: number}> = ({level}) => (
	<g>
		{level > 0 && <rect x={-150} y={-260 * level} width={300} height={260 * level} fill={C.gold} opacity={0.9} />}
		<R s={{kind: 'path', d: 'M -180 -300 L -150 0 L 150 0 L 180 -300'}} o={{strokeWidth: 6}} seed={6020} />
		<R s={{kind: 'rect', x: -120, y: -170, w: 240, h: 70}} o={{fill: C.white, fillStyle: 'solid'}} seed={6021} />
		<T x={0} y={-133} size={44} font="marker" color={C.red}>
			BREAKAGE
		</T>
	</g>
);

const Popup: React.FC<{text: string; seed: number}> = ({text, seed}) => (
	<Card w={560} h={130} seed={seed}>
		<R s={{kind: 'rect', x: -280, y: -65, w: 560, h: 30}} o={{fill: C.blue, fillStyle: 'solid'}} seed={seed + 50} boil={false} />
		<T x={0} y={18} size={44} font="marker">
			{text}
		</T>
	</Card>
);

const Gavel: React.FC<{hit: number}> = ({hit}) => (
	<g transform={`rotate(${-30 + hit * 30})`}>
		<R s={{kind: 'line', x1: 0, y1: 0, x2: 220, y2: 0}} o={{strokeWidth: 16, stroke: C.brown}} seed={6030} />
		<R s={{kind: 'rect', x: 200, y: -50, w: 80, h: 100}} o={{fill: C.brown, fillStyle: 'solid'}} seed={6031} />
	</g>
);

// ---------------------------------------------------------------- 1. Hook (0 – 17.63)
const S1 = 0;
const Hook: React.FC = () => {
	const {p, pop, after} = useCue(S1);
	return (
		<Svg>
			<G x={360} y={1000} s={0.85}>
				<Penny mood={after(9.98) ? 'shocked' : 'confident'} look={1} />
			</G>
			<G x={520} y={420} s={pop(0.4)}>
				<Bubble w={460} h={220} tail="left">
					<T x={0} y={-30} size={40}>
						subscriptions?
					</T>
					<T x={0} y={40} size={64} font="marker" color={C.green}>
						~$86/mo
					</T>
				</Bubble>
			</G>
			{after(9.98) && (
				<G x={1350} y={180}>
					<R s={{kind: 'rect', x: -260, y: 0, w: 520, h: 780 * p(10, 2)}} o={{fill: C.white, fillStyle: 'solid'}} seed={1} boil={false} />
					{['streaming', 'music', 'cloud', 'gym', 'apps', 'news'].map((l, i) =>
						80 + i * 90 < 780 * p(10, 2) ? (
							<T key={l} x={-200} y={60 + i * 90} size={40} anchor="start">
								{l}
							</T>
						) : null,
					)}
					{after(12) && (
						<T x={0} y={680} size={110} font="marker" color={C.red} scale={pop(12.2)}>
							$219/mo
						</T>
					)}
				</G>
			)}
			{after(14.98) && (
				<T x={760} y={800} size={70} font="marker" color={C.red} scale={pop(15)}>
					2.5x more!
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 2. Promise (17.63 – 30.42)
const S2 = 17.63;
const Promise_: React.FC = () => {
	const {pop, t} = useCue(S2);
	if (t < 21.07) {
		return (
			<Svg>
				<G x={620} y={560} s={pop(17.7)}>
					<Phone>
						<Feed scroll={t * 60} />
					</Phone>
				</G>
				<T x={1350} y={540} size={80} font="marker" color={C.blue} scale={pop(18.5)}>
					= YOUR TIME
				</T>
			</Svg>
		);
	}
	if (t < 25.8) {
		return (
			<Svg>
				<TitleCard S={S2} at={21.07} subtitle="The subscription trap, explained" />
			</Svg>
		);
	}
	return (
		<Svg>
			<G x={960} y={380} s={pop(25.85) * 0.75}>
				<CalendarPage day={30} />
			</G>
			<EngineLabels S={S2} at={27} labels={['FREE TRIAL', 'FORGET', 'FRICTION']} y={850} />
		</Svg>
	);
};

// ---------------------------------------------------------------- 3. The gap (30.42 – 45.36)
const S3 = 30.42;
const Gap: React.FC = () => {
	const {p, pop, after} = useCue(S3);
	return (
		<Svg>
			<G x={560} y={420} s={pop(30.5)}>
				<Stat label="the gap, every month" value="$133" w={560} />
			</G>
			{after(34.39) && (
				<>
					<T x={960} y={420} size={90} font="marker" scale={pop(35)}>
						x 12
					</T>
					<G x={1400} y={420} s={pop(36.5)}>
						<Stat label="every year" value={money(countUp(p(36.5, 1.5), 1596))} w={560} />
					</G>
				</>
			)}
			{after(39.81) && (
				<G x={960} y={1000} s={0.8}>
					<Penny mood="shocked" />
				</G>
			)}
			{after(39.81) && (
				<T x={960} y={630} size={52} font="marker" color={C.red} scale={pop(41)}>
					...and they know it
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 4. Engine 1: free trial (45.36 – 80.8)
const S4 = 45.36;
const Trial: React.FC = () => {
	const {p, pop, after, t} = useCue(S4);
	return (
		<Svg>
			<Header text="ENGINE #1: THE FREE TRIAL" at={45.36} S={S4} />
			{t < 63.25 ? (
				<>
					<G x={760} y={450} s={pop(49)}>
						<R s={{kind: 'rect', x: -300, y: -90, w: 600, h: 180}} o={{fill: C.green, fillStyle: 'solid'}} seed={2} />
						<T x={0} y={6} size={90} font="marker" color={C.white}>
							TRY FREE!
						</T>
						<T x={0} y={140} size={30} color={C.shadow}>
							then $14.99/month
						</T>
					</G>
					{after(51.14) && (
						<G x={1450} y={460} s={pop(52)}>
							<Card w={440} h={260} seed={3} fill={C.blue}>
								<T x={0} y={-60} size={38} font="marker" color={C.white}>
									CARD NUMBER
								</T>
								<T x={0} y={30} size={44} color={C.white}>
									{'**** '.repeat(3)}
									{String(1000 + Math.floor(p(52.5, 2) * 234)).slice(-4)}
								</T>
							</Card>
						</G>
					)}
					<G x={360} y={1010} s={0.7}>
						<Penny mood="happy" look={1} />
					</G>
					{after(56.93) && (
						<G x={1150} y={840} s={pop(57)}>
							<Label text="the bet: you forget the date" w={900} size={50} fill={C.yellow} color={C.red} />
						</G>
					)}
				</>
			) : (
				<>
					<G x={560} y={560} s={pop(63.3)}>
						<CalendarPage day={after(64) ? 30 : 29} stamp={p(66.05, 0.4)} />
					</G>
					{after(68.84) && (
						<G x={1350} y={430} s={pop(70)}>
							<Card w={680} h={300} seed={4}>
								<T x={0} y={-90} size={40} font="marker">
									NO BOX. NO REMINDER.
								</T>
								<T x={0} y={10} size={34} color={C.shadow}>
									coffee ........ $4.50
								</T>
								<T x={0} y={70} size={34} color={C.red}>
									STREAMFLIX ... $14.99
								</T>
							</Card>
						</G>
					)}
					{after(66.05) && (
						<G x={1350} y={interpolate(p(66.5, 1.5), [0, 1], [700, 980])} s={0.9}>
							<Coin />
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 5. Engine 2: forgetting (80.8 – 118.9)
const S5 = 80.8;
const apps = [
	{price: '$9.99', color: C.red, at: 87.3},
	{price: '$4.99', color: C.blue, at: 87.8},
	{price: '$14.99', color: C.green, at: 89.2},
	{price: '$6.99', color: C.gold, at: 89.7},
	{price: '$12.99', color: '#8E5BC6', at: 90.2},
];
const Forget: React.FC = () => {
	const {p, pop, after, t} = useCue(S5);
	return (
		<Svg>
			<Header text="ENGINE #2: FORGETTING" at={80.8} S={S5} />
			{t < 102.74 ? (
				<>
					{apps.map((a, i) =>
						after(a.at) ? (
							<G key={a.price} x={360 + i * 300} y={400} s={pop(a.at)}>
								<AppTile price={a.price} color={a.color} grey={after(94.43) && i % 2 === 0} />
							</G>
						) : null,
					)}
					{after(90.97) && (
						<T x={960} y={640} size={54} font="marker" scale={pop(91)}>
							too small to feel
						</T>
					)}
					{after(94.43) && (
						<G x={960} y={860} s={pop(97)}>
							<Stat label="forgot they were still paying" value="42%" w={720} />
						</G>
					)}
				</>
			) : (
				<>
					<G x={760} y={900} s={pop(102.8)}>
						<Bucket level={p(107.6, 8)} />
					</G>
					{[0, 1, 2].map((i) => {
						const k = ((t - 104 + i * 0.9) % 2.7) / 2.7;
						return t > 104 ? (
							<G key={i} x={interpolate(k, [0, 1], [300 + i * 120, 760])} y={interpolate(k, [0, 1], [250, 620])} s={0.55}>
								<AppTile price={['$9.99', '$14.99', '$12.99'][i]} color={C.shadow} grey />
							</G>
						) : null;
					})}
					{after(112.04) && (
						<G x={1450} y={460} s={pop(112.1)}>
							<Label text="almost pure profit" w={620} size={52} fill={C.yellow} color={C.green} />
						</G>
					)}
					{after(115.03) && (
						<T x={1450} y={640} size={44} scale={pop(115.1)}>
							costs nothing to serve
						</T>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 6. Engine 3: friction (118.9 – 182.91)
const S6 = 118.9;
const popups = [
	{text: 'Are you sure?', at: 127.3},
	{text: 'Wait! 50% off!', at: 128.77},
	{text: 'Tell us why...', at: 130.54},
	{text: 'Are you REALLY sure?', at: 132.0},
];
const Friction: React.FC = () => {
	const {p, pop, after, t} = useCue(S6);
	const part = t < 139.02 ? 1 : t < 162.22 ? 2 : 3;
	return (
		<Svg>
			<Header text="ENGINE #3: FRICTION" at={118.9} S={S6} />
			{part === 1 && (
				<>
					<G x={420} y={420} s={pop(122.2)}>
						<R s={{kind: 'rect', x: -220, y: -80, w: 440, h: 160}} o={{fill: C.green, fillStyle: 'solid'}} seed={5} />
						<T x={0} y={6} size={70} font="marker" color={C.white}>
							SIGN UP
						</T>
						<T x={0} y={140} size={40}>
							1 click
						</T>
					</G>
					{after(124.61) && (
						<G x={420} y={820} s={pop(124.7)}>
							<R s={{kind: 'rect', x: -180, y: -60, w: 360, h: 120}} o={{fill: C.shadow, fillStyle: 'solid'}} seed={6} />
							<T x={0} y={6} size={54} font="marker">
								cancel
							</T>
						</G>
					)}
					{popups.map((pp, i) =>
						after(pp.at) ? (
							<G key={pp.text} x={1150 + i * 60} y={330 + i * 160} s={pop(pp.at)}>
								<Popup text={pp.text} seed={10 + i} />
							</G>
						) : null,
					)}
				</>
			)}
			{part === 2 && (
				<>
					<G x={400} y={520} s={pop(139.1)}>
						<Gavel hit={Math.abs(Math.sin(Math.max(0, t - 141) * 4)) * (t < 143 ? 1 : 0)} />
					</G>
					{after(141.29) && (
						<G x={1250} y={380} s={pop(146)}>
							<Stat label="Amazon settles FTC Prime case, 2025" value="$2.5 BILLION" w={880} />
						</G>
					)}
					{after(153.7) && (
						<G x={1250} y={720} s={pop(157)}>
							<T x={0} y={0} size={56}>
								cancel flow nickname:
							</T>
							<T x={0} y={110} size={130} font="marker" color={C.red}>
								&quot;ILIAD&quot;
							</T>
						</G>
					)}
					{after(159.5) && (
						<T x={1250} y={980} size={44} color={C.shadow} scale={pop(159.6)}>
							(a famously long war)
						</T>
					)}
				</>
			)}
			{part === 3 && (
				<>
					<G x={960} y={500} s={pop(165)}>
						<Card w={1150} h={240} seed={20}>
							<T x={0} y={-40} size={66} font="marker">
								CLICK-TO-CANCEL RULE
							</T>
							<T x={0} y={50} size={40}>
								leaving = as easy as joining (2024)
							</T>
						</Card>
					</G>
					{after(172.72) && (
						<g transform={`translate(960 520) rotate(-10) scale(${1 + (1 - p(176, 0.3)) * 1.4})`} opacity={p(176, 0.3)}>
							<rect x={-300} y={-70} width={600} height={140} fill="none" stroke={C.red} strokeWidth={12} />
							<text x={0} y={32} textAnchor="middle" fontFamily="Permanent Marker" fontSize={96} fill={C.red}>
								VACATED
							</text>
						</g>
					)}
					{after(179.1) && (
						<T x={960} y={850} size={56} font="marker" color={C.red} scale={pop(179.2)}>
							the maze is still there
						</T>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 7. Machine (182.91 – 217.26)
const S7 = 182.91;
const Machine: React.FC = () => (
	<MachineAndRules
		S={S7}
		labels={['FREE TRIAL', 'FORGET', 'FRICTION']}
		gearAt={[184.93, 187.62, 190.18]}
		punch={[
			{text: 'they profit when you stop paying attention', at: 193.38},
			{text: 'SO PAY ATTENTION', at: 198.07},
		]}
		rulesAt={199.89}
		banner="audit your subscriptions"
		rules={[
			{text: 'Set a reminder before a trial ends.', at: 201.04},
			{text: 'List every recurring charge each quarter.', at: 206.76},
			{text: 'Wouldn’t join today? Cancel today.', at: 213.26},
		]}
	/>
);

// ---------------------------------------------------------------- 8. Payoff + bridge (217.26 – 231.16)
const S8 = 217.26;
const Payoff: React.FC = () => {
	const {p, pop, after, t} = useCue(S8);
	return (
		<Svg>
			{t < 220.4 ? (
				<>
					{[0, 1, 2].map((i) => (
						<G key={i} x={500 + i * 460} y={420} s={pop(217.4 + i * 0.6)}>
							<AppTile price="CANCELLED" color={C.shadow} grey={after(217.8 + i * 0.6)} />
							{after(217.8 + i * 0.6) && (
								<G x={0} y={0}>
									<Cross draw={p(217.8 + i * 0.6, 0.3)} size={60} />
								</G>
							)}
						</G>
					))}
					<G x={960} y={1000} s={0.8}>
						<Penny mood="happy" />
					</G>
				</>
			) : (
				<>
					<G x={1100} y={460} s={pop(220.5)}>
						<Card w={760} h={420} seed={30}>
							<T x={0} y={-150} size={44}>
								CHECKOUT: $135
							</T>
							<R s={{kind: 'rect', x: -300, y: -60, w: 600, h: 140}} o={{fill: C.ink, fillStyle: 'solid'}} seed={31} />
							<T x={0} y={14} size={60} font="marker" color={C.yellow}>
								PAY IN 4
							</T>
							<T x={0} y={150} size={48} font="marker" color={C.green}>
								interest-free!
							</T>
						</Card>
					</G>
					<G x={420} y={1000} s={0.8}>
						<Penny mood="thinking" look={1} />
					</G>
					{after(226.29) && (
						<T x={1100} y={900} size={60} font="marker" color={C.red} scale={pop(226.3)}>
							NEXT: BUY NOW, PAY LATER
						</T>
					)}
				</>
			)}
		</Svg>
	);
};

const End: React.FC = () => <EndScreen S={VO6_SECONDS} />;

const SFX: SfxCue[] = [
	[0.4, 'pop', 0.45],
	[10.0, 'flip', 0.4],
	[12.2, 'sting_dark', 0.45],
	[15.0, 'buzzer', 0.35],
	[17.7, 'whoosh', 0.4],
	[21.07, 'sting', 0.6],
	[25.85, 'flip', 0.4],
	[27.0, 'pop', 0.4],
	[27.7, 'pop', 0.4],
	[28.4, 'pop', 0.4],
	[30.5, 'pop', 0.45],
	[36.5, 'chaching', 0.5],
	[41.0, 'sting_dark', 0.4],
	[45.36, 'pop', 0.5],
	[49.0, 'ding', 0.45],
	[52.0, 'beep', 0.45],
	[57.0, 'pop', 0.4],
	[63.3, 'flip', 0.4],
	[66.05, 'stamp', 0.6],
	[66.6, 'coin', 0.45],
	[70.0, 'pop', 0.4],
	[80.8, 'pop', 0.5],
	[87.3, 'coin', 0.35],
	[87.8, 'coin', 0.35],
	[89.2, 'coin', 0.35],
	[89.7, 'coin', 0.35],
	[90.2, 'coin', 0.35],
	[97.0, 'sting_dark', 0.45],
	[102.8, 'whoosh', 0.4],
	[104.5, 'coin', 0.3],
	[107.2, 'coin', 0.3],
	[109.9, 'coin', 0.3],
	[112.1, 'chaching', 0.45],
	[118.9, 'pop', 0.5],
	[122.2, 'ding', 0.4],
	[127.3, 'bloop', 0.4],
	[128.77, 'bloop', 0.4],
	[130.54, 'bloop', 0.4],
	[132.0, 'bloop', 0.4],
	[141.3, 'slap', 0.5],
	[146.0, 'chaching', 0.5],
	[157.0, 'sting', 0.5],
	[165.0, 'pop', 0.45],
	[176.0, 'stamp', 0.6],
	[183.0, 'pop', 0.5],
	[184.93, 'whirr', 0.35],
	[187.62, 'whirr', 0.35],
	[190.18, 'whirr', 0.35],
	[198.07, 'sting_dark', 0.45],
	[199.9, 'pop', 0.45],
	[200.2, 'pop', 0.45],
	[205.9, 'pop', 0.45],
	[212.4, 'pop', 0.45],
	[202.5, 'tick', 0.5],
	[208.3, 'tick', 0.5],
	[214.8, 'tick', 0.5],
	[217.8, 'scratch', 0.35],
	[218.4, 'scratch', 0.35],
	[219.0, 'scratch', 0.35],
	[220.5, 'ding', 0.45],
	[226.3, 'sting_dark', 0.5],
];

export const Ep06: React.FC = () => (
	<Episode
		vo="ep06_vo.mp3"
		music="music_lofi_ep04.mp3"
		voEnd={VO6_SECONDS}
		total={EP06_SECONDS}
		sfx={SFX}
		dips={[9.98, 153.7]}
		scenes={[
			[S1, Hook],
			[S2, Promise_],
			[S3, Gap],
			[S4, Trial],
			[S5, Forget],
			[S6, Friction],
			[S7, Machine],
			[S8, Payoff],
			[VO6_SECONDS, End],
		]}
	/>
);
