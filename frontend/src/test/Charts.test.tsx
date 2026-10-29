import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { ErrorChart, GenerationChart } from '../Charts';
it('shows an explicit empty generation chart without inventing a series', () => {
  render(<GenerationChart rows={[]}/>);
  expect(screen.getByText('No generation observations for this delivery day.')).toBeInTheDocument();
});
it('does not treat absent errors as a zero-error chart', () => {
  render(<ErrorChart rows={[]}/>);
  expect(screen.getByText('No matched observations to calculate forecast error.')).toBeInTheDocument();
});
