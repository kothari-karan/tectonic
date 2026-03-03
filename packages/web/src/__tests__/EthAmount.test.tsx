import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import EthAmount from '@/components/EthAmount';

describe('EthAmount', () => {
  it('formats whole numbers with one decimal place', () => {
    render(<EthAmount amount={5} />);
    const el = screen.getByTestId('eth-amount');
    expect(el).toHaveTextContent('5.0');
    expect(el).toHaveTextContent('ETH');
  });

  it('formats decimal amounts correctly', () => {
    render(<EthAmount amount={2.5} />);
    const el = screen.getByTestId('eth-amount');
    expect(el).toHaveTextContent('2.5');
    expect(el).toHaveTextContent('ETH');
  });

  it('formats small decimal amounts', () => {
    render(<EthAmount amount={0.001} />);
    const el = screen.getByTestId('eth-amount');
    expect(el).toHaveTextContent('0.001');
  });

  it('trims trailing zeros to 4 decimal places', () => {
    render(<EthAmount amount={1.23456789} />);
    const el = screen.getByTestId('eth-amount');
    expect(el).toHaveTextContent('1.2346');
  });

  it('displays ETH suffix', () => {
    render(<EthAmount amount={1} />);
    expect(screen.getByTestId('eth-amount')).toHaveTextContent('ETH');
  });

  it('applies custom className', () => {
    render(<EthAmount amount={1} className="custom-class" />);
    expect(screen.getByTestId('eth-amount')).toHaveClass('custom-class');
  });

  it('handles zero amount', () => {
    render(<EthAmount amount={0} />);
    const el = screen.getByTestId('eth-amount');
    expect(el).toHaveTextContent('0.0');
    expect(el).toHaveTextContent('ETH');
  });
});
