import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Penny} from '../lib/characters';
import {Coin, Gear} from '../lib/props';
import {C, G, R, T} from '../lib/rough';

/** Profile picture, 800x800 (YouTube shows it as a circle, so keep everything central). */
export const Avatar: React.FC = () => (
	<AbsoluteFill style={{background: C.yellow}}>
		<svg viewBox="0 0 800 800" width="100%" height="100%">
			<rect x={0} y={0} width={800} height={800} fill={C.yellow} />
			<G x={400} y={400}>
				<Gear r={330} teeth={14} fill={C.paper} seed={1} />
				<R s={{kind: 'circle', x: 0, y: 0, d: 300}} o={{fill: C.yellow, fillStyle: 'solid', stroke: 'none'}} seed={9} boil={false} />
			</G>
			<G x={400} y={1010} s={1.9}>
				<Penny mood="happy" />
			</G>
		</svg>
	</AbsoluteFill>
);

/**
 * Channel banner, 2560x1440. Only the centre 1546x423 is safe on every device,
 * so the logo and tagline live there; the rest is decoration.
 */
export const Banner: React.FC = () => (
	<AbsoluteFill style={{background: C.paper}}>
		<svg viewBox="0 0 2560 1440" width="100%" height="100%">
			<rect x={0} y={0} width={2560} height={1440} fill={C.paper} />
			{/* decorative gears and coins outside the safe area */}
			<G x={250} y={300}>
				<Gear r={220} fill={C.blue} seed={2} />
			</G>
			<G x={2330} y={1150}>
				<Gear r={260} fill={C.green} seed={3} />
			</G>
			<G x={2300} y={250}>
				<Gear r={160} fill={C.red} seed={4} />
			</G>
			<G x={300} y={1180}>
				<Gear r={170} fill={C.yellow} seed={5} />
			</G>
			{[
				[600, 420],
				[1950, 980],
				[700, 1050],
				[1900, 430],
			].map(([x, y], i) => (
				<G key={i} x={x} y={y} s={1.3}>
					<Coin seed={i} />
				</G>
			))}
			{/* safe area: x 507–2053, y 508–931 */}
			<G x={760} y={915} s={0.98}>
				<Penny mood="happy" wave />
			</G>
			<T x={1480} y={590} size={140} font="marker">
				MONEY
			</T>
			<T x={1480} y={725} size={140} font="marker" color={C.yellow} stroke={C.ink}>
				MECHANICS
			</T>
			<T x={1480} y={825} size={48}>
				How the money machines around you actually work
			</T>
			<G x={1480} y={890}>
				<R s={{kind: 'rect', x: -300, y: -34, w: 600, h: 68}} o={{fill: C.red, fillStyle: 'solid'}} seed={6} boil={false} />
				<T x={0} y={4} size={40} font="marker" color={C.white}>
					NEW VIDEOS TUE + FRI
				</T>
			</G>
		</svg>
	</AbsoluteFill>
);

/** Video watermark ("branding"), 150x150, shown bottom-right on every video. */
export const Watermark: React.FC = () => (
	<AbsoluteFill style={{background: 'transparent'}}>
		<svg viewBox="0 0 150 150" width="100%" height="100%">
			<R s={{kind: 'circle', x: 75, y: 75, d: 136}} o={{fill: C.yellow, fillStyle: 'solid', strokeWidth: 5}} seed={7} boil={false} />
			<T x={75} y={64} size={28} font="marker">
				MONEY
			</T>
			<T x={75} y={92} size={17} font="marker" color={C.red}>
				MECHANICS
			</T>
		</svg>
	</AbsoluteFill>
);
