import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Penny} from '../lib/characters';
import {Card, Coin, Cross, Phone, Tick} from '../lib/props';
import {C, G, R, T, countUp} from '../lib/rough';
import {SfxCue} from '../lib/sound';
import {EndScreen, EngineLabels, Episode, Header, Label, MachineAndRules, Stat, Svg, TitleCard, useCue} from '../lib/kit';

/**
 * Episode 9 (Friday special): POV: A "Wrong Number" Texted You.
 * POV format borrowed from @POVFinanceUS: "you" (Penny) see through the scam, Marcus takes the bait.
 * Cue times are GLOBAL seconds from timing_ep09.json (exact Kokoro timings).
 */
export const VO9_SECONDS = 301.0;
export const EP09_SECONDS = VO9_SECONDS + 12;

// ---------------------------------------------------------------- Episode props
/** Marcus: Penny's coworker. Blue hoodie, short dark hair. Origin at his feet. */
export const Marcus: React.FC<{mood?: 'neutral' | 'happy' | 'worried' | 'shocked'; phone?: boolean}> = ({mood = 'neutral', phone = false}) => {
	const frame = useCurrentFrame();
	const blink = (frame + 23) % 120 < 4 ? 0.15 : 1;
	const bob = Math.sin(frame / 19) * 1.5;
	const shocked = mood === 'shocked';
	return (
		<g transform={`translate(0 ${bob})`}>
			<R s={{kind: 'line', x1: -20, y1: -115, x2: -24, y2: 0}} o={{strokeWidth: 7}} seed={9001} />
			<R s={{kind: 'line', x1: 20, y1: -115, x2: 24, y2: 0}} o={{strokeWidth: 7}} seed={9002} />
			<R s={{kind: 'ellipse', x: -28, y: 0, w: 36, h: 14}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9003} />
			<R s={{kind: 'ellipse', x: 28, y: 0, w: 36, h: 14}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9004} />
			<R s={{kind: 'polygon', pts: [[-56, -245], [56, -245], [68, -108], [-68, -108]]}} o={{fill: C.blue, fillStyle: 'hachure', hachureAngle: 41}} seed={9005} />
			{phone ? (
				<>
					<R s={{kind: 'line', x1: -52, y1: -228, x2: -20, y2: -170}} o={{strokeWidth: 7}} seed={9006} />
					<R s={{kind: 'line', x1: 52, y1: -228, x2: 20, y2: -170}} o={{strokeWidth: 7}} seed={9007} />
					<R s={{kind: 'rect', x: -26, y: -215, w: 52, h: 80}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9008} />
				</>
			) : shocked ? (
				<>
					<R s={{kind: 'line', x1: -52, y1: -228, x2: -100, y2: -300}} o={{strokeWidth: 7}} seed={9006} />
					<R s={{kind: 'line', x1: 52, y1: -228, x2: 100, y2: -300}} o={{strokeWidth: 7}} seed={9007} />
				</>
			) : (
				<>
					<R s={{kind: 'line', x1: -52, y1: -228, x2: -76, y2: -135}} o={{strokeWidth: 7}} seed={9006} />
					<R s={{kind: 'line', x1: 52, y1: -228, x2: 76, y2: -135}} o={{strokeWidth: 7}} seed={9007} />
				</>
			)}
			<g transform="translate(0 -318)">
				<R s={{kind: 'circle', x: 0, y: 0, d: 136}} o={{fill: '#C98E68', fillStyle: 'solid'}} seed={9009} />
				<R s={{kind: 'path', d: 'M -66 -10 C -70 -80 70 -84 66 -10 C 40 -40 -40 -40 -66 -10 Z'}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9010} />
				{[-22, 22].map((x, i) => (
					<g key={x} transform={`translate(${x} 6) scale(1 ${shocked ? 1.4 : blink})`}>
						<R s={{kind: 'ellipse', x: 0, y: 0, w: shocked ? 20 : 12, h: shocked ? 20 : 16}} o={{fill: C.ink, fillStyle: 'solid', roughness: 0.6}} seed={9011 + i} />
					</g>
				))}
				{shocked ? (
					<R s={{kind: 'ellipse', x: 0, y: 38, w: 24, h: 30}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9013} />
				) : mood === 'worried' ? (
					<R s={{kind: 'arc', x: 0, y: 46, w: 36, h: 20, start: Math.PI * 1.1, stop: Math.PI * 1.9}} o={{strokeWidth: 3}} seed={9013} />
				) : (
					<R s={{kind: 'arc', x: 0, y: 28, w: mood === 'happy' ? 46 : 30, h: 26, start: Math.PI * 0.15, stop: Math.PI * 0.85}} o={{strokeWidth: 3}} seed={9013} />
				)}
			</g>
		</g>
	);
};

/** The POV Finance signature: a red "YOU" with an arrow pointing at the protagonist. Origin at arrow tip. */
const YouArrow: React.FC<{s?: number}> = ({s = 1}) => (
	<G x={0} y={0} s={s}>
		<R s={{kind: 'curve', pts: [[-150, -110], [-90, -40], [-10, -8]]}} o={{stroke: C.red, strokeWidth: 9}} seed={9020} />
		<R s={{kind: 'polygon', pts: [[0, 0], [-40, -6], [-20, -34]]}} o={{fill: C.red, fillStyle: 'solid', stroke: C.red}} seed={9021} />
		<T x={-190} y={-130} size={70} font="marker" color={C.red}>
			YOU
		</T>
	</G>
);

