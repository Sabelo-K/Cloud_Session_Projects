import React from 'react';
import {Penny} from '../lib/characters';
import {HotDog, MemberCard} from '../lib/props2';
import {C, G} from '../lib/rough';
import {Arrow, Burst, Glow, Headline, ThumbPenny, ThumbFrame} from '../lib/thumbkit';

/** Ep. 2 thumbnail: giant membership card as the real product, "$5.3B" from fees. */
export const Ep02Thumb: React.FC = () => (
	<ThumbFrame>
		<Burst bg="#C62F35" ray="#D9444A" cx={880} cy={420} />
		<G x={270} y={980} s={2.2}>
			<ThumbPenny><Penny mood="shocked" /></ThumbPenny>
		</G>
		<Glow x={890} y={470} r={300} />
		<G x={890} y={470} s={1.55} r={-8}>
			<MemberCard />
		</G>
		<G x={560} y={690} s={0.8} r={8}>
			<HotDog />
		</G>
		<Arrow x1={600} y1={250} x2={720} y2={390} color={C.yellow} />
		<Headline x={900} y={115} size={170}>
			$5.3B
		</Headline>
		<Headline x={930} y={672} size={70} color={C.white} rotate={-3}>
			IT&apos;S THE CARD
		</Headline>
	</ThumbFrame>
);
