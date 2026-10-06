import { Loader2 } from 'lucide-react';

interface Props {
  text?: string;
  className?: string;
}

export default function LoadingSpinner({ text = 'Loading...', className = '' }: Props) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      <p className="mt-3 text-sm text-gray-500">{text}</p>
    </div>
  );
}
