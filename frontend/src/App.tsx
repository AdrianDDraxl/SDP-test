import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import AuthorMergePage from './pages/AuthorMergePage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/repo/:id" element={<DashboardPage />} />
        <Route path="/repo/:id/authors" element={<AuthorMergePage />} />
      </Route>
    </Routes>
  );
}