/** Big "DAY N" stamp, top left. */
const DayStamp: React.FC<{n: number; at: number; S: number}> = ({n, at, S}) => {
	const {pop} = useCue(S);
	return (
		<G x={230} y={130} s={pop(at)} r={-6}>
			<Card w={300} h={120} seed={90} fill={C.red}>
				<T x={0} y={6} size={70} font="marker" color={C.white}>
					DAY {n}
				</T>
			</Card>
		</G>
	);
};

/** Chat bubble inside a phone screen (phone-local coords). */
const Msg: React.FC<{y: number; lines: string[]; me?: boolean; fill?: string; s?: number}> = ({y, lines, me = false, fill, s = 1}) => (
	<G x={me ? 14 : -14} y={y} s={s}>
		<Card w={190} h={24 + lines.length * 26} seed={y % 50} fill={fill ?? (me ? '#D6F5E3' : C.white)}>
			{lines.map((l, i) => (
				<T key={l} x={0} y={-((lines.length - 1) * 13) + i * 26 + 2} size={21}>
					{l}
				</T>
			))}
		</Card>
	</G>
);

/** The fake trading app screen (phone-local coords). */
const FakeApp: React.FC<{balance: string; chart?: number; children?: React.ReactNode}> = ({balance, chart = 1, children}) => {
	const candles = [30, -20, 45, 25, -15, 60];
	return (
		<g>
			<R s={{kind: 'rect', x: -112, y: -205, w: 224, h: 52}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9030} boil={false} />
			<T x={0} y={-172} size={26} font="marker" color={C.yellow}>
				TRADEX PRO
			</T>
			<T x={0} y={-118} size={20} color={C.shadow}>
				balance
			</T>
			<T x={0} y={-76} size={balance.length > 6 ? 28 : 44} font="marker" color={C.green}>
				{balance}
			</T>
			{candles.map((c, i) =>
				i / candles.length < chart ? (
					<R
						key={i}
						s={{kind: 'rect', x: -90 + i * 32, y: 40 - i * 14 - Math.max(c, 0), w: 18, h: Math.abs(c) + 10}}
						o={{fill: c > 0 ? C.green : C.red, fillStyle: 'solid'}}
						seed={9031 + i}
						boil={false}
					/>
				) : null,
			)}
			{children}
		</g>
	);
};

const WithdrawBtn: React.FC<{pressed?: boolean}> = ({pressed = false}) => (
	<G x={0} y={140} s={pressed ? 0.94 : 1}>
		<Card w={180} h={56} seed={9040} fill={pressed ? C.shadow : C.yellow}>
			<T x={0} y={4} size={26} font="marker">
				WITHDRAW
			</T>
		</Card>
	</G>
);

/** Night-time living room backdrop: dark band, moon, couch. */
const Night: React.FC = () => (
	<g>
		<rect x={0} y={0} width={1920} height={1080} fill="#1E2A4A" opacity={0.1} />
		<R s={{kind: 'circle', x: 1780, y: 130, d: 90}} o={{fill: C.yellow, fillStyle: 'solid'}} seed={9050} boil={false} />
		<R s={{kind: 'rect', x: 560, y: 860, w: 560, h: 140}} o={{fill: C.brown, fillStyle: 'hachure'}} seed={9051} boil={false} />
		<R s={{kind: 'rect', x: 540, y: 800, w: 600, h: 70}} o={{fill: C.brown, fillStyle: 'solid'}} seed={9052} boil={false} />
	</g>
);

const Pig: React.FC<{fat: number}> = ({fat}) => (
	<g transform={`scale(${0.6 + fat * 0.6} ${0.6 + fat * 0.45})`}>
		<R s={{kind: 'ellipse', x: 0, y: 0, w: 320, h: 220}} o={{fill: '#F4A7B9', fillStyle: 'solid'}} seed={9060} />
		<R s={{kind: 'circle', x: 150, y: -10, d: 70}} o={{fill: '#E98AA2', fillStyle: 'solid'}} seed={9061} />
		<R s={{kind: 'polygon', pts: [[60, -100], [100, -150], [110, -90]]}} o={{fill: '#E98AA2', fillStyle: 'solid'}} seed={9062} />
		<R s={{kind: 'circle', x: 90, y: -40, d: 14}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9063} />
		<R s={{kind: 'rect', x: -60, y: 50, w: 22, h: 90}} o={{fill: '#F4A7B9', fillStyle: 'solid'}} seed={9067} />
		<R s={{kind: 'rect', x: 50, y: 50, w: 22, h: 90}} o={{fill: '#F4A7B9', fillStyle: 'solid'}} seed={9068} />
		<R s={{kind: 'rect', x: -40, y: -120, w: 80, h: 10}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9064} />
	</g>
);

