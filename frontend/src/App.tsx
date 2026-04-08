import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Discover from './pages/Discover';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Discover />} />
      </Routes>
    </Router>
  );
};

export default App;
