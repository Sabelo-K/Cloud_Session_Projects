import React from 'react';
import {Penny} from '../lib/characters';
import {Card, Cash, Coin, Phone} from '../lib/props';
import {C, G, R, T, countUp} from '../lib/rough';
import {SfxCue} from '../lib/sound';
import {EndScreen, EngineLabels, Episode, Header, Label, MachineAndRules, Stat, Svg, TitleCard, useCue} from '../lib/kit';

/**
 * Episode 8: Why Being Broke Is Expensive.
 * Cue times are GLOBAL seconds from timing_ep08.json (exact Kokoro timings).
 */
export const VO8_SECONDS = 241.7;
export const EP08_SECONDS = VO8_SECONDS + 12;

// ---------------------------------------------------------------- Episode props
/** A bank receipt line. Origin centre. */
const Receipt: React.FC<{rows: [string, string, string?][]; w?: number}> = ({rows, w = 620}) => (
	<Card w={w} h={90 + rows.length * 80} seed={8000} fill={C.white}>
		{rows.map(([a, b, col], i) => (
			<React.Fragment key={a}>
				<T x={-w / 2 + 40} y={-((rows.length - 1) * 40) + i * 80} size={44} anchor="start">
					{a}
				</T>
				<T x={w / 2 - 40} y={-((rows.length - 1) * 40) + i * 80} size={52} font="marker" anchor="end" color={col ?? C.ink}>
					{b}
				</T>
			</React.Fragment>
		))}
	</Card>
);

const Boot: React.FC<{good?: boolean; worn?: number}> = ({good = false, worn = 0}) => (
	<g>
		<R
			s={{kind: 'polygon', pts: [[-40, -150], [40, -150], [40, 20], [130, 50], [130, 100], [-40, 100]]}}
			o={{fill: good ? C.brown : C.shadow, fillStyle: good ? 'solid' : 'hachure'}}
			seed={good ? 8010 : 8011}
		/>
		{worn > 0 && <R s={{kind: 'line', x1: 0, y1: 100, x2: 50 + worn * 40, y2: 60}} o={{stroke: C.red, strokeWidth: 6}} seed={8012} />}
	</g>
);