const Table: React.FC = () => (
	<g>
		<R s={{kind: 'rect', x: 560, y: 760, w: 800, h: 40}} o={{fill: C.brown, fillStyle: 'solid'}} seed={9070} boil={false} />
		<R s={{kind: 'line', x1: 620, y1: 800, x2: 620, y2: 1000}} o={{strokeWidth: 8}} seed={9071} boil={false} />
		<R s={{kind: 'line', x1: 1300, y1: 800, x2: 1300, y2: 1000}} o={{strokeWidth: 8}} seed={9072} boil={false} />
	</g>
);

const Chair: React.FC = () => (
	<g>
		<R s={{kind: 'rect', x: -70, y: -300, w: 20, h: 300}} o={{fill: C.shadow, fillStyle: 'solid'}} seed={9080} boil={false} />
		<R s={{kind: 'rect', x: -70, y: -130, w: 150, h: 20}} o={{fill: C.shadow, fillStyle: 'solid'}} seed={9081} boil={false} />
		<R s={{kind: 'line', x1: 70, y1: -110, x2: 70, y2: 0}} o={{strokeWidth: 6, stroke: C.shadow}} seed={9082} boil={false} />
	</g>
);

// ---------------------------------------------------------------- 1. Cold open (0 – 36.0)
const S1 = 0;
const Hook: React.FC = () => {
	const {pop, p, after, t} = useCue(S1);
	const bal = after(7.45) ? '$' + countUp(p(7.6, 2.2), 184000).toLocaleString('en-US') : '$0';
	return (
		<Svg>
			<Night />
			<T x={960} y={90} size={56} font="marker" scale={pop(0.1)}>
				THURSDAY, 11:48 PM
			</T>
			<G x={310} y={1000} s={0.9}>
				<Penny mood={after(27.93) ? 'confident' : 'neutral'} look={1} />
			</G>
			{after(27.93) && (
				<G x={330} y={630} s={pop(28)}>
					<YouArrow />
				</G>
			)}
			<G x={830} y={1000} s={pop(3.3) * 0.9}>
				<Marcus phone mood={after(15.64) ? 'worried' : 'happy'} />
			</G>
			{after(3.3) && (
				<T x={830} y={560} size={44} font="marker" color={C.blue} scale={pop(3.4)}>
					MARCUS
				</T>
			)}
			<G x={1460} y={540} s={pop(7.45) * 1.55}>
				<Phone>
					<FakeApp balance={bal} chart={p(7.6, 2)}>
						<WithdrawBtn pressed={after(11.95) && t < 13.0} />
						{after(15.64) && (
							<G x={0} y={20} s={pop(15.7)}>
								<Card w={210} h={170} seed={9090} fill={C.white}>
									<T x={0} y={-50} size={20}>
										to release your funds
									</T>
									<T x={0} y={-18} size={24} font="marker" color={C.red}>
										PAY 15% TAX
									</T>
									{after(20.05) && (
										<T x={0} y={36} size={40} font="marker" color={C.red} scale={pop(20.1)}>
											$27,600
										</T>
									)}
								</Card>
							</G>
						)}
					</FakeApp>
				</Phone>
			</G>
			{after(23.13) && (
				<G x={1460} y={960} s={pop(23.2)}>
					<Label text="already in: everything" w={560} size={46} fill={C.yellow} color={C.red} />
				</G>
			)}
			{after(32.15) && (
				<G x={760} y={250} s={pop(32.3)}>
					<Label text="90 DAYS AGO... YOU GOT THE SAME TEXT" w={1000} size={42} fill={C.ink} color={C.yellow} />
				</G>
			)}
			{t < 4 && <DayStamp n={90} at={0.6} S={S1} />}
		</Svg>
	);
};

// ---------------------------------------------------------------- 2. Promise (36.0 – 56.62)
const S2 = 36.0;
const Promise_: React.FC = () => {
	const {pop, p, after, t} = useCue(S2);
	if (t < 43.44) {
		return (
			<Svg>
				<G x={960} y={330} s={pop(36.1)} r={-4}>
					<Card w={860} h={170} seed={9100} fill={C.yellow}>
						<T x={0} y={8} size={100} font="marker" color={C.red}>
							FRIDAY SPECIAL
						</T>
					</Card>
				</G>
				{after(39.28) && (
					<T x={960} y={620} size={70} font="marker" scale={pop(39.3)}>
						the story is made up.
					</T>
				)}
				{after(41.35) && (
					<T x={960} y={760} size={80} font="marker" color={C.red} scale={pop(41.4)}>
						the playbook is real.
					</T>
				)}
			</Svg>
		);
	}
	if (t < 48.59) {
		return (
			<Svg>
				<TitleCard S={S2} at={43.44} subtitle="POV: the pig-butchering scam" />
			</Svg>
		);
	}
	if (t < 53.02) {
		return (
			<Svg>
				<G x={760} y={540}>
					<Pig fat={p(48.6, 2)} />
				</G>
				<T x={1440} y={420} size={70} font="marker" scale={pop(48.7)}>
					1. FATTEN
				</T>
				{after(50.74) && (
					<T x={1440} y={600} size={70} font="marker" color={C.red} scale={pop(50.8)}>
						2. TAKE EVERYTHING
					</T>
				)}
			</Svg>
		);
	}
	return (
		<Svg>
			<T x={960} y={330} size={70} font="marker" scale={pop(53.1)}>
				how it works... and how you saw it coming
			</T>
			<EngineLabels S={S2} at={53.5} labels={['WRONG NUMBER', 'THE FRIEND', 'FAKE APP']} y={680} />
		</Svg>
	);
};

