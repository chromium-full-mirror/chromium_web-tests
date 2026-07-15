// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import test from 'node:test';
import assert from 'node:assert';
import fs from 'fs';
import path from 'path';
import {fileURLToPath} from 'url';
import {parseDataset} from '../parser.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('should extract metadata from sample.metrics.json', () => {
  const jsonPath = path.join(__dirname, 'sample.metrics.json');
  const jsonString = fs.readFileSync(jsonPath, 'utf8');

  const map = parseDataset(jsonString);
  const metadata = map.metadata;

  assert.ok(metadata, 'Metadata object should exist');
  assert.strictEqual(
      metadata.hardware_class,
      'Generic Device 14',
      'Hardware class should be correctly extracted',
  );
  assert.strictEqual(
      metadata.cr_os_name,
      'GenericOS',
      'cr_os_name should be correctly extracted',
  );
  assert.strictEqual(
      metadata.system_machine,
      'x86_64',
      'system_machine should be correctly extracted',
  );
  assert.strictEqual(
      metadata.android_build_fingerprint,
      'Generic/device/device:DEV/XX.000000.000/0000000:userdebug/dev-keys',
      'android_build_fingerprint should be correctly extracted',
  );

  // Verify that it correctly handles version
  assert.strictEqual(
      metadata.cr_version,
      '999.0.0000.0-00',
      'cr_version should be correctly extracted from pseudo-metric',
  );

  // Verify that it correctly handles revision
  assert.ok(
      metadata.cr_revision.startsWith('00000000000000000000'),
      'cr_revision should be correctly extracted',
  );

  // Verify that it correctly handles RAM
  assert.strictEqual(
      metadata.system_ram_bytes,
      16288968704,
      'system_ram_bytes should be correctly extracted',
  );
});
