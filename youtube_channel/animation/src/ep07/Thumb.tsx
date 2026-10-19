import React from 'react';
import {Penny} from '../lib/characters';
import {G} from '../lib/rough';
import {Burst, Glow, Headline, NewsBar, ThumbFrame, ThumbPenny} from '../lib/thumbkit';
import {PayIn4} from './Ep07';

/** Ep. 7 thumbnail: the glowing Pay in 4 button, "0% INTEREST?". */
export const Ep07Thumb: React.FC = () => (
	<ThumbFrame>
		<Burst scene="bnpl" bg="#0B6E73" ray="#138489" cx={960} cy={420} />
		<G x={270} y={980} s={2.2}>
			<ThumbPenny><Penny mood="thinking" /></ThumbPenny>
		</G>
		<Glow x={1000} y={500} r={330} />
		<G x={900} y={480} s={0.95} r={-5}>
			<PayIn4 glow />
		</G>
		<Headline x={780} y={95} size={130}>
			0% INTEREST?
		</Headline>
		<Headline x={770} y={225} size={86} color={'#FFFFFF'}>
			SO WHO PROFITS
		</Headline>
		<NewsBar text="BUY NOW, PAY MORE" />
	</ThumbFrame>
);
