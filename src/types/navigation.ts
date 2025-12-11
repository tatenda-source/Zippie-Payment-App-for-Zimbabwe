/**
 * Navigation-related type definitions
 */

export type Screen =
    | 'home'
    | 'send'
    | 'request'
    | 'history'
    | 'payment-success';

export interface ScreenData {
    symbol?: string;
    paymentData?: any;
    [key: string]: any;
}

export interface NavigationState {
    currentScreen: Screen;
    screenData: ScreenData;
    history: Screen[];
}
