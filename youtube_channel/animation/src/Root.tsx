import React from 'react';
import {Composition} from 'remotion';
import {EP01_SECONDS, Ep01} from './ep01/Ep01';
import {Ep01Thumb} from './ep01/Thumb';
import {EP02_SECONDS, Ep02} from './ep02/Ep02';
import {Ep02Thumb} from './ep02/Thumb';
import {EP03_SECONDS, Ep03} from './ep03/Ep03';
import {Ep03Thumb} from './ep03/Thumb';

const FPS = 30;

export const RemotionRoot: React.FC = () => (
	<>
	<Composition id="Ep01" component={Ep01} durationInFrames={Math.round(EP01_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep01Thumb" component={Ep01Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep02" component={Ep02} durationInFrames={Math.round(EP02_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep02Thumb" component={Ep02Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep03" component={Ep03} durationInFrames={Math.round(EP03_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep03Thumb" component={Ep03Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	</>
);
