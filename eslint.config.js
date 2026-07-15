// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

const {FlatCompat} = require('@eslint/eslintrc');
const fs = require('fs');
const globals = require('globals');
const js = require('@eslint/js');
const jsdoc = require('eslint-plugin-jsdoc');
const path = require('node:path');
const tsParser = require('@typescript-eslint/parser');
const typescriptEslint = require('@typescript-eslint/eslint-plugin');
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});
// The eslint-config-google uses deprecated jsdoc options that break with the
// latest version of eslint. This has been fixed upstram [1] but no npm package
// has been released since then. Hence patching the config manually.
// [1] https://github.com/google/eslint-config-google/pull/72.
const googleCfg = compat.extends('google');
delete googleCfg[0].rules['valid-jsdoc'];
delete googleCfg[0].rules['require-jsdoc'];
const ignorePath = path.resolve(__dirname, '.prettierignore');
const ignores = fs
    .readFileSync(ignorePath, {encoding: 'utf8'})
    .split('\n')
    .filter((l) => l !== '' && !l.startsWith('#'));
module.exports = [
  // `ignores` has to go on a standalone block at the start otherwise gets
  // overridden by the googleCfg and jsdoc.configs, because the new eslint
  // flat config is so clever.
  {ignores: ignores},
  ...googleCfg,
  {
    files: ['src/**/*.ts'],
    plugins: {
      '@typescript-eslint': typescriptEslint,
      jsdoc,
    },
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: tsParser,
    },
    rules: {
      'indent': 'off',
      'max-len': 'off',
      'operator-linebreak': 'off',
      'quotes': 'off',
      'brace-style': 'off',
      'space-before-function-paren': 'off',
      'generator-star-spacing': 'off',
      'semi-spacing': 'off',
      'no-unused-vars': 'off',
      'no-array-constructor': 'off',
      '@typescript-eslint/no-array-constructor': ['error'],
      'prefer-rest-params': 'off',
      'new-cap': [
        'error',
        {
          capIsNew: false,
          properties: false,
        },
      ],
      'jsdoc/require-jsdoc': 'off',
      'jsdoc/require-param': 'off',
      'jsdoc/require-param-type': 'off',
      'jsdoc/require-returns': 'off',
      'jsdoc/require-returns-type': 'off',
      'jsdoc/tag-lines': 'off',
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/strict-boolean-expressions': [
        'error',
        {
          allowNullableBoolean: true,
          allowNullableObject: true,
          allowNullableString: true,
        },
      ],
    },
  },
  {
    files: ['analysis/**/*.js'],
    rules: {
      'max-len': 'off',
    },
  },
];
