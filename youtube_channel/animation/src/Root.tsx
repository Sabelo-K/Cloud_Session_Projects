import React from 'react';
import {Composition} from 'remotion';
import {EP01_SECONDS, Ep01} from './ep01/Ep01';
import {Ep01Thumb} from './ep01/Thumb';
import {EP02_SECONDS, Ep02} from './ep02/Ep02';
import {Ep02Thumb} from './ep02/Thumb';
import {EP03_SECONDS, Ep03} from './ep03/Ep03';
import {Ep03Thumb} from './ep03/Thumb';
import {EP04_SECONDS, Ep04} from './ep04/Ep04';
import {Ep04Thumb} from './ep04/Thumb';
import {Ep08Thumb} from './ep08/Thumb';
import {Ep07Thumb} from './ep07/Thumb';
import {Ep06Thumb} from './ep06/Thumb';
import {Ep05Thumb} from './ep05/Thumb';
import {EP05_SECONDS, Ep05} from './ep05/Ep05';
import {EP06_SECONDS, Ep06} from './ep06/Ep06';
import {EP07_SECONDS, Ep07} from './ep07/Ep07';
import {EP08_SECONDS, Ep08} from './ep08/Ep08';
import {SHORTS, ShortComp, shortSeconds} from './shorts/Shorts';
import {SHORT_THUMBS, ShortThumb} from './shorts/ShortThumbs';

import {Avatar, Banner, Watermark} from './brand/Brand';

const FPS = 30;

export const RemotionRoot: React.FC = () => (
	<>
	<Composition id="Ep01" component={Ep01} durationInFrames={Math.round(EP01_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep01Thumb" component={Ep01Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep02" component={Ep02} durationInFrames={Math.round(EP02_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep02Thumb" component={Ep02Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep03" component={Ep03} durationInFrames={Math.round(EP03_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep03Thumb" component={Ep03Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep04" component={Ep04} durationInFrames={Math.round(EP04_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep04Thumb" component={Ep04Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep05" component={Ep05} durationInFrames={Math.round(EP05_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep06" component={Ep06} durationInFrames={Math.round(EP06_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep07" component={Ep07} durationInFrames={Math.round(EP07_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep08" component={Ep08} durationInFrames={Math.round(EP08_SECONDS * FPS)} fps={FPS} width={1920} height={1080} />
	<Composition id="Ep05Thumb" component={Ep05Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep06Thumb" component={Ep06Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep07Thumb" component={Ep07Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	<Composition id="Ep08Thumb" component={Ep08Thumb} durationInFrames={1} fps={FPS} width={1280} height={720} />
	{SHORTS.map((d, i) => (
		<Composition key={d.id} id={d.id} component={ShortComp} defaultProps={{i}} durationInFrames={Math.round(shortSeconds(d) * FPS)} fps={FPS} width={1080} height={1920} />
	))}
	{SHORT_THUMBS.map((d, i) => (
		<Composition key={d.id} id={d.id} component={ShortThumb} defaultProps={{i}} durationInFrames={1} fps={FPS} width={1080} height={1920} />
	))}
	<Composition id="Avatar" component={Avatar} durationInFrames={1} fps={FPS} width={800} height={800} />
	<Composition id="Banner" component={Banner} durationInFrames={1} fps={FPS} width={2560} height={1440} />
	<Composition id="Watermark" component={Watermark} durationInFrames={1} fps={FPS} width={150} height={150} />
	</>
);
