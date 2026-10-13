import rawData from './latest_data.json';
import { RawRecord, ScoredRecord } from '../types';
import { processAndScoreRecord } from '../utils/scoreCalculator';

export const initialRawRecords: RawRecord[] = rawData as unknown as RawRecord[];

export const initialScoredData: ScoredRecord[] = initialRawRecords.map(r => processAndScoreRecord(r));
