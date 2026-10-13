import React from 'react';
import {interpolate} from 'remotion';
import {Penny} from '../lib/characters';
import {Card, Cash, Coin, Phone} from '../lib/props';
import {Cart} from '../lib/props2';
import {C, G, R, T, countUp} from '../lib/rough';
import {SfxCue} from '../lib/sound';
import {Bar, EndScreen, EngineLabels, Episode, Header, Label, MachineAndRules, Pie, Stat, Svg, TitleCard, useCue} from '../lib/kit';

/**
 * Episode 7: How Buy Now, Pay Later Makes Money.
 * Cue times are GLOBAL seconds from timing_ep07.json (exact Kokoro timings).
 */
export const VO7_SECONDS = 233.08;
export const EP07_SECONDS = VO7_SECONDS + 12;

// ---------------------------------------------------------------- Episode props
const Jacket: React.FC = () => (
	<g>
		<R s={{kind: 'polygon', pts: [[-90, -120], [-30, -140], [30, -140], [90, -120], [130, 60], [80, 70], [70, -20], [70, 140], [-70, 140], [-70, -20], [-80, 70], [-130, 60]]}} o={{fill: C.blue, fillStyle: 'solid'}} seed={7000} />
		<R s={{kind: 'line', x1: 0, y1: -130, x2: 0, y2: 140}} o={{strokeWidth: 4}} seed={7001} />
	</g>
);

/** The "Pay in 4" button. Origin centre. */
export const PayIn4: React.FC<{glow?: boolean}> = ({glow = false}) => (
	<g>
		<R s={{kind: 'rect', x: -300, y: -70, w: 600, h: 140}} o={{fill: C.ink, fillStyle: 'solid', stroke: glow ? C.yellow : C.ink, strokeWidth: glow ? 8 : 3}} seed={7010} />
		<T x={0} y={-12} size={56} font="marker" color={C.yellow}>
			PAY IN 4 x $33.75
		</T>
		<T x={0} y={42} size={30} color={C.white}>
			0% interest
		</T>
	</g>
);

const Shop: React.FC = () => (
	<g>
		<R s={{kind: 'rect', x: -170, y: -140, w: 340, h: 280}} o={{fill: C.white, fillStyle: 'solid'}} seed={7020} />
		<R s={{kind: 'polygon', pts: [[-200, -140], [200, -140], [170, -210], [-170, -210]]}} o={{fill: C.red, fillStyle: 'hachure'}} seed={7021} />
		<R s={{kind: 'rect', x: -50, y: 20, w: 100, h: 120}} o={{fill: C.brown, fillStyle: 'solid'}} seed={7022} />
		<T x={0} y={-60} size={46} font="marker">
			SHOP
		</T>
	</g>
);

const Lender: React.FC = () => (
	<g>
		<R s={{kind: 'rect', x: -150, y: -150, w: 300, h: 300}} o={{fill: C.ink, fillStyle: 'solid'}} seed={7030} />
		<T x={0} y={-30} size={50} font="marker" color={C.yellow}>
			PAY
		</T>
		<T x={0} y={40} size={50} font="marker" color={C.yellow}>
			LATER
		</T>
	</g>
);

const LoanCard: React.FC<{item: string; amt: string; color: string}> = ({item, amt, color}) => (
	<Card w={300} h={140} seed={item.length} fill={color}>
		<T x={0} y={-25} size={36}>
			{item}
		</T>
		<T x={0} y={35} size={48} font="marker" color={C.white} stroke={C.ink}>
			{amt}
		</T>
	</Card>
);

