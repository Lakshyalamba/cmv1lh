const number = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 1 });
export const mw = (value: number | null, signed = false) => value === null ? '—' : `${signed && value > 0 ? '+' : ''}${number.format(value)}`;
export const dateLabel = (value: string) => new Intl.DateTimeFormat('en-GB', {
  day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/London',
}).format(new Date(`${value}T12:00:00Z`));
export const timeLabel = (value: string) => new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone: 'Europe/London',
}).format(new Date(value));
export const publicationLabel = (value: string) => new Intl.DateTimeFormat('en-GB', {
  day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone: 'Europe/London',
}).format(new Date(value));
