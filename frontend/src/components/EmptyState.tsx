import { Package } from 'lucide-react';

interface Props {
  title: string;
  message: string;
}

export default function EmptyState({ title, message }: Props) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 bg-gray-50/50 py-16 px-6">
      <Package className="h-12 w-12 text-gray-300" />
      <h3 className="mt-4 text-lg font-medium text-gray-700">{title}</h3>
      <p className="mt-1 text-sm text-gray-400">{message}</p>
    </div>
  );
}
