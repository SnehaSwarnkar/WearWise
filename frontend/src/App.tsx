import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { BodyProfilePage } from './pages/BodyProfile';
import { AvatarStudio } from './pages/AvatarStudio';
import { GarmentStudio } from './pages/GarmentStudio';
import { HonestFitPage } from './pages/HonestFit';

export const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/profile" element={<BodyProfilePage />} />
      <Route path="/avatar" element={<AvatarStudio />} />
      <Route path="/garments" element={<GarmentStudio />} />
      <Route path="/fit" element={<HonestFitPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
