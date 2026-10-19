import React from 'react';
import {Penny} from '../lib/characters';
import {Card} from '../lib/props';
import {C, G, T} from '../lib/rough';
import {Burst, Glow, Headline, NewsBar, ThumbFrame, ThumbPenny} from '../lib/thumbkit';

/** Ep. 6 thumbnail: a pile of monthly charges, "FORGOT TO CANCEL?". */
export const Ep06Thumb: React.FC = () => {
	const subs = ['$9.99', '$14.99', '$6.99', '$12.99'];
	return (
		<ThumbFrame>
			<Burst scene="subs" bg="#6B1F7A" ray="#80308F" cx={960} cy={420} />
			<G x={270} y={980} s={2.2}>
				<ThumbPenny><Penny mood="worried" /></ThumbPenny>
			</G>
			<Glow x={1000} y={560} r={330} />
			{subs.map((s, i) => (
				<G key={s} x={900 + (i % 2) * 260} y={390 + Math.floor(i / 2) * 170} r={(i % 2 ? 6 : -6)}>
					<Card w={240} h={150} seed={i + 3} fill={i % 3 ? C.white : C.yellow}>
						<T x={0} y={-30} size={30}>every month</T>
						<T x={0} y={30} size={56} font="marker" color={C.red}>{s}</T>
					</Card>
				</G>
			))}
			<Headline x={760} y={95} size={120}>
				FORGOT TO
			</Headline>
			<Headline x={780} y={225} size={120} color={'#FFFFFF'}>
				CANCEL?
			</Headline>
			<NewsBar text="THE SUBSCRIPTION TRAP" />
		</ThumbFrame>
	);
};
