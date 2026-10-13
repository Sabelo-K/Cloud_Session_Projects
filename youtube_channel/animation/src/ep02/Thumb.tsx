import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Penny} from '../lib/characters';
import {HotDog, MemberCard} from '../lib/props2';
import {C, G, R, T} from '../lib/rough';

/** Ep. 2 thumbnail: Penny holding a giant membership card, the $1.50 hot dog, "IT'S THE CARD". */
export const Ep02Thumb: React.FC = () => (
	<AbsoluteFill style={{background: C.paper}}>
		<svg viewBox="0 0 1280 720" width="100%" height="100%">
			<rect x={0} y={0} width={1280} height={720} fill={C.paper} />
			<R s={{kind: 'polygon', pts: [[640, 0], [1280, 0], [1280, 720], [520, 720]]}} o={{fill: C.red, fillStyle: 'solid'}} seed={1} boil={false} />
			<G x={300} y={840} s={1.7}>
				<Penny mood="shocked" />
			</G>
			<G x={930} y={470} s={1.25} r={-8}>
				<MemberCard />
			</G>
			<G x={360} y={640} s={0.65}>
				<HotDog />
			</G>
			<T x={940} y={150} size={170} font="marker" color={C.yellow} stroke={C.ink} rotate={-5}>
				$5.3B
			</T>
		</svg>
	</AbsoluteFill>
);
