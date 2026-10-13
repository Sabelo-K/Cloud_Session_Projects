import React from 'react';
import {Penny} from '../lib/characters';
import {G} from '../lib/rough';
import {Burst, Glow, Headline, ThumbPenny, Ring, Ribbon, ThumbFrame} from '../lib/thumbkit';
import {CreditCard} from './Ep03';

/** Ep. 3 thumbnail: glowing credit card, "19 YEARS?!" to pay off the minimum. */
export const Ep03Thumb: React.FC = () => (
	<ThumbFrame>
		<Burst bg="#5B2A86" ray="#6B379A" cx={900} cy={430} />
		<G x={270} y={980} s={2.2}>
			<ThumbPenny><Penny mood="shocked" /></ThumbPenny>
		</G>
		<Glow x={920} y={460} r={280} />
		<G x={920} y={460} s={1.6} r={-10}>
			<CreditCard glow />
		</G>
		
		<Headline x={880} y={110} size={150}>
			19 YEARS?!
		</Headline>
		<Ribbon x={860} y={660} w={740} text="DON'T PAY THE MINIMUM" size={50} />
	</ThumbFrame>
);
