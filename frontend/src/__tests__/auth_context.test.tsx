import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';

// Helper component to inspect AuthContext
const TestConsumer: React.FC = () => {
  const { role, currentPrincipalId, switchRole, activeProfile, setActiveProfile } = useAuth();
  return (
    <div>
      <span data-testid="role">{role}</span>
      <span data-testid="principal-id">{currentPrincipalId}</span>
      <span data-testid="active-profile">{activeProfile?.profile_id || 'none'}</span>
      <button onClick={() => switchRole('brand', '99999999-9999-9999-9999-999999999999')}>Switch To Brand</button>
      <button
        onClick={() =>
          setActiveProfile({
            profile_id: 'test-profile-123',
            user_id: 'test-user',
            current_revision: 1,
            presentation_gender: 'masculine',
            stature_cm: 180.0,
            reported_weight_kg: 75.0,
            active_measurements: {},
            shape_controls: {
              shoulder_width: 0.5,
              chest_fullness: 0.5,
              belly_fullness: 0.5,
              waist_definition: 0.5,
              arm_fullness: 0.5,
              hip_fullness: 0.5,
              thigh_fullness: 0.5,
              calf_fullness: 0.5,
            },
            latest_asset_url: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        }
      >
        Set Active Profile
      </button>
    </div>
  );
};

describe('AuthContext Component', () => {
  it('provides default shopper user role and allows switching to brand principal', () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    expect(screen.getByTestId('role').textContent).toBe('user');

    // Click switch to brand
    act(() => {
      screen.getByText('Switch To Brand').click();
    });

    expect(screen.getByTestId('role').textContent).toBe('brand');
    expect(screen.getByTestId('principal-id').textContent).toBe('99999999-9999-9999-9999-999999999999');
  });

  it('updates activeProfile across components and persists id', () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    act(() => {
      screen.getByText('Set Active Profile').click();
    });

    expect(screen.getByTestId('active-profile').textContent).toBe('test-profile-123');
  });
});
