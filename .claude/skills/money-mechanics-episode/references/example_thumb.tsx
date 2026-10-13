import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Penny} from '../lib/characters';
import {C, G, R, T} from '../lib/rough';
import {CreditCard} from './Ep03';

/** Ep. 3 thumbnail: shocked Penny, glowing credit card, "19 YEARS?!". */
export const Ep03Thumb: React.FC = () => (
	<AbsoluteFill style={{background: C.paper}}>
		<svg viewBox="0 0 1280 720" width="100%" height="100%">
			<rect x={0} y={0} width={1280} height={720} fill={C.paper} />
			<R s={{kind: 'polygon', pts: [[640, 0], [1280, 0], [1280, 720], [520, 720]]}} o={{fill: C.ink, fillStyle: 'solid'}} seed={1} boil={false} />
			<G x={300} y={840} s={1.7}>
				<Penny mood="shocked" />
			</G>
			<G x={960} y={500} s={1.2} r={-10}>
				<CreditCard glow />
			</G>
			<T x={920} y={160} size={118} font="marker" color={C.yellow} stroke={C.ink} rotate={-5}>
				19 YEARS?!
			</T>
		</svg>
	</AbsoluteFill>
);
