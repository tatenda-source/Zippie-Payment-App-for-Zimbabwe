/**
 * Account-related type definitions
 */

export type Currency = 'USD' | 'ZWL';

export type AccountType = 'primary' | 'savings' | 'zwl';

export interface Account {
    id: string;
    name: string;
    balance: number;
    currency: Currency;
    color: string;
    type?: AccountType;
}

export interface AccountUpdate {
    id: string;
    balance?: number;
    name?: string;
    color?: string;
}