// ---------------------------------------------------------------- 3. Day 1 (56.62 – 87.24)
const S3 = 56.62;
const Day1: React.FC = () => {
	const {pop, after, t} = useCue(S3);
	if (t < 78.74) {
		return (
			<Svg>
				<DayStamp n={1} at={56.7} S={S3} />
				<T x={1200} y={130} size={52} scale={pop(57.9)}>
					Tuesday, 7:10 AM
				</T>
				<G x={560} y={560} s={pop(60.97) * 1.35}>
					<Phone>
						<T x={0} y={-170} size={22} color={C.shadow}>
							unknown number
						</T>
						{after(63.59) && <Msg y={-90} lines={['Hi Anna, still on', 'for golf Saturday?']} />}
						{after(76.91) && (
							<T x={0} y={60} size={24} color={C.shadow} scale={pop(77)}>
								(no reply)
							</T>
						)}
					</Phone>
				</G>
				<T x={560} y={950} size={60} font="marker" color={C.red} scale={pop(61)}>
					YOU
				</T>
				{after(68.52) && (
					<>
						<G x={1360} y={560} s={pop(68.6) * 1.35}>
							<Phone>
								<T x={0} y={-170} size={22} color={C.shadow}>
									unknown number
								</T>
								<Msg y={-90} lines={['Hi Sam, still on', 'for golf Saturday?']} />
								{after(74.13) && (
									<G x={0} y={20} s={pop(74.2)}>
										<Msg y={0} me lines={['Sorry, wrong', 'number!']} />
									</G>
								)}
							</Phone>
						</G>
						<T x={1360} y={950} size={60} font="marker" color={C.blue}>
							MARCUS
						</T>
					</>
				)}
				{after(71.74) && (
					<T x={960} y={330} size={40} color={C.ink} scale={pop(71.8)}>
						same message
					</T>
				)}
			</Svg>
		);
	}
	const dots = 24;
	return (
		<Svg>
			<Header text="MECHANISM #1: THE FILTER" at={78.8} S={S3} />
			<R s={{kind: 'polygon', pts: [[560, 330], [1360, 330], [1020, 700], [900, 700]]}} o={{fill: C.shadow, fillStyle: 'hachure'}} seed={9110} />
			{Array.from({length: dots}).map((_, i) => (
				<G key={i} x={600 + (i % 12) * 65} y={220 + Math.floor(i / 12) * 60} s={pop(79 + i * 0.03)}>
					<R s={{kind: 'rect', x: -16, y: -26, w: 32, h: 52}} o={{fill: C.ink, fillStyle: 'solid'}} seed={9120 + i} boil={false} />
				</G>
			))}
			{after(82.94) && (
				<>
					<G x={960} y={790} s={pop(83)}>
						<R s={{kind: 'rect', x: -22, y: -36, w: 44, h: 72}} o={{fill: C.red, fillStyle: 'solid'}} seed={9150} />
					</G>
					<G x={960} y={950} s={pop(84.5)}>
						<Label text="replied = a lead" w={640} size={60} fill={C.yellow} color={C.red} />
					</G>
				</>
			)}
			{after(81.47) && (
				<T x={1580} y={520} size={56} font="marker" color={C.red} scale={pop(81.5)}>
					not a mistake
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 4. Day 12 (87.24 – 127.06)
const S4 = 87.24;
const Day12: React.FC = () => {
	const {pop, after, t} = useCue(S4);
	if (t < 116.02) {
		const msgs: {at: number; lines: string[]; fill?: string}[] = [
			{at: 93.3, lines: ['good morning :)']},
			{at: 94.2, lines: ['good morning!']},
			{at: 96.6, lines: ['how is your sister', 'Lena doing?']},
			{at: 98.3, lines: ['still hate that job?']},
			{at: 103.8, lines: ['my uncle taught me', 'crypto trading...']},
			{at: 109.4, lines: ['can we chat on', 'another app?'], fill: '#FBD3D4'},
		];
		const shown = msgs.filter((m) => after(m.at)).slice(-4);
		return (
			<Svg>
				<DayStamp n={12} at={87.3} S={S4} />
				<G x={330} y={1000} s={0.85}>
					<Marcus phone mood="happy" />
				</G>
				<G x={960} y={560} s={pop(88.7) * 1.6}>
					<Phone>
						<T x={0} y={-172} size={26} font="marker" color={C.red}>
							{after(91.25) ? 'Grace' : ''}
						</T>
						{shown.map((m, i) => (
							<G key={m.at} x={0} y={-110 + i * 78} s={pop(m.at)}>
								<Msg y={0} lines={m.lines} fill={m.fill} />
							</G>
						))}
					</Phone>
				</G>
				{after(100.38) && (
					<G x={1560} y={330} s={pop(100.4)}>
						<Stat label="asked for money" value="$0" w={420} color={C.green} fill={C.white} />
					</G>
				)}
				<G x={1600} y={1000} s={0.8}>
					<Penny mood={after(112.52) ? 'thinking' : 'neutral'} look={-1} />
				</G>
				{after(114.16) && (
					<G x={1560} y={560} s={pop(114.2)}>
						<Label text="fewer people watching" w={520} size={42} fill={C.yellow} color={C.red} />
					</G>
				)}
			</Svg>
		);
	}
	return (
		<Svg>
			<Header text="MECHANISM #2: SELL A PERSON" at={116.1} S={S4} />
			<G x={560} y={450} s={pop(117.9)}>
				<Card w={520} h={200} seed={9200} fill={C.white}>
					<T x={0} y={6} size={64} font="marker">
						AN INVESTMENT
					</T>
				</Card>
				{after(119.5) && (
					<G x={0} y={0} s={2.4}>
						<Cross draw={1} seed={9} />
					</G>
				)}
			</G>
			{after(120.76) && (
				<G x={1360} y={450} s={pop(120.8)}>
					<Card w={520} h={200} seed={9201} fill={C.yellow}>
						<T x={0} y={6} size={64} font="marker" color={C.red}>
							A PERSON
						</T>
					</Card>
				</G>
			)}
			{after(122.59) && (
				<T x={760} y={800} size={80} font="marker" color={C.green} scale={pop(122.6)}>
					1. TRUST
				</T>
			)}
			{after(124.7) && (
				<T x={1200} y={800} size={80} font="marker" color={C.red} scale={pop(124.75)}>
					2. MONEY
				</T>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 5. Day 30 (127.06 – 164.17)
const S5 = 127.06;
const Day30: React.FC = () => {
	const {pop, p, after, t} = useCue(S5);
	if (t < 150.29) {
		const bal = after(138.88) ? '$' + (500 + countUp(p(139, 1.6), 140)) : after(136.38) ? '$500' : '$0';
		return (
			<Svg>
				<DayStamp n={30} at={127.1} S={S5} />
				<G x={700} y={560} s={pop(128.5) * 1.6}>
					<Phone>
						<FakeApp balance={bal} chart={p(133, 2.5)}>
							{after(133.03) && (
								<G x={0} y={92} s={pop(134.5)}>
									<Card w={200} h={36} seed={9300} fill={C.white}>
										<T x={0} y={4} size={18}>
											24/7 support chat
										</T>
									</Card>
								</G>
							)}
							<WithdrawBtn pressed={after(142.16) && t < 143.5} />
						</FakeApp>
					</Phone>
				</G>
				{after(131.54) && (
					<T x={700} y={140} size={56} font="marker" scale={pop(131.6)}>
						looks real.
					</T>
				)}
				{after(144.5) && (
					<G x={1400} y={360} s={pop(144.6)}>
						<Stat label="your real bank" value="+$100" w={520} color={C.green} fill={C.white} />
					</G>
				)}
				{after(147.5) && (
					<G x={1250} y={1000} s={0.75}>
						<Marcus mood="happy" />
					</G>
				)}
				{after(149.05) && (
					<G x={1650} y={1000} s={0.75}>
						<Penny mood="thinking" look={-1} />
					</G>
				)}
			</Svg>
		);
	}
	return (
		<Svg>
			<Header text="MECHANISM #3: THE STAGE SET" at={150.4} S={S5} />
			<G x={560} y={560} s={pop(150.4) * 1.5}>
				<R s={{kind: 'curve', pts: [[0, -330], [0, -120], [40, 0], [0, 60], [-40, 20]]}} o={{strokeWidth: 8, stroke: C.shadow}} seed={9310} />
				<G x={-10} y={70} s={0.55}>
					<Card w={300} h={140} seed={9311} fill={C.green}>
						<T x={0} y={8} size={70} font="marker" color={C.white}>
							$100
						</T>
					</Card>
				</G>
			</G>
			<T x={560} y={940} size={52} font="marker" color={C.red} scale={pop(151)}>
				THE BAIT
			</T>
			{after(153.38) && (
				<G x={1300} y={500} s={pop(153.4) * 1.2}>
					<Phone>
						<FakeApp balance="$640" />
					</Phone>
					<R s={{kind: 'line', x1: 130, y1: -240, x2: 260, y2: -320}} o={{strokeWidth: 5}} seed={9312} />
					<R s={{kind: 'line', x1: -130, y1: -240, x2: -260, y2: -320}} o={{strokeWidth: 5}} seed={9313} />
				</G>
			)}
			{after(155.58) && (
				<G x={1300} y={850} s={pop(155.6)}>
					<Label text="numbers typed by the scammers" w={760} size={44} fill={C.white} color={C.red} />
				</G>
			)}
			{after(159.4) && (
				<G x={1300} y={980} s={pop(159.5)}>
					<Label text="a little out = buys the BIG deposit" w={800} size={46} fill={C.yellow} color={C.red} />
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 6. Day 60 (164.17 – 188.58)
const S6 = 164.17;
const Day60: React.FC = () => {
	const {pop, p, after, t} = useCue(S6);
	if (t < 175.96) {
		const srcs = [
			{at: 165.68, text: 'SAVINGS'},
			{at: 167.96, text: 'RETIREMENT'},
			{at: 170.2, text: 'CAR LOAN'},
		];
		return (
			<Svg>
				<DayStamp n={60} at={164.2} S={S6} />
				{srcs.map((s, i) =>
					after(s.at) ? (
						<G key={s.text} x={500} y={330 + i * 180} s={pop(s.at)}>
							<Card w={480} h={130} seed={9400 + i} fill={C.white}>
								<T x={0} y={6} size={56} font="marker">
									{s.text}
								</T>
							</Card>
							<G x={300 + p(s.at + 0.3, 1.2) * 400} y={-60 * p(s.at + 0.3, 1.2)} s={1 - p(s.at + 1.2, 0.4)}>
								<Coin seed={i} />
							</G>
						</G>
					) : null,
				)}
				<G x={1400} y={500} s={1.3}>
					<Phone>
						<FakeApp balance="$184,000" />
					</Phone>
				</G>
				{after(172.72) && (
					<G x={1400} y={930} s={pop(172.8)}>
						<Stat label="Marcus has deposited" value={'$' + countUp(p(172.8, 1.6), 120000).toLocaleString('en-US')} w={620} />
					</G>
				)}
			</Svg>
		);
	}
	return (
		<Svg>
			<T x={960} y={120} size={60} font="marker" scale={pop(176)}>
				lunch, day 60
			</T>
			<Table />
			<G x={760} y={1000} s={0.85}>
				<Penny mood={after(181.79) ? 'worried' : 'neutral'} look={1} />
			</G>
			<G x={1180} y={1000}>
				<Chair />
			</G>
			<T x={1180} y={560} size={110} font="marker" color={C.shadow} scale={pop(178.1)}>
				?
			</T>
			{after(179.78) && (
				<G x={1560} y={520} s={pop(179.8)}>
					<Card w={460} h={110} seed={9410} fill={C.white}>
						<T x={0} y={6} size={40}>
							Marcus: &quot;busy&quot;
						</T>
					</Card>
				</G>
			)}
			{after(181.79) && (
				<G x={960} y={300} s={pop(181.9)}>
					<Label text="SILENCE IS PART OF THE DESIGN" w={980} size={56} fill={C.yellow} color={C.red} />
				</G>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 7. Day 90 (188.58 – 259.78)
const S7 = 188.58;
const Day90: React.FC = () => {
	const {pop, p, after, t} = useCue(S7);
	if (t < 200.7) {
		return (
			<Svg>
				<Night />
				<DayStamp n={90} at={188.6} S={S7} />
				<G x={310} y={1000} s={0.9}>
					<Penny mood="confident" look={1} />
				</G>
				<G x={330} y={630}>
					<YouArrow />
				</G>
				<G x={830} y={1000} s={0.9}>
					<Marcus phone mood="worried" />
				</G>
				<G x={1460} y={540} s={1.55}>
					<Phone>
						<FakeApp balance="$184,000">
							<G x={0} y={20}>
								<Card w={210} h={170} seed={9090} fill={C.white}>
									<T x={0} y={-30} size={24} font="marker" color={C.red}>
										PAY 15% TAX
									</T>
									<T x={0} y={30} size={40} font="marker" color={C.red}>
										$27,600
									</T>
								</Card>
							</G>
						</FakeApp>
					</Phone>
				</G>
				{after(195.73) && (
					<G x={760} y={330} s={pop(195.8)}>
						<Card w={1180} h={200} seed={9500} fill={C.yellow}>
							<T x={0} y={-36} size={50} font="marker">
								A REAL EXCHANGE NEVER MAKES YOU
							</T>
							<T x={0} y={42} size={50} font="marker" color={C.red}>
								PAY TO GET YOUR OWN MONEY OUT
							</T>
						</Card>
					</G>
				)}
			</Svg>
		);
	}
	if (t < 216.59) {
		return (
			<Svg>
				<G x={420} y={1000} s={0.9}>
					<Marcus mood={after(210.21) ? 'shocked' : 'worried'} />
				</G>
				<G x={420} y={420} s={pop(200.8)}>
					<Card w={460} h={120} seed={9510} fill={C.white}>
						<T x={0} y={6} size={50} font="marker">
							PAY $27,600
						</T>
					</Card>
					{after(202.24) && (
						<G x={0} y={0} s={2}>
							<Cross draw={p(202.3, 0.5)} seed={3} />
						</G>
					)}
				</G>
				{after(203.75) && (
					<G x={1000} y={330} s={pop(203.8)}>
						<Card w={440} h={150} seed={9511} fill={C.white}>
							<T x={0} y={-24} size={40} font="marker" color={C.red}>
								Grace
							</T>
							<T x={0} y={32} size={34} color={C.shadow}>
								(no reply)
							</T>
						</Card>
					</G>
				)}
				{after(206.67) && (
					<G x={1560} y={330} s={pop(206.7)} r={after(208) ? 8 : 0}>
						<Card w={440} h={150} seed={9512} fill={C.shadow}>
							<T x={0} y={-24} size={36} font="marker">
								tradexpro.app
							</T>
							<T x={0} y={32} size={32} color={C.red}>
								site not found
							</T>
						</Card>
					</G>
				)}
				{after(210.21) && (
					<G x={1240} y={640} s={pop(210.3)}>
						<Stat label="Marcus put in" value="$120,000 GONE" w={760} />
					</G>
				)}
				{after(213.33) && (
					<G x={1240} y={880} s={pop(213.4)}>
						<Stat label="the fee he didn't pay" value="$27,600 SAVED" w={760} color={C.green} fill={C.white} seed={2} />
					</G>
				)}
			</Svg>
		);
	}
	if (t < 237.84) {
		return (
			<Svg>
				<G x={960} y={180} s={pop(216.6)}>
					<Label text="most people don't have someone on the couch" w={1300} size={52} fill={C.ink} color={C.yellow} />
				</G>
				{after(219.67) && (
					<G x={960} y={480} s={pop(219.8)}>
						<Stat label="lost to crypto investment fraud, US, 2024 (FBI)" value={`$${(5.8 * p(220, 1.6)).toFixed(1)} BILLION`} w={1100} size={96} />
					</G>
				)}
				{after(230.69) && (
					<G x={960} y={780} s={pop(230.8)}>
						<Stat label="crypto scam losses reported by people 60+" value="$2.8 BILLION+" w={1100} size={88} fill={C.white} seed={3} />
					</G>
				)}
			</Svg>
		);
	}
	return (
		<Svg>
			{t < 241.25 ? (
				<>
					<G x={960} y={540} s={pop(237.9) * 1.4}>
						<Phone>
							<Msg y={-100} lines={['good morning :)']} />
						</Phone>
					</G>
					{after(239.14) && (
						<T x={1450} y={540} size={80} font="marker" color={C.red} scale={pop(239.2)}>
							Grace?
						</T>
					)}
				</>
			) : (
				<>
					<Header text="WHO IS TYPING GOOD MORNING?" at={241.3} S={S7} />
					{/* compound: fence + blocks */}
					<R s={{kind: 'rect', x: 220, y: 520, w: 420, h: 300}} o={{fill: C.shadow, fillStyle: 'solid'}} seed={9520} />
					<R s={{kind: 'rect', x: 680, y: 440, w: 300, h: 380}} o={{fill: C.shadow, fillStyle: 'hachure'}} seed={9521} />
					{Array.from({length: 16}).map((_, i) => (
						<R key={i} s={{kind: 'line', x1: 180 + i * 55, y1: 900, x2: 180 + i * 55, y2: 700}} o={{strokeWidth: 5}} seed={9530 + i} boil={false} />
					))}
					<R s={{kind: 'line', x1: 170, y1: 720, x2: 1020, y2: 720}} o={{strokeWidth: 4}} seed={9550} boil={false} />
					<R s={{kind: 'line', x1: 170, y1: 760, x2: 1020, y2: 760}} o={{strokeWidth: 4}} seed={9551} boil={false} />
					{after(245) && (
						<G x={1460} y={360} s={pop(245.1)}>
							<Stat label="Myanmar: may be forced to run scams" value="120,000+" w={680} />
						</G>
					)}
					{after(249) && (
						<G x={1460} y={620} s={pop(249.1)}>
							<Stat label="Cambodia" value="~100,000" w={680} seed={2} />
						</G>
					)}
					<T x={1460} y={800} size={34} color={C.ink}>
						UN Human Rights Office estimate, 2023
					</T>
					{after(255.63) && (
						<G x={960} y={970} s={pop(255.7)}>
							<Label text="SOME ARE PRISONERS TOO" w={900} size={60} fill={C.red} color={C.white} />
						</G>
					)}
				</>
			)}
		</Svg>
	);
};

// ---------------------------------------------------------------- 8. Rules (259.78 – 283.81)
const S8 = 259.78;
const Rules: React.FC = () => (
	<MachineAndRules
		S={S8}
		labels={['WRONG NUMBER', 'THE FRIEND', 'FAKE APP']}
		gearAt={[259.9, 260.4, 260.9]}
		punch={[{text: 'HOW DO YOU JAM IT?', at: 260.2}]}
		rulesAt={262.15}
		banner="jam the machine"
		rules={[
			{text: 'Small talk turns to investing? Red flag.', at: 263.49},
			{text: 'Pay to withdraw? The money was never there.', at: 271.28},
			{text: 'Tell one person. Or be that person.', at: 276.78},
		]}
	/>
);

// ---------------------------------------------------------------- 9. Payoff + bridge (283.81 – 301.0)
const S9 = 283.81;
const Payoff: React.FC = () => {
	const {pop, after} = useCue(S9);
	return (
		<Svg>
			<T x={960} y={110} size={58} font="marker" scale={pop(283.9)}>
				it doesn&apos;t hack your phone...
			</T>
			{after(286.8) && (
				<T x={960} y={200} size={64} font="marker" color={C.red} scale={pop(286.9)}>
					it hacks loneliness and hope
				</T>
			)}
			<Table />
			<G x={760} y={1000} s={0.85}>
				<Penny mood="happy" look={1} />
			</G>
			<G x={1180} y={1000} s={0.85}>
				<Marcus mood="happy" />
			</G>
			{after(292.77) && (
				<G x={700} y={640} s={pop(292.8)}>
					<YouArrow />
				</G>
			)}
			{after(289.3) && (
				<T x={1560} y={420} size={46} font="marker" scale={pop(289.4)}>
					best defence:
				</T>
			)}
			{after(289.3) && (
				<T x={1560} y={490} size={46} font="marker" color={C.green} scale={pop(290.2)}>
					knowing the playbook
				</T>
			)}
			{after(294.46) && (
				<T x={960} y={330} size={62} font="marker" color={C.blue} scale={pop(294.5)}>
					NEXT: HOW AIRLINES REALLY MAKE MONEY
				</T>
			)}
		</Svg>
	);
};

const End: React.FC = () => <EndScreen S={VO9_SECONDS} />;

const SFX: SfxCue[] = [
	[0.1, 'clock', 0.35],
	[0.6, 'stamp', 0.45],
	[3.4, 'pop', 0.4],
	[7.6, 'rise', 0.4],
	[9.8, 'chaching', 0.45],
	[11.95, 'plink', 0.45],
	[15.7, 'buzzer', 0.45],
	[20.1, 'sting_dark', 0.5],
	[28.0, 'pop', 0.4],
	[32.2, 'rewind', 0.5],
	[36.1, 'stamp', 0.55],
	[39.3, 'pop', 0.4],
	[41.4, 'pop', 0.45],
	[43.44, 'sting', 0.6],
	[48.7, 'pop', 0.4],
	[50.8, 'sting_dark', 0.5],
	[53.5, 'pop', 0.4],
	[54.2, 'pop', 0.4],
	[54.9, 'pop', 0.4],
	[56.7, 'stamp', 0.5],
	[61.0, 'whoosh', 0.35],
	[63.6, 'ding', 0.45],
	[68.6, 'ding', 0.4],
	[74.2, 'bloop', 0.45],
	[77.0, 'plink', 0.35],
	[78.8, 'flip', 0.4],
	[83.0, 'beep', 0.45],
	[84.5, 'pop', 0.4],
	[87.3, 'stamp', 0.5],
	[93.3, 'ding', 0.35],
	[94.2, 'ding', 0.35],
	[96.6, 'ding', 0.35],
	[98.3, 'ding', 0.35],
	[100.4, 'coin', 0.35],
	[103.8, 'ding', 0.4],
	[109.4, 'buzzer', 0.4],
	[114.2, 'pop', 0.4],
	[116.1, 'flip', 0.4],
	[119.5, 'slap', 0.45],
	[120.8, 'pop', 0.45],
	[122.6, 'pop', 0.4],
	[124.75, 'chaching', 0.45],
	[127.1, 'stamp', 0.5],
	[128.5, 'whoosh', 0.35],
	[136.4, 'coin', 0.4],
	[139.0, 'rise', 0.4],
	[144.6, 'chaching', 0.5],
	[150.4, 'flip', 0.4],
	[153.4, 'pop', 0.4],
	[155.6, 'pop', 0.4],
	[159.5, 'sting_dark', 0.45],
	[164.2, 'stamp', 0.5],
	[165.7, 'coin', 0.4],
	[168.0, 'coin', 0.4],
	[170.2, 'coin', 0.4],
	[172.8, 'rise', 0.4],
	[176.0, 'whoosh', 0.35],
	[178.1, 'plink', 0.35],
	[181.9, 'sting_dark', 0.45],
	[188.6, 'rewind', 0.45],
	[195.8, 'sting', 0.5],
	[202.3, 'slap', 0.5],
	[203.8, 'plink', 0.4],
	[206.7, 'sputter', 0.45],
	[210.3, 'sting_dark', 0.5],
	[213.4, 'chaching', 0.5],
	[216.6, 'whoosh', 0.35],
	[219.8, 'rise', 0.4],
	[221.4, 'chaching', 0.45],
	[230.8, 'coin', 0.45],
	[237.9, 'ding', 0.4],
	[239.2, 'pop', 0.4],
	[241.3, 'sting_dark', 0.45],
	[245.1, 'stamp', 0.45],
	[249.1, 'stamp', 0.45],
	[255.7, 'sting_dark', 0.5],
	[284.0, 'whoosh', 0.4],
	[286.9, 'pop', 0.4],
	[292.8, 'pop', 0.45],
	[294.5, 'sting', 0.5],
];

export const Ep09: React.FC = () => (
	<Episode
		vo="ep09_vo.mp3"
		music="music_lofi_ep09.mp3"
		voEnd={VO9_SECONDS}
		total={EP09_SECONDS}
		sfx={SFX}
		dips={[20.1, 210.3, 255.7]}
		scenes={[
			[S1, Hook],
			[S2, Promise_],
			[S3, Day1],
			[S4, Day12],
			[S5, Day30],
			[S6, Day60],
			[S7, Day90],
			[S8, Rules],
			[S9, Payoff],
			[VO9_SECONDS, End],
		]}
	/>
);
