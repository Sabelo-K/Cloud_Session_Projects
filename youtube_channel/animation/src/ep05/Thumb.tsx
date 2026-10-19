import React from 'react';
import {Penny} from '../lib/characters';
import {Phone} from '../lib/props';
import {G} from '../lib/rough';
import {Burst, Glow, Headline, NewsBar, ThumbFrame, ThumbPenny} from '../lib/thumbkit';
import {Feed} from './Ep05';

/** Ep. 5 thumbnail: Penny inside the phone, "YOU'RE THE PRODUCT". */
export const Ep05Thumb: React.FC = () => (
	<ThumbFrame>
		<Burst scene="apps" bg="#2B3FA0" ray="#3A50BA" cx={960} cy={420} />
		<G x={270} y={980} s={2.2}>
			<ThumbPenny><Penny mood="shocked" /></ThumbPenny>
		</G>
		<Glow x={1000} y={560} r={330} />
		<G x={1000} y={560} s={1.5} r={6}>
			<Phone><Feed scroll={0} /></Phone>
		</G>
		<Headline x={780} y={95} size={130}>
			FREE?
		</Headline>
		<Headline x={760} y={225} size={78} color={'#FFFFFF'}>
			YOU&apos;RE THE PRODUCT
		</Headline>
		<NewsBar text="WHO PAYS FOR FREE APPS" />
	</ThumbFrame>
);
