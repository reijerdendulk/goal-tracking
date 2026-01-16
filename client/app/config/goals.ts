export interface GoalField {
  key: string;
  label: string;
  type: 'number';
}

export interface Goal {
  id: string;
  name: string;
  navLabel: string;
  description: string;
  hrefNew: string;
  unitLabel?: string;
  fields: GoalField[];
}

export const GOALS: Goal[] = [
  {
    id: 'runs',
    name: 'Runs',
    navLabel: 'Log Run',
    description: 'Track your running activities',
    hrefNew: '/runs/new',
    fields: [
      { key: 'miles', label: 'Miles', type: 'number' },
      { key: 'paceMinPerMile', label: 'Minutes/Mile', type: 'number' },
    ],
  },
  {
    id: 'hangouts',
    name: 'Hangouts',
    navLabel: 'Log Hangout',
    description: 'Track social hangouts',
    hrefNew: '/hangouts/new',
    unitLabel: 'hangouts',
    fields: [{ key: 'count', label: 'Hangouts', type: 'number' }],
  },
  {
    id: 'work-sessions',
    name: 'Work Sessions',
    navLabel: 'Log Work Session',
    description: 'Track work sessions',
    hrefNew: '/work/new',
    unitLabel: 'minutes',
    fields: [{ key: 'minutes', label: 'Minutes', type: 'number' }],
  },
];

export function getGoalById(id: string): Goal | undefined {
  return GOALS.find((g) => g.id === id);
}