// ---------------------------------------------------------------- 1. Hook (0 – 19.12)
const S1 = 0;
const Hook: React.FC = () => {
	const {pop, after} = useCue(S1);
	return (
		<Svg>
			<G x={360} y={1000} s={0.8}>
				<Penny mood={after(5.99) ? 'shocked' : 'happy'} look={1} />
			</G>
			<G x={1150} y={430} s={pop(0.2)}>
				<Receipt
					rows={[
						['lunch', '$24'],
						...(after(3.26) ? ([['balance', '-$3', C.red]] as [string, string, string][]) : []),
						...(after(5.99) ? ([['overdraft fee', '$34', C.red]] as [string, string, string][]) : []),
					]}
				/>
			</G>
			{after(11.05) && (
				<T x={1150} y={720} size={50} color={C.green} scale={pop(11.1)}>
					paid back 3 days later
				</T>
			)}
			{after(13.72) && (
				<G x={1150} y={880} s={pop(14.5)}>
					<Label text="= ~17,000% A YEAR" w={720} size={60} fill={C.yellow} color={C.red} />
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 2. Promise (19.12 – 30.65)
const S2 = 19.12;
const Promise_: React.FC = () => {
	const {pop, t} = useCue(S2);
	if (t < 23.11) {
		return (
			<Svg>
				<T x={960} y={420} size={80} font="marker" scale={pop(19.2)}>
					THE MOST FEES...
				</T>
				<T x={960} y={600} size={80} font="marker" color={C.red} scale={pop(20.8)}>
					...FROM THE LEAST MONEY
				</T>
			</Svg>
		);
	}
	if (t < 25.0) {
		return (
			<Svg>
				<TitleCard S={S2} at={23.11} subtitle="Why being broke is expensive" />
			</Svg>
		);
	}
	return (
		<Svg>
			<G x={960} y={400} s={pop(25.0) * 2.5}>
				<Coin />
				<T x={0} y={-70} size={30} font="marker">
					$0.00
				</T>
			</G>
			<EngineLabels S={S2} at={25.01} labels={['OVERDRAFT', 'FAST CASH', 'NO BANK']} y={760} />
		</Svg>
	);
};

// ---------------------------------------------------------------- 3. Overdraft (30.65 – 86.66)
const S3 = 30.65;
const Overdraft: React.FC = () => {
	const {pop, p, after, t} = useCue(S3);
	if (t < 55.48) {
		return (
			<Svg>
				<Header text="ENGINE #1: OVERDRAFT" at={30.7} S={S3} />
				{after(34.13) && (
					<G x={520} y={430} s={pop(34.2)}>
						<Stat label="bank covers you, then..." value="FEE" w={600} />
					</G>
				)}
				{after(40.0) && (
					<>
						<G x={1300} y={340} s={pop(40.2)}>
							<Stat label="typical fee" value="$34" w={520} />
						</G>
						<G x={1300} y={580} s={pop(43.5)}>
							<Stat label="for purchases of" value="$24 or less" w={520} size={70} fill={C.white} color={C.ink} seed={2} />
						</G>
					</>
				)}
				{after(49.81) && (
					<G x={960} y={880} s={pop(50)}>
						<Label text="most paid back within 3 days" w={1000} size={52} fill={C.yellow} />
					</G>
				)}
			</Svg>
		);
	}
	if (t < 76.78) {
		const n = 25;
		return (
			<Svg>
				<Header text="NOT SPREAD EVENLY" at={55.5} S={S3} />
				<G x={460} y={260}>
					{Array.from({length: n}).map((_, i) => {
						const hot = i < 2;
						return (
							<G key={i} x={(i % 5) * 110} y={Math.floor(i / 5) * 110} s={pop(56 + i * 0.03)}>
								<R s={{kind: 'circle', x: 0, y: 0, d: 80}} o={{fill: hot && after(57.76) ? C.red : C.white, fillStyle: 'solid'}} seed={8100 + i} boil={false} />
							</G>
						);
					})}
				</G>
				{after(57.76) && (
					<T x={1400} y={420} size={60} font="marker" color={C.red} scale={pop(58)}>
						~8% of accounts
					</T>
				)}
				{after(59.5) && (
					<T x={1400} y={510} size={48} scale={pop(59.6)}>
						pay most of the fees
					</T>
				)}
				{after(65.48) && (
					<G x={1400} y={760} s={pop(65.6)}>
						<Stat label="overdraft + bounced fees, 2023" value={`$${(5.8 * p(66, 1.4)).toFixed(1)} BILLION`} w={720} size={74} />
					</G>
				)}
			</Svg>
		);
	}
	return (
		<Svg>
			<Header text="AND THAT'S AFTER THE CUTS" at={76.8} S={S3} />
			<G x={560} y={900}>
				<R s={{kind: 'line', x1: -260, y1: 0, x2: 1060, y2: 0}} o={{strokeWidth: 6}} seed={8200} />
				{after(79.57) && (
					<>
						<rect x={-150} y={-560 * p(79.7, 1)} width={240} height={560 * p(79.7, 1)} fill={C.red} stroke={C.ink} strokeWidth={3} />
						<T x={-30} y={-610} size={56} font="marker" color={C.red} scale={pop(80.5)}>
							$11-12B / yr
						</T>
						<T x={-30} y={50} size={44}>
							before 2020
						</T>
					</>
				)}
				<rect x={600} y={-280 * p(77, 1)} width={240} height={280 * p(77, 1)} fill={C.yellow} stroke={C.ink} strokeWidth={3} />
				<T x={720} y={-330} size={56} font="marker" scale={pop(77.5)}>
					$5.8B
				</T>
				<T x={720} y={50} size={44}>
					2023
				</T>
			</G>
		</Svg>
	);
};

// ---------------------------------------------------------------- 4. Fast cash (86.66 – 126.92)
const S4 = 86.66;
const FastCash: React.FC = () => {
	const {pop, p, after, t} = useCue(S4);
	if (t < 109.5) {
		return (
			<Svg>
				<Header text="ENGINE #2: FAST CASH" at={86.7} S={S4} />
				<G x={500} y={500} s={pop(87.5)}>
					<Card w={420} h={300} seed={3} fill={C.white}>
						<T x={0} y={-80} size={50} font="marker">
							RENT DUE
						</T>
						<T x={0} y={20} size={44} color={C.red}>
							before payday
						</T>
						<T x={0} y={100} size={40} color={C.shadow}>
							savings: $0
						</T>
					</Card>
				</G>
				{after(90.18) && (
					<G x={1300} y={420} s={pop(90.3)}>
						<Card w={620} h={260} seed={4} fill={C.yellow}>
							<T x={0} y={-60} size={54} font="marker">
								PAYDAY LOAN
							</T>
							{after(97.84) && (
								<T x={0} y={30} size={50} color={C.red} scale={pop(98)}>
									$15 per $100 borrowed
								</T>
							)}
							{after(102.0) && (
								<T x={0} y={95} size={44} scale={pop(102.1)}>
									due in 2 weeks
								</T>
							)}
						</Card>
					</G>
				)}
				{after(105.4) && (
					<T x={1300} y={720} size={56} font="marker" color={C.green} scale={pop(105.5)}>
						15%... not outrageous?
					</T>
				)}
			</Svg>
		);
	}
	if (t < 114.02) {
		return (
			<Svg>
				<Header text="STRETCHED ACROSS A YEAR" at={109.55} S={S4} />
				<T x={960} y={520} size={200} font="marker" color={C.red} scale={pop(110)}>
					{countUp(p(110.2, 2), 391)}%
				</T>
				<T x={960} y={720} size={52}>
					(about 400% APR)
				</T>
			</Svg>
		);
	}
	// rollover loop
	const loops = Math.min(4, Math.floor((t - 114.5) / 1.6) + 1);
	return (
		<Svg>
			<Header text="CAN'T REPAY? ROLL IT OVER" at={114.1} S={S4} />
			{Array.from({length: Math.max(0, loops)}).map((_, i) => (
				<G key={i} x={360 + i * 400} y={480} s={pop(114.5 + i * 1.6)}>
					<Card w={320} h={180} seed={10 + i} fill={i === 0 ? C.white : C.yellow}>
						<T x={0} y={-35} size={40}>
							{i === 0 ? 'loan' : `rollover ${i}`}
						</T>
						<T x={0} y={35} size={56} font="marker" color={C.red}>
							+$15
						</T>
					</Card>
				</G>
			))}
			{after(121.17) && (
				<G x={960} y={820} s={pop(121.3)}>
					<Label text="the gap gets wider" w={760} size={60} fill={C.red} color={C.white} />
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 5. No bank (126.92 – 162.69)
const S5 = 126.92;
const NoBank: React.FC = () => {
	const {pop, after, t} = useCue(S5);
	if (t < 143.72) {
		return (
			<Svg>
				<Header text="ENGINE #3: NO BANK" at={127} S={S5} />
				{after(131.06) && (
					<G x={960} y={380} s={pop(131.2)}>
						<Stat label="US households with no bank account (2023)" value="5.6 MILLION" w={1000} />
					</G>
				)}
				{after(137.67) && (
					<G x={960} y={720} s={pop(137.8)}>
						<Card w={1200} h={200} seed={5} fill={C.white}>
							<T x={0} y={-45} size={40}>
								most common reason
							</T>
							<T x={0} y={35} size={56} font="marker" color={C.red}>
								CAN&apos;T MEET MINIMUM BALANCE
							</T>
						</Card>
					</G>
				)}
			</Svg>
		);
	}
	const fees = [
		{t: 148.03, text: 'cash a paycheck'},
		{t: 150.46, text: 'pay a bill'},
		{t: 152.4, text: 'load a prepaid card'},
	];
	return (
		<Svg>
			<Header text="PAYING TO USE YOUR OWN MONEY" at={143.8} S={S5} />
			<G x={300} y={1000} s={0.75}>
				<Penny mood={after(156.99) ? 'worried' : 'neutral'} />
			</G>
			<G x={620} y={420} s={pop(144.5)}>
				<Cash thick />
			</G>
			{fees.map((f, i) =>
				after(f.t) ? (
					<G key={f.text} x={1250} y={300 + i * 170} s={pop(f.t + 0.1)}>
						<Card w={720} h={130} seed={20 + i} fill={C.white}>
							<T x={-320} y={4} size={46} anchor="start">
								fee to {f.text}
							</T>
							<T x={300} y={4} size={56} font="marker" color={C.red} anchor="end">
								-$
							</T>
						</Card>
					</G>
				) : null,
			)}
			{after(156.99) && (
				<G x={1100} y={880} s={pop(157.1)}>
					<Label text="A TAX ON BEING BROKE" w={900} size={66} fill={C.yellow} color={C.red} />
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 6. Boots theory (162.69 – 188.3)
const S6 = 162.69;
const Boots: React.FC = () => {
	const {pop, after, t} = useCue(S6);
	if (t < 167.58) {
		return (
			<Svg>
				<T x={960} y={380} size={60} scale={pop(162.8)}>
					Terry Pratchett&apos;s
				</T>
				{after(166.0) && (
					<T x={960} y={540} size={130} font="marker" color={C.brown} scale={pop(166.1)}>
						BOOTS THEORY
					</T>
				)}
			</Svg>
		);
	}
	if (t < 181.17) {
		const pairs = after(172.21) ? Math.min(5, Math.floor((t - 174.5) / 1.3) + 1) : 0;
		return (
			<Svg>
				<R s={{kind: 'line', x1: 960, y1: 200, x2: 960, y2: 900}} o={{strokeWidth: 4, stroke: C.shadow}} seed={8300} boil={false} />
				<G x={480} y={460} s={pop(167.7)}>
					<Boot good />
				</G>
				<T x={480} y={680} size={52} font="marker" scale={pop(168.5)}>
					1 good pair: $50
				</T>
				<T x={480} y={760} size={44} color={C.green} scale={pop(170)}>
					lasts for years
				</T>
				{after(172.21) && (
					<>
						{Array.from({length: Math.max(0, pairs)}).map((_, i) => (
							<G key={i} x={1120 + (i % 5) * 150} y={460} s={pop(174.5 + i * 1.3) * 0.6}>
								<Boot worn={i < pairs - 1 ? 1 : 0} />
							</G>
						))}
						<T x={1440} y={680} size={52} font="marker" color={C.red} scale={pop(172.3)}>
							cheap pair: $10
						</T>
						{after(176.5) && (
							<T x={1440} y={760} size={44} scale={pop(176.6)}>
								spends more, still wet feet
							</T>
						)}
					</>
				)}
			</Svg>
		);
	}
	return (
		<Svg>
			<T x={960} y={260} size={52} color={C.shadow} scale={pop(181.2)}>
				it&apos;s fiction... but the real-world version:
			</T>
			{['OVERDRAFTS', 'PAYDAY LOANS', 'CHECK CASHING'].map((s, i) => (
				<G key={s} x={460 + i * 500} y={560} s={pop(182.6 + i * 1.1)} r={(i - 1) * 3}>
					<Label text={s} w={440} size={50} fill={i === 1 ? C.yellow : C.white} color={C.red} seed={60 + i} />
				</G>
			))}
		</Svg>
	);
};

// ---------------------------------------------------------------- 7. Machine (188.3 – 227.44)
const S7 = 188.3;
const Machine: React.FC = () => (
	<MachineAndRules
		S={S7}
		labels={['OVERDRAFT', 'FAST CASH', 'NO BANK']}
		gearAt={[190.33, 193.66, 197.31]}
		punch={[{text: 'THE CHEAPEST THING: A SMALL CUSHION', at: 200.95}]}
		rulesAt={204.45}
		banner="build the cushion"
		rules={[
			{text: 'Turn off overdraft coverage.', at: 206.5},
			{text: 'Free checking, no minimum balance.', at: 214.8},
			{text: 'Emergency fund, even $10 a week.', at: 219.9},
		]}
	/>
);

// ---------------------------------------------------------------- 8. Payoff + bridge (227.44 – 241.70)
const S8 = 227.44;
const Payoff: React.FC = () => {
	const {pop, after} = useCue(S8);
	return (
		<Svg>
			<T x={960} y={170} size={58} font="marker" scale={pop(227.5)}>
				the system prices in your lack of options
			</T>
			{after(232.92) && (
				<G x={960} y={500} s={pop(233)}>
					<Phone>
						<G x={0} y={-40}>
							<Card w={220} h={110} seed={70} fill={C.white}>
								<T x={0} y={4} size={30}>
									hi, is this Anna?
								</T>
							</Card>
						</G>
					</Phone>
				</G>
			)}
			<G x={300} y={1000} s={0.75}>
				<Penny mood={after(232.92) ? 'thinking' : 'confident'} look={1} />
			</G>
			{after(237.25) && (
				<T x={960} y={880} size={62} font="marker" color={C.red} scale={pop(237.35)}>
					NEXT: THE PIG-BUTCHERING SCAM
				</T>
			)}
		</Svg>
	);
};

const End: React.FC = () => <EndScreen S={VO8_SECONDS} />;

const SFX: SfxCue[] = [
	[0.2, 'pop', 0.45],
	[3.3, 'beep', 0.4],
	[6.0, 'buzzer', 0.45],
	[11.1, 'coin', 0.4],
	[14.5, 'sting_dark', 0.5],
	[19.2, 'whoosh', 0.4],
	[20.8, 'pop', 0.4],
	[23.11, 'sting', 0.6],
	[25.0, 'pop', 0.4],
	[25.7, 'pop', 0.4],
	[26.4, 'pop', 0.4],
	[30.7, 'pop', 0.5],
	[34.2, 'pop', 0.4],
	[40.2, 'buzzer', 0.4],
	[43.5, 'pop', 0.4],
	[50.0, 'pop', 0.4],
	[55.5, 'flip', 0.4],
	[58.0, 'beep', 0.4],
	[65.6, 'chaching', 0.45],
	[76.8, 'whoosh', 0.4],
	[79.7, 'rise', 0.4],
	[80.5, 'chaching', 0.45],
	[86.7, 'pop', 0.5],
	[90.3, 'pop', 0.45],
	[98.0, 'coin', 0.45],
	[105.5, 'pop', 0.4],
	[110.0, 'rise', 0.4],
	[112.2, 'sting_dark', 0.45],
	[114.5, 'slap', 0.4],
	[116.1, 'slap', 0.4],
	[117.7, 'slap', 0.4],
	[119.3, 'slap', 0.4],
	[121.3, 'sting_dark', 0.4],
	[127.0, 'pop', 0.5],
	[131.2, 'pop', 0.45],
	[137.8, 'buzzer', 0.4],
	[143.8, 'flip', 0.4],
	[148.1, 'coin', 0.4],
	[150.5, 'coin', 0.4],
	[152.5, 'coin', 0.4],
	[157.1, 'stamp', 0.5],
	[162.8, 'whoosh', 0.4],
	[166.1, 'sting', 0.45],
	[167.7, 'pop', 0.4],
	[172.3, 'pop', 0.4],
	[176.6, 'plink', 0.35],
	[182.6, 'slap', 0.4],
	[183.7, 'slap', 0.4],
	[184.8, 'slap', 0.4],
	[188.4, 'pop', 0.5],
	[190.33, 'whirr', 0.35],
	[193.66, 'whirr', 0.35],
	[197.31, 'whirr', 0.35],
	[200.95, 'sting', 0.45],
	[204.5, 'pop', 0.45],
	[205.6, 'pop', 0.45],
	[213.9, 'pop', 0.45],
	[219.0, 'pop', 0.45],
	[208.0, 'tick', 0.5],
	[216.3, 'tick', 0.5],
	[221.4, 'tick', 0.5],
	[227.5, 'whoosh', 0.4],
	[233.0, 'ding', 0.45],
	[237.35, 'sting_dark', 0.5],
];

export const Ep08: React.FC = () => (
	<Episode
		vo="ep08_vo.mp3"
		music="music_lofi_ep04.mp3"
		voEnd={VO8_SECONDS}
		total={EP08_SECONDS}
		sfx={SFX}
		dips={[14.5, 157.1]}
		scenes={[
			[S1, Hook],
			[S2, Promise_],
			[S3, Overdraft],
			[S4, FastCash],
			[S5, NoBank],
			[S6, Boots],
			[S7, Machine],
			[S8, Payoff],
			[VO8_SECONDS, End],
		]}
	/>
);
