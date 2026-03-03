'use client';

interface EthAmountProps {
  amount: number;
  className?: string;
}

export default function EthAmount({ amount, className }: EthAmountProps) {
  const formatted =
    amount % 1 === 0 ? amount.toFixed(1) : parseFloat(amount.toFixed(4)).toString();

  return (
    <span className={className} data-testid="eth-amount">
      <span className="font-mono font-semibold">{formatted}</span>
      <span className="ml-1 text-white/50 text-sm">ETH</span>
    </span>
  );
}
