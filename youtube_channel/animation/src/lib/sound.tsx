import React from 'react';
import {Audio, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';

/** [global seconds, sfx file name (in public/sfx, .wav), volume] */
export type SfxCue = [number, string, number];

/**
 * Music bed + SFX for an episode. The bed sits at `bed` volume, drops out around
 * each `dips` time, and swells after `voEnd` for the end screen.
 */
export const Soundtrack: React.FC<{
	music: string;
	sfx: SfxCue[];
	voEnd: number;
	bed?: number;
	dips?: number[];
}> = ({music, sfx, voEnd, bed = 0.14, dips = []}) => {
	const {fps} = useVideoConfig();
	const vol = (sec: number) => {
		for (const d of dips) {
			if (sec > d - 1 && sec < d) return interpolate(sec, [d - 1, d - 0.7, d - 0.3, d], [bed, 0, 0, bed]);
		}
		if (sec > voEnd - 0.5) return interpolate(sec, [voEnd - 0.5, voEnd + 1], [bed, 0.4], {extrapolateRight: 'clamp'});
		return bed;
	};
	return (
		<>
			<Audio src={staticFile(`sfx/${music}`)} volume={(f) => vol(f / fps)} />
			{sfx.map(([at, file, v], i) => (
				<Sequence key={i} from={Math.round(at * fps)} durationInFrames={Math.round(3.5 * fps)}>
					<Audio src={staticFile(`sfx/${file}.wav`)} volume={v} />
				</Sequence>
			))}
		</>
	);
};
