import React from 'react';
import {Broker, Penny} from '../lib/characters';
import {Cash} from '../lib/props';
import {G} from '../lib/rough';
import {Arrow, Burst, Glow, Headline, ThumbPenny, Ribbon, ThumbFrame} from '../lib/thumbkit';

/** Ep. 1 thumbnail: shocked Penny, smirking broker, tiny cash for her guitar, "$150?!". */
export const Ep01Thumb: React.FC = () => (
	<ThumbFrame>
		<Burst bg="#1B3A8C" ray="#24489F" cx={300} cy={420} />
		<G x={290} y={980} s={2.2}>
			<ThumbPenny><Penny mood="shocked" holdGuitar /></ThumbPenny>
		</G>
		<G x={1110} y={860} s={1.35}>
			<Broker mood="smirk" arm={1} look={-1} />
		</G>
		<Glow x={850} y={560} r={170} />
		<G x={850} y={560} s={1.5} r={-12}>
			<Cash />
		</G>
		<Arrow x1={720} y1={300} x2={815} y2={485} />
		<Headline x={870} y={150} size={200}>
			$150?!
		</Headline>
		<Ribbon x={860} y={655} w={760} text="THE PAWN SHOP TRICK" />
	</ThumbFrame>
);