// ---------------------------------------------------------------- 1. Hook (0 – 19.0)
const S1 = 0;
const Hook: React.FC = () => {
	const {pop, after} = useCue(S1);
	return (
		<Svg>
			<G x={600} y={420} s={pop(0.2)}>
				<Jacket />
				<T x={0} y={210} size={70} font="marker" color={C.red}>
					$135
				</T>
			</G>
			<G x={340} y={1000} s={0.75}>
				<Penny mood={after(12.78) ? 'happy' : 'thinking'} look={1} />
			</G>
			{after(4.69) && (
				<G x={1300} y={360} s={pop(5)}>
					<PayIn4 glow={after(12.78)} />
				</G>
			)}
			{after(9.43) && (
				<T x={1300} y={560} size={54} font="marker" color={C.green} scale={pop(9.5)}>
					no interest
				</T>
			)}
			{after(11.05) && (
				<T x={1300} y={650} size={54} font="marker" color={C.green} scale={pop(11.1)}>
					no credit card
				</T>
			)}
			{after(14.1) && (
				<T x={1300} y={860} size={64} font="marker" color={C.red} scale={pop(15)}>
					so who makes money?
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 2. Promise (19.0 – 34.69)
const S2 = 19.0;
const Promise_: React.FC = () => {
	const {pop, t} = useCue(S2);
	if (t < 23.54) {
		return (
			<Svg>
				<G x={620} y={560} s={pop(19.1)}>
					<Card w={360} h={400} seed={2}>
						<R s={{kind: 'rect', x: -180, y: -200, w: 360, h: 90}} o={{fill: C.red, fillStyle: 'solid'}} seed={3} />
						<T x={0} y={40} size={110} font="marker">
							$$$
						</T>
					</Card>
				</G>
				<T x={1350} y={560} size={70} font="marker" color={C.blue} scale={pop(20)}>
					= EVERY MONTH
				</T>
			</Svg>
		);
	}
	if (t < 28.72) {
		return (
			<Svg>
				<TitleCard S={S2} at={23.54} subtitle="How buy now, pay later makes money" />
			</Svg>
		);
	}
	return (
		<Svg>
			<G x={960} y={380} s={pop(28.8)}>
				<PayIn4 />
			</G>
			<EngineLabels S={S2} at={30.5} labels={['THE SHOP', 'LATE FEES', 'THE HABIT']} y={760} />
		</Svg>
	);
};

// ---------------------------------------------------------------- 3. Growth (34.69 – 51.42)
const S3 = 34.69;
const Growth: React.FC = () => {
	const {p, pop, after} = useCue(S3);
	const h1 = 60 * p(37, 1);
	const h2 = 640 * p(42.7, 1.8);
	return (
		<Svg>
			<T x={960} y={110} size={64} font="marker" scale={pop(34.8)}>
				BNPL LOANS, 5 BIG LENDERS
			</T>
			<G x={0} y={0}>
				<R s={{kind: 'line', x1: 300, y1: 950, x2: 1300, y2: 950}} o={{strokeWidth: 6}} seed={10} />
				{h1 > 1 && <rect x={450} y={950 - h1} width={220} height={h1} fill={C.blue} stroke={C.ink} strokeWidth={3} />}
				<T x={560} y={1000} size={44}>
					2019
				</T>
				<T x={560} y={890 - h1} size={48} font="marker" scale={pop(38)}>
					16.8M
				</T>
				{after(42.64) && (
					<>
						<rect x={900} y={950 - h2} width={220} height={h2} fill={C.green} stroke={C.ink} strokeWidth={3} />
						<T x={1010} y={1000} size={44}>
							2021
						</T>
						<T x={1010} y={900 - h2} size={56} font="marker" color={C.green}>
							{countUp(p(42.7, 1.8), 180)}M
						</T>
					</>
				)}
			</G>
			{after(46.38) && (
				<G x={1560} y={560} s={pop(47)}>
					<Label text="10x in 2 years" w={460} size={52} fill={C.yellow} color={C.red} />
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 4. Engine 1: the shop pays (51.42 – 88.26)
const S4 = 51.42;
const ShopPays: React.FC = () => {
	const {p, pop, after, t} = useCue(S4);
	return (
		<Svg>
			<Header text="ENGINE #1: THE SHOP PAYS" at={51.42} S={S4} />
			{t < 75.69 ? (
				<>
					<G x={360} y={500} s={pop(55.1)}>
						<Lender />
					</G>
					<G x={1560} y={520} s={pop(55.5)}>
						<Shop />
					</G>
					{after(56.5) && (
						<G x={interpolate(p(56.5, 2), [0, 1], [500, 1350])} y={480} s={0.9}>
							<Cash thick />
						</G>
					)}
					{after(58.5) && (
						<G x={interpolate(p(58.6, 1.2), [0, 1], [1100, 450])} y={interpolate(p(58.6, 1.2), [0, 1], [500, 330])} s={0.5}>
							<Cash />
						</G>
					)}
					{after(63.41) && (
						<G x={960} y={780} s={pop(63.5)}>
							<T x={-420} y={0} size={44} anchor="start">
								shop fee: pay later
							</T>
							<G x={-20} y={-30}>
								<Bar w={500} v={p(64, 1) * (2.49 / 3)} />
							</G>
							<T x={600} y={4} size={56} font="marker" color={C.red}>
								2.49%
							</T>
							{after(70.75) && (
								<>
									<T x={-420} y={110} size={44} anchor="start">
										card fee (same study)
									</T>
									<G x={-20} y={80}>
										<Bar w={500} v={p(71, 1) * (0.67 / 3)} color={C.blue} />
									</G>
									<T x={540} y={114} size={56} font="marker" color={C.blue}>
										0.67%
									</T>
								</>
							)}
						</G>
					)}
				</>
			) : (
				<>
					<G x={560} y={820} s={pop(75.8) * 1.6}>
						<Cart>
							<R s={{kind: 'rect', x: -80, y: -110, w: 160, h: 100}} o={{fill: C.blue, fillStyle: 'solid'}} seed={20} />
						</Cart>
					</G>
					{after(77.91) && (
						<G x={1300} y={420} s={pop(78)}>
							<Label text="BIGGER BASKETS" w={620} size={64} fill={C.yellow} />
						</G>
					)}
					{after(82.6) && (
						<T x={1300} y={680} size={46} scale={pop(82.7)}>
							the lender sells the shop
						</T>
					)}
					{after(82.6) && (
						<T x={1300} y={760} size={50} font="marker" color={C.red} scale={pop(84)}>
							your willingness to spend
						</T>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 5. Engine 2: late fees (88.26 – 129.67)
const S5 = 88.26;
const Late: React.FC = () => {
	const {p, pop, after, t} = useCue(S5);
	const retries = Math.min(8, Math.floor(Math.max(0, t - 115.45) / 0.55) + (after(115.45) ? 1 : 0));
	return (
		<Svg>
			<Header text="ENGINE #2: LATE FEES" at={88.26} S={S5} />
			{t < 107.13 ? (
				<>
					{[0, 1, 2, 3].map((i) => {
						const late = i === 2 && after(96.41);
						return (
							<G key={i} x={420 + i * 360} y={380} s={pop(91.8 + i * 0.4)}>
								<Card w={280} h={180} seed={30 + i} fill={late ? C.red : C.white}>
									<T x={0} y={-40} size={36} color={late ? C.white : C.ink}>
										payment {i + 1}
									</T>
									<T x={0} y={30} size={52} font="marker" color={late ? C.white : C.green}>
										{late ? 'LATE' : 'PAID'}
									</T>
								</Card>
							</G>
						);
					})}
					{after(96.41) && (
						<G x={1140} y={600} s={pop(98)}>
							<Label text="LATE FEE: ~$7" w={460} size={52} fill={C.yellow} color={C.red} />
						</G>
					)}
					{after(101.49) && (
						<G x={960} y={880}>
							{Array.from({length: 10}).map((_, i) => (
								<G key={i} x={-540 + i * 120} y={0} s={0.3 * pop(101.6 + i * 0.08)}>
									<R s={{kind: 'circle', x: 0, y: -260, d: 120}} o={{fill: i === 6 ? C.red : C.shadow, fillStyle: 'solid'}} seed={40 + i} boil={false} />
									<R s={{kind: 'rect', x: -70, y: -200, w: 140, h: 200}} o={{fill: i === 6 ? C.red : C.shadow, fillStyle: 'solid'}} seed={50 + i} boil={false} />
								</G>
							))}
							<T x={0} y={60} size={44} font="marker" color={C.red} scale={pop(103)}>
								1 in 10 borrowers charged a late fee (2021)
							</T>
						</G>
					)}
				</>
			) : (
				<>
					<G x={440} y={560} s={pop(107.2)}>
						<Card w={460} h={300} seed={60}>
							<T x={0} y={-90} size={40}>
								Penny&apos;s debit card
							</T>
							<T x={0} y={20} size={90} font="marker" color={after(115.45) ? C.red : C.green}>
								{after(115.45) ? '$0.00' : '$41.20'}
							</T>
						</Card>
					</G>
					{after(115.45) && (
						<G x={1300} y={400}>
							{Array.from({length: retries}).map((_, i) => (
								<G key={i} x={(i % 4) * 170 - 255} y={Math.floor(i / 4) * 110} s={0.8}>
									<Label text="RETRY" w={190} size={36} fill={C.white} color={C.red} seed={70 + i} />
								</G>
							))}
						</G>
					)}
					{after(119.4) && (
						<T x={1300} y={680} size={50} font="marker" scale={pop(120)}>
							up to 8 tries for one payment
						</T>
					)}
					{after(125.03) && (
						<G x={1300} y={860} s={pop(125.1)}>
							<Label text="+ bank fees each time" w={640} size={48} fill={C.yellow} color={C.red} />
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 6. Engine 3: the habit (129.67 – 171.08)
const S6 = 129.67;
const loans = [
	{item: 'jacket', amt: '$33.75', color: C.blue, at: 133.1},
	{item: 'headphones', amt: '$20', color: C.green, at: 135.2},
	{item: 'groceries', amt: '$18', color: C.gold, at: 137.5},
	{item: 'concert', amt: '$45', color: C.red, at: 139.5},
];
const Habit: React.FC = () => {
	const {pop, after, t, p} = useCue(S6);
	return (
		<Svg>
			<Header text="ENGINE #3: THE HABIT" at={129.67} S={S6} />
			{t < 151.99 ? (
				<>
					<G x={330} y={600}>
						<Phone />
					</G>
					{loans.map((l, i) =>
						after(l.at) ? (
							<G key={l.item} x={330 + (i % 2) * 40 - 20} y={420 + i * 110} s={pop(l.at) * 0.7} r={(i % 2 ? 1 : -1) * 5}>
								<LoanCard item={l.item} amt={l.amt} color={l.color} />
							</G>
						) : null,
					)}
					{after(142.3) && (
						<G x={1250} y={420} s={pop(145)}>
							<Stat label="took out more than one loan (2022)" value="63%" w={800} />
						</G>
					)}
					{after(147) && (
						<G x={1250} y={700} s={pop(148.5)}>
							<Stat label="used more than one lender" value="1 IN 3" w={800} fill={C.white} />
						</G>
					)}
				</>
			) : (
				<>
					<G x={620} y={400} s={pop(152)}>
						<Stat label="BNPL loans in one year (2022)" value="277 MILLION" w={820} />
					</G>
					<G x={620} y={680} s={pop(157)}>
						<Stat label="worth" value="$34 BILLION" w={820} color={C.green} fill={C.white} />
					</G>
					{after(160.23) && (
						<G x={1460} y={540} s={pop(160.3)}>
							<Pie pct={0.66 * p(160.5, 1.2)} r={180} />
							<T x={0} y={250} size={42}>
								~2/3 to lower credit scores
							</T>
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 7. How it sneaks up (171.08 – 189.84)
const S7 = 171.08;
const Pile: React.FC = () => {
	const {pop, after} = useCue(S7);
	return (
		<Svg>
			<T x={960} y={110} size={64} font="marker" scale={pop(171.2)}>
				THE SAME WEEK...
			</T>
			{['MON', 'TUE', 'WED', 'THU', 'FRI'].map((d, i) => (
				<G key={d} x={360 + i * 300} y={480}>
					<Card w={260} h={360} seed={80 + i}>
						<T x={0} y={-140} size={40} font="marker">
							{d}
						</T>
					</Card>
				</G>
			))}
			{loans.map((l, i) =>
				after(179.18 + i * 0.6) ? (
					<G key={l.item} x={360 + [0, 1, 3, 4][i] * 300} y={480} s={pop(179.2 + i * 0.6) * 0.75}>
						<Coin />
						<T x={0} y={70} size={40} font="marker">
							{l.amt}
						</T>
					</G>
				) : null,
			)}
			{after(181) && (
				<G x={960} y={500} s={pop(181.5)}>
					<Label text="RENT DUE" w={240} size={44} fill={C.red} color={C.white} />
				</G>
			)}
			{after(187.46) && (
				<T x={960} y={870} size={64} font="marker" color={C.red} scale={pop(187.5)}>
					it&apos;s the pile that hurts
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 8. Machine (189.84 – 221.04)
const S8 = 189.84;
const Machine: React.FC = () => (
	<MachineAndRules
		S={S8}
		labels={['THE SHOP', 'LATE FEES', 'THE HABIT']}
		gearAt={[191.87, 194.51, 196.86]}
		punch={[{text: 'IT&apos;S STILL DEBT'.replace('&apos;', '’'), at: 199.31}]}
		rulesAt={205.05}
		banner="treat it like debt"
		rules={[
			{text: 'Only for things you could buy with cash.', at: 206.2},
			{text: 'Never more than one plan at a time.', at: 211.07},
			{text: 'Put every due date in your calendar.', at: 215.84},
		]}
	/>
);

// ---------------------------------------------------------------- 9. Payoff + bridge (221.04 – 233.08)
const S9 = 221.04;
const Payoff: React.FC = () => {
	const {pop, after} = useCue(S9);
	const signs = ['OVERDRAFT FEE', 'CHECK CASHING', 'PAYDAY LOANS'];
	return (
		<Svg>
			<T x={960} y={160} size={60} font="marker" scale={pop(221.1)}>
				small debts feel free...
			</T>
			{signs.map((s, i) =>
				after(224.11 + i * 1.2) ? (
					<G key={s} x={460 + i * 500} y={480} s={pop(224.2 + i * 1.2)} r={(i - 1) * 4}>
						<Label text={s} w={440} size={46} fill={i === 1 ? C.yellow : C.white} color={C.red} seed={90 + i} />
					</G>
				) : null,
			)}
			<G x={960} y={1000} s={0.75}>
				<Penny mood={after(224.11) ? 'worried' : 'happy'} />
			</G>
			{after(228.31) && (
				<T x={960} y={690} size={60} font="marker" color={C.red} scale={pop(228.4)}>
					NEXT: WHY BEING BROKE IS EXPENSIVE
				</T>
			)}
		</Svg>
	);
};

const End: React.FC = () => <EndScreen S={VO7_SECONDS} />;

const SFX: SfxCue[] = [
	[0.2, 'pop', 0.45],
	[5.0, 'ding', 0.45],
	[9.5, 'pop', 0.4],
	[11.1, 'pop', 0.4],
	[12.78, 'beep', 0.45],
	[15.0, 'sting_dark', 0.45],
	[19.1, 'flip', 0.4],
	[23.54, 'sting', 0.6],
	[28.8, 'whoosh', 0.4],
	[30.5, 'pop', 0.4],
	[31.2, 'pop', 0.4],
	[31.9, 'pop', 0.4],
	[34.8, 'pop', 0.45],
	[42.7, 'rise', 0.4],
	[47.0, 'chaching', 0.45],
	[51.42, 'pop', 0.5],
	[56.5, 'whoosh', 0.4],
	[58.6, 'coin', 0.45],
	[64.0, 'rise', 0.3],
	[71.0, 'pop', 0.4],
	[75.8, 'whoosh', 0.4],
	[78.0, 'chaching', 0.45],
	[84.0, 'sting_dark', 0.4],
	[88.26, 'pop', 0.5],
	[91.8, 'tick', 0.35],
	[92.2, 'tick', 0.35],
	[92.6, 'tick', 0.35],
	[93.0, 'tick', 0.35],
	[96.41, 'buzzer', 0.4],
	[98.0, 'coin', 0.45],
	[103.0, 'pop', 0.4],
	[107.2, 'flip', 0.4],
	[115.45, 'buzzer', 0.35],
	[116.0, 'beep', 0.3],
	[117.1, 'beep', 0.3],
	[118.2, 'beep', 0.3],
	[119.3, 'beep', 0.3],
	[125.1, 'coin', 0.45],
	[129.67, 'pop', 0.5],
	[133.1, 'plink', 0.4],
	[135.2, 'plink', 0.4],
	[137.5, 'plink', 0.4],
	[139.5, 'plink', 0.4],
	[145.0, 'pop', 0.45],
	[148.5, 'pop', 0.45],
	[152.0, 'chaching', 0.5],
	[157.0, 'chaching', 0.45],
	[160.3, 'sting_dark', 0.45],
	[171.2, 'flip', 0.4],
	[179.2, 'coin', 0.35],
	[179.8, 'coin', 0.35],
	[180.4, 'coin', 0.35],
	[181.0, 'coin', 0.35],
	[181.5, 'stamp', 0.5],
	[187.5, 'sting_dark', 0.45],
	[189.9, 'pop', 0.5],
	[191.87, 'whirr', 0.35],
	[194.51, 'whirr', 0.35],
	[196.86, 'whirr', 0.35],
	[199.31, 'sting_dark', 0.45],
	[205.05, 'pop', 0.45],
	[205.3, 'pop', 0.45],
	[210.2, 'pop', 0.45],
	[214.9, 'pop', 0.45],
	[207.7, 'tick', 0.5],
	[212.6, 'tick', 0.5],
	[217.3, 'tick', 0.5],
	[224.2, 'slap', 0.4],
	[225.4, 'slap', 0.4],
	[226.6, 'slap', 0.4],
	[228.4, 'sting_dark', 0.5],
];

export const Ep07: React.FC = () => (
	<Episode
		vo="ep07_vo.mp3"
		music="music_lofi_ep04.mp3"
		voEnd={VO7_SECONDS}
		total={EP07_SECONDS}
		sfx={SFX}
		dips={[14.1, 151.99]}
		scenes={[
			[S1, Hook],
			[S2, Promise_],
			[S3, Growth],
			[S4, ShopPays],
			[S5, Late],
			[S6, Habit],
			[S7, Pile],
			[S8, Machine],
			[S9, Payoff],
			[VO7_SECONDS, End],
		]}
	/>
);
