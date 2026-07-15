// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

import * as readline from 'readline';
import {execFile} from 'child_process';
import {promisify} from 'util';
import {readFile} from 'fs/promises';
import {randomUUID} from 'crypto';

import {mcpToolSchemas, executeMcpTool} from '../common/mcp_tools.js';

const execFileAsync = promisify(execFile);

/**
 * Helper to fetch a dataset from a local path or a gs:// URI using gcloud storage.
 */
async function loadDataset(path) {
  if (!path) return null;
  if (path.startsWith('gs://')) {
    try {
      // Use gcloud storage to a tmp file to avoid maxBuffer issues
      const tmpPath = `/tmp/mcp_dataset_${randomUUID()}.json`;
      await execFileAsync('gcloud', ['storage', 'cp', path, tmpPath]);
      const data = await readFile(tmpPath, 'utf-8');
      return data;
    } catch (e) {
      throw new Error(
          `Failed to load dataset from GCS (${path}): ${e.message}`,
      );
    }
  }

  // Try treating as local file path
  try {
    const data = await readFile(path, 'utf-8');
    return data;
  } catch (e) {
    throw new Error(
        `Failed to load dataset from local path (${path}): ${e.message}`,
    );
  }
}

// ----------------------------------------------------------------------------
// JSON-RPC / MCP Implementation
// ----------------------------------------------------------------------------

function respond(id, result) {
  process.stdout.write(
      JSON.stringify({
        jsonrpc: '2.0',
        id,
        result,
      }) + '\n',
  );
}

function respondError(id, code, message) {
  process.stdout.write(
      JSON.stringify({
        jsonrpc: '2.0',
        id,
        error: {code, message},
      }) + '\n',
  );
}

// Map of handlers for MCP methods
const handlers = {
  'initialize': async (request) => {
    return {
      protocolVersion: '2024-11-05',
      serverInfo: {
        name: 'Web Tests Analyzer MCP',
        version: '1.0.0',
      },
      capabilities: {
        tools: {},
      },
    };
  },

  'notifications/initialized': async (request) => {
    // Client acknowledges initialization. No response needed.
    return null;
  },

  'tools/list': async (request) => {
    return {tools: mcpToolSchemas};
  },

  'tools/call': async (request) => {
    const {name, arguments: args} = request.params;
    return await executeMcpTool(name, args, loadDataset);
  },
};

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

rl.on('line', async (line) => {
  if (!line.trim()) return;

  let request;
  try {
    request = JSON.parse(line);
  } catch {
    // Ignore unparsable lines
    return;
  }

  // Respond to request
  if (request.method) {
    try {
      const handler = handlers[request.method];
      if (!handler) {
        if (request.id !== undefined) {
          respondError(
              request.id,
              -32601,
              `Method not found: ${request.method}`,
          );
        }
        return;
      }

      const result = await handler(request);

      // If it's not a notification (has an id), respond
      if (request.id !== undefined) {
        respond(request.id, result);
      }
    } catch (e) {
      if (request.id !== undefined) {
        respondError(request.id, -32000, e.message);
      }
    }
  }
});
