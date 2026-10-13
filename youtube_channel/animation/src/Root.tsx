import React from 'react';
import {Composition} from 'remotion';
import {EP01_SECONDS, Ep01} from './ep01/Ep01';
import {Ep01Thumb} from './ep01/Thumb';

const FPS = 30;

export const RemotionRoot: React.FC = () => (
	<>
	<Composition id="Ep01" component={Ep01} durationInFrames={Math.round(EP01_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep01Thumb" component={Ep01Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	</>
);
