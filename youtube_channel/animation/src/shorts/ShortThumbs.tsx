import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Penny, Mood} from '../lib/characters';
import {C, G} from '../lib/rough';
import {Burst, Glow, Headline, ThumbPenny} from '../lib/thumbkit';

/** Vertical (1080x1920) "Breaking News" covers for the Shorts. */
type T = {id: string; bg: string; ray: string; top: string; big: string; line2: string; strip: string; mood: Mood};

const ARIAL = 'Arial Black, Arial, sans-serif';

const Cover: React.FC<{d: T}> = ({d}) => (
	<AbsoluteFill>
		<svg viewBox="0 0 1080 1920" width="100%" height="100%">
			<Burst bg={d.bg} ray={d.ray} cx={540} cy={760} w={1080} h={1920} />
			{/* breaking banner */}
			<rect x={0} y={90} width={1080} height={130} fill="#D7141A" />
			<text x={60} y={160} dominantBaseline="middle" fontFamily={ARIAL} fontWeight={900} fontStyle="italic" fontSize={78} fill={C.white}>
				BREAKING NEWS
			</text>
			<g transform="translate(930 155)">
				<rect x={-90} y={-36} width={180} height={72} rx={8} fill={C.white} />
				<circle cx={-52} cy={0} r={14} fill="#D7141A" />
				<text x={18} y={4} textAnchor="middle" dominantBaseline="middle" fontFamily={ARIAL} fontWeight={900} fontSize={40} fill="#D7141A">
					LIVE
				</text>
			</g>
			<Headline x={540} y={390} size={d.top.length > 12 ? 84 : 110} color={C.white} rotate={-3}>
				{d.top}
			</Headline>
			<Glow x={540} y={720} r={420} />
			<Headline x={540} y={700} size={d.big.length > 6 ? 200 : 260} rotate={-4}>
				{d.big}
			</Headline>
			<Headline x={540} y={930} size={d.line2.length > 18 ? 70 : d.line2.length > 14 ? 84 : 100} color={C.white} rotate={-3}>
				{d.line2}
			</Headline>
			<G x={540} y={1650} s={1.55}>
				<ThumbPenny>
					<Penny mood={d.mood} />
				</ThumbPenny>
			</G>
			{/* lower third */}
			<rect x={0} y={1640} width={1080} height={150} fill={C.white} />
			<rect x={0} y={1640} width={22} height={150} fill="#D7141A" />
			<text x={540} y={1717} textAnchor="middle" dominantBaseline="middle" fontFamily={ARIAL} fontWeight={900} fontSize={d.strip.length > 20 ? 62 : 74} fill={C.ink}>
				{d.strip}
			</text>
			<rect x={0} y={1790} width={1080} height={130} fill="#111" />
			<text x={540} y={1855} textAnchor="middle" dominantBaseline="middle" fontFamily={ARIAL} fontWeight={900} fontSize={52} fill={C.yellow}>
				MONEY MECHANICS
			</text>
		</svg>
	</AbsoluteFill>
);

export const SHORT_THUMBS: T[] = [
	{id: 'Short01Thumb', bg: '#1E3A8A', ray: '#2747A8', top: 'UNSPENT GIFT CARDS', big: '$23B', line2: 'IN YOUR DRAWER', strip: 'WHERE GIFT CARDS GO', mood: 'shocked'},
	{id: 'Short02Thumb', bg: '#B91C1C', ray: '#D02A2A', top: 'YOUR GYM WANTS', big: 'YOU', line2: 'TO STAY HOME', strip: 'HOW GYMS REALLY PROFIT', mood: 'shocked'},
	{id: 'Short03Thumb', bg: '#5B21B6', ray: '#6D31CC', top: 'PRINTER INK COSTS', big: '7X', line2: 'THE PRICE OF CHAMPAGNE', strip: 'THE PRINTER INK SCAM', mood: 'shocked'},
	{id: 'Short04Thumb', bg: '#065F46', ray: '#0A7A5A', top: 'EXTENDED WARRANTY?', big: '50%+', line2: 'PROFIT MARGIN', strip: 'DON\'T BUY THE WARRANTY', mood: 'shocked'},
	{id: 'Short05Thumb', bg: '#9A3412', ray: '#B4441A', top: 'DELTA MADE', big: '$8.2B', line2: 'SELLING MILES', strip: 'AIRLINES SELL MILES', mood: 'shocked'},
];

export const ShortThumb: React.FC<{i: number}> = ({i}) => <Cover d={SHORT_THUMBS[i]} />;
