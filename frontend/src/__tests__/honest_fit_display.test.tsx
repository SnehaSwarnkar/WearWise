import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { HonestFitPage } from '../pages/HonestFit';

describe('HonestFit UI Component', () => {
  it('renders without crashing and displays rulebook version header', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <HonestFitPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText('Honest Fit Studio')).toBeDefined();
    expect(screen.getByText('Rev 1.2.1 Rulebook')).toBeDefined();
    expect(screen.getByText('Select Garment for Evaluation')).toBeDefined();
    expect(screen.getByText('Your Silhouette Fit Preference')).toBeDefined();
  });
});
