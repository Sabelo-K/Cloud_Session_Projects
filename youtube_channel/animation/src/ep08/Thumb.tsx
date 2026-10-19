import React from 'react';
import {Penny} from '../lib/characters';
import {Card} from '../lib/props';
import {C, G, T} from '../lib/rough';
import {Burst, Glow, Headline, NewsBar, ThumbFrame, ThumbPenny} from '../lib/thumbkit';

/** Ep. 8 thumbnail: a $34 fee on a $24 lunch, "17,000%". */
export const Ep08Thumb: React.FC = () => (
	<ThumbFrame>
		<Burst scene="broke" bg="#8A2A12" ray="#A0371C" cx={960} cy={420} />
		<G x={270} y={980} s={2.2}>
			<ThumbPenny><Penny mood="shocked" /></ThumbPenny>
		</G>
		<Glow x={1000} y={520} r={330} />
		<G x={1000} y={430} r={5}>
			<Card w={520} h={260} seed={8} fill={C.white}>
				<T x={-220} y={-60} size={48} anchor="start">lunch</T>
				<T x={220} y={-60} size={60} font="marker" anchor="end">$24</T>
				<T x={-220} y={50} size={48} anchor="start">fee</T>
				<T x={220} y={50} size={80} font="marker" anchor="end" color={C.red}>$34</T>
			</Card>
		</G>
		<Headline x={780} y={95} size={130}>
			17,000%
		</Headline>
		<Headline x={770} y={225} size={86} color={'#FFFFFF'}>
			FOR BEING BROKE
		</Headline>
		<NewsBar text="THE TAX ON BEING BROKE" />
	</ThumbFrame>
);
