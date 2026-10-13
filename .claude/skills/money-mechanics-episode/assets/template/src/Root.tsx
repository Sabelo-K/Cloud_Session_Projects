import React from 'react';
import {Composition} from 'remotion';
// Register each episode and its thumbnail here, e.g.:
// import {EP04_SECONDS, Ep04} from './ep04/Ep04';
// import {Ep04Thumb} from './ep04/Thumb';

const FPS = 30;

export const RemotionRoot: React.FC = () => (
	<>
		{/* <Composition id="Ep04" component={Ep04} durationInFrames={Math.round(EP04_SECONDS * FPS)} fps={FPS} width={1920} height={1080} /> */}
		{/* <Composition id="Ep04Thumb" component={Ep04Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} /> */}
	</>
);
