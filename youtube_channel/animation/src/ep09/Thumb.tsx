import React from 'react';
import {Penny} from '../lib/characters';
import {Card, Phone} from '../lib/props';
import {C, G, T} from '../lib/rough';
import {Burst, Glow, Headline, NewsBar, ThumbFrame, ThumbPenny} from '../lib/thumbkit';
import {Marcus} from './Ep09';

/**
 * Ep. 9 thumbnail. POV Finance formula (calm "YOU" + red arrow, contrasted with the person
 * getting it wrong) inside the house Breaking News frame.
 */
export const Ep09Thumb: React.FC = () => (
	<ThumbFrame>
		<Burst bg="#1E2A4A" ray="#2B3A63" cx={640} cy={330} />
		<G x={210} y={830} s={1.75}>
			<ThumbPenny><Penny mood="confident" look={1} /></ThumbPenny>
		</G>
		<Headline x={430} y={190} size={84} color={C.red}>YOU</Headline>
		<G x={650} y={880} s={1.45}>
			<Marcus mood="shocked" />
		</G>
		<Glow x={1050} y={400} r={230} />
		<G x={1050} y={400} s={1.05} r={6}>
			<Phone>
				<T x={0} y={-150} size={22} color={C.shadow}>balance</T>
				<T x={0} y={-100} size={44} font="marker" color={C.green}>$184,000</T>
				<G x={0} y={30}>
					<Card w={210} h={150} seed={9} fill={C.white}>
						<T x={0} y={-30} size={26} font="marker" color={C.red}>PAY 15% TAX</T>
						<T x={0} y={30} size={42} font="marker" color={C.red}>$27,600</T>
					</Card>
				</G>
			</Phone>
		</G>
		<Headline x={640} y={78} size={84}>
			&quot;WRONG NUMBER&quot;
		</Headline>
		<NewsBar text="POV: YOU KNEW EXACTLY WHAT IT WAS" />
	</ThumbFrame>
);
