import { NavLink, useParams } from 'react-router-dom';
import { Home, BarChart3, Users } from 'lucide-react';

export default function Sidebar() {
  const { id } = useParams();

  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-50 text-blue-700'
        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
    }`;

  return (
    <aside className="hidden md:flex w-56 flex-col border-r border-gray-200 bg-white px-3 py-4">
      <nav className="flex flex-col gap-1">
        <NavLink to="/" end className={linkCls}>
          <Home className="h-4 w-4" />
          Repositories
        </NavLink>
        {id && (
          <>
            <NavLink to={`/repo/${id}`} end className={linkCls}>
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </NavLink>
            <NavLink to={`/repo/${id}/authors`} className={linkCls}>
              <Users className="h-4 w-4" />
              Author Merge
            </NavLink>
          </>
        )}
      </nav>
    </aside>
  );
}
