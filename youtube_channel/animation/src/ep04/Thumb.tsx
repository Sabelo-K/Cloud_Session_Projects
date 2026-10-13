import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Penny} from '../lib/characters';
import {C, G, R, T} from '../lib/rough';
import {SlotMachine} from './Ep04';

/** Ep. 4 thumbnail: shocked Penny, slot machine, "RIGGED BY MATH". */
export const Ep04Thumb: React.FC = () => (
	<AbsoluteFill style={{background: C.paper}}>
		<svg viewBox="0 0 1280 720" width="100%" height="100%">
			<rect x={0} y={0} width={1280} height={720} fill={C.paper} />
			<R s={{kind: 'polygon', pts: [[640, 0], [1280, 0], [1280, 720], [520, 720]]}} o={{fill: C.ink, fillStyle: 'solid'}} seed={1} boil={false} />
			<G x={300} y={840} s={1.7}>
				<Penny mood="shocked" />
			</G>
			<G x={1000} y={760} s={0.72} r={6}>
				<SlotMachine reels={['7', '7', '$']} />
			</G>
			<T x={930} y={100} size={112} font="marker" color={C.yellow} stroke={C.ink} rotate={-5}>
				RIGGED
			</T>
			<T x={960} y={225} size={96} font="marker" color={C.yellow} stroke={C.ink} rotate={-5}>
				BY MATH
			</T>
		</svg>
	</AbsoluteFill>
);
