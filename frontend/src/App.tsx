import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Discover from './pages/Discover';
import Detail from './pages/Detail';
import ErrorBoundary from './components/ErrorBoundary';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<Discover />} />
          <Route path="/detail/:id" element={<Detail />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
};

export default App;
