import { useEffect } from 'react';

import { currentUserState } from '@/auth/states/currentUserState';
import { isWelcomeAnimationVisibleState } from '@/onboarding/states/isWelcomeAnimationVisibleState';
import { useAtomStateValue } from '@/ui/utilities/state/jotai/hooks/useAtomStateValue';
import { useSetAtomState } from '@/ui/utilities/state/jotai/hooks/useSetAtomState';
import { OnboardingStatus } from '~/generated-metadata/graphql';

const SESSION_STORAGE_KEY = 'compasWelcomeAnimationShown';

// CRITERIUM COMPÁS: la animación de bienvenida sale en cada inicio de sesión,
// no solo en el onboarding. Una vez por sesión de navegador.
export const WelcomeAnimationOnSessionStartEffect = () => {
  const currentUser = useAtomStateValue(currentUserState);
  const setIsWelcomeAnimationVisible = useSetAtomState(
    isWelcomeAnimationVisibleState,
  );

  useEffect(() => {
    if (currentUser?.onboardingStatus !== OnboardingStatus.COMPLETED) {
      return;
    }
    if (window.sessionStorage.getItem(SESSION_STORAGE_KEY) === '1') {
      return;
    }
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, '1');
    setIsWelcomeAnimationVisible(true);
  }, [currentUser?.onboardingStatus, setIsWelcomeAnimationVisible]);

  return null;
};
