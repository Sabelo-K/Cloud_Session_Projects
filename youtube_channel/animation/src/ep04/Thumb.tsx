import React from 'react';
import {Penny} from '../lib/characters';
import {G} from '../lib/rough';
import {Burst, Glow, Headline, ThumbPenny, ThumbFrame} from '../lib/thumbkit';
import {SlotMachine} from './Ep04';

/** Ep. 4 thumbnail: shocked Penny, jackpot slot machine, "RIGGED BY MATH". */
export const Ep04Thumb: React.FC = () => (
	<ThumbFrame>
		<Burst bg="#0E6B3E" ray="#14804C" cx={960} cy={400} />
		<G x={270} y={980} s={2.2}>
			<ThumbPenny><Penny mood="shocked" /></ThumbPenny>
		</G>
		<Glow x={1010} y={540} r={330} />
		<G x={1010} y={860} s={0.9} r={6}>
			<SlotMachine reels={['7', '7', '$']} />
		</G>
		<Headline x={760} y={95} size={130}>
			RIGGED
		</Headline>
		<Headline x={800} y={225} size={110} color={'#FFFFFF'}>
			BY MATH
		</Headline>
	</ThumbFrame>
);
