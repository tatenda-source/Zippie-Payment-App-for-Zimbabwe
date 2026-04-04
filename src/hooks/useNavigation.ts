/**
 * Custom hook for navigation state management
 */

import { useState, useCallback } from 'react';
import type { Screen, ScreenData } from '../types/navigation';

export interface UseNavigationReturn {
  currentScreen: Screen;
  screenData: ScreenData;
  navigate: (screen: Screen, data?: ScreenData) => void;
  goBack: () => void;
  canGoBack: boolean;
}

/**
 * Hook for managing navigation state
 * @param initialScreen - Initial screen to show
 * @returns Navigation state and methods
 */
export function useNavigation(initialScreen: Screen = 'home'): UseNavigationReturn {
  const [currentScreen, setCurrentScreen] = useState<Screen>(initialScreen);
  const [screenData, setScreenData] = useState<ScreenData>({});
  const [history, setHistory] = useState<Screen[]>([initialScreen]);

  const navigate = useCallback((screen: Screen, data?: ScreenData) => {
    setCurrentScreen(screen);
    setScreenData(data || {});
    setHistory(prev => [...prev, screen]);
  }, []);

  const goBack = useCallback(() => {
    if (history.length > 1) {
      const newHistory = history.slice(0, -1);
      const previousScreen = newHistory[newHistory.length - 1];
      setHistory(newHistory);
      setCurrentScreen(previousScreen);
      setScreenData({});
    } else {
      // Default to home if no history
      setCurrentScreen('home');
      setScreenData({});
    }
  }, [history]);

  const canGoBack = history.length > 1;

  return {
    currentScreen,
    screenData,
    navigate,
    goBack,
    canGoBack,
  };
}
