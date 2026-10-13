import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Broker, Penny} from '../lib/characters';
import {Cash} from '../lib/props';
import {C, G, R, T} from '../lib/rough';

/** Ep. 1 thumbnail, concept A: shocked Penny, huge hand offering tiny cash, "$150?!". */
export const Ep01Thumb: React.FC = () => (
	<AbsoluteFill style={{background: C.paper}}>
		<svg viewBox="0 0 1280 720" width="100%" height="100%">
			<rect x={0} y={0} width={1280} height={720} fill={C.paper} />
			<R s={{kind: 'polygon', pts: [[700, 0], [1280, 0], [1280, 720], [560, 720]]}} o={{fill: C.ink, fillStyle: 'solid'}} seed={1} boil={false} />
			<G x={330} y={830} s={1.75}>
				<Penny mood="shocked" holdGuitar />
			</G>
			<G x={1090} y={820} s={1.3}>
				<Broker mood="smirk" arm={1} look={-1} />
			</G>
			<G x={810} y={650} s={0.9} r={-10}>
				<Cash />
			</G>
			<T x={930} y={190} size={190} font="marker" color={C.yellow} stroke={C.ink} rotate={-6}>
				$150?!
			</T>
		</svg>
	</AbsoluteFill>
);
