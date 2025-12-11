module.exports = {
  extends: [
    'react-app',
    'react-app/jest'
  ],
  rules: {
    'no-console': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    'object-shorthand': 'error',
    'prefer-template': 'error',
    'arrow-spacing': 'error',
    'prefer-arrow-callback': 'error',
    'arrow-parens': ['error', 'as-needed'],
    'no-duplicate-imports': 'error'
  },
  settings: {
    react: {
      version: 'detect'
    }
  },
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true
  }
};