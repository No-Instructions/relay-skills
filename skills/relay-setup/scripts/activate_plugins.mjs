#!/usr/bin/env node
// Complete a prepared vault's first launch through Obsidian's local CDP endpoint.
import { readFile, realpath } from 'node:fs/promises';
import { parseArgs } from 'node:util';

const defaults = new URL('../assets/defaults/', import.meta.url);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function request(url, method, params = {}) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(url);
    let settled = false;
    const finish = (error, result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket.close();
      if (error) reject(error); else resolve(result);
    };
    const timer = setTimeout(() => finish(new Error(`CDP timed out: ${method}`)), 10000);
    socket.addEventListener('error', () => finish(new Error('CDP connection failed')));
    socket.addEventListener('open', () => socket.send(JSON.stringify({ id: 1, method, params })));
    socket.addEventListener('message', event => {
      const reply = JSON.parse(event.data);
      if (reply.id !== 1) return;
      if (reply.error) return finish(new Error(reply.error.message));
      if (reply.result?.exceptionDetails) {
        return finish(new Error(reply.result.exceptionDetails.exception?.description || 'Evaluation failed'));
      }
      finish(null, reply.result);
    });
  });
}

async function evaluate(url, expression) {
  const result = await request(url, 'Runtime.evaluate', {
    expression, awaitPromise: true, returnByValue: true,
  });
  return result.result?.value;
}

async function main() {
  if (typeof WebSocket === 'undefined') throw new Error('Node.js 22 or later is required');
  const { values } = parseArgs({ options: {
    vault: { type: 'string' }, port: { type: 'string', default: '9222' },
    'plugins-file': { type: 'string' }, 'storage-file': { type: 'string' },
    timeout: { type: 'string', default: '60' }, check: { type: 'boolean', default: false },
  } });
  if (!values.vault) throw new Error('Usage: activate_plugins.mjs --vault PATH [--port 9222] [--check]');
  const vault = await realpath(values.vault);
  const port = Number(values.port), timeout = Number(values.timeout);
  if (!Number.isInteger(port) || port < 1 || port > 65535 || !Number.isFinite(timeout) || timeout <= 0) {
    throw new Error('Port and timeout must be positive numbers; port must be an integer below 65536');
  }
  const ids = JSON.parse(await readFile(values['plugins-file'] || new URL('community-plugins.json', defaults), 'utf8'));
  const storage = JSON.parse(await readFile(values['storage-file'] || new URL('local-storage.json', defaults), 'utf8'));
  if (!Array.isArray(ids) || !ids.every(id => typeof id === 'string' && /^[A-Za-z0-9_-]+$/.test(id))) {
    throw new Error('Expected an array of plugin ids');
  }
  if (!storage || Object.keys(storage).length !== 1 || !['true', 'false'].includes(storage['enable-plugin'])) {
    throw new Error('Local storage defaults must contain only "enable-plugin": "true" or "false"');
  }
  const enabled = storage['enable-plugin'] === 'true';
  const probe = `(() => {
    if (typeof app === 'undefined' || !app.vault?.adapter?.basePath || !app.plugins || !app.appId) return null;
    if (require('fs').realpathSync(app.vault.adapter.basePath) !== ${JSON.stringify(vault)}) return null;
    return {
      vault: app.vault.adapter.basePath,
      restricted: localStorage.getItem('enable-plugin-' + app.appId) !== 'true',
      plugins: Object.fromEntries(${JSON.stringify(ids)}.map(id => [id, app.plugins.plugins[id]?.manifest.version || null]))
    };
  })()`;
  const deadline = Date.now() + timeout * 1000;
  let reloaded = false;
  let lastError = 'No open Obsidian window matches the requested vault';
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(3000) });
      if (!response.ok) throw new Error(`CDP discovery returned HTTP ${response.status}`);
      const targets = await response.json();
      for (const target of targets.filter(item => item.type === 'page' && item.webSocketDebuggerUrl)) {
        const state = await evaluate(target.webSocketDebuggerUrl, probe);
        if (!state) continue;
        if (state.restricted === !enabled && Object.values(state.plugins).every(version => enabled ? Boolean(version) : !version)) {
          console.log(JSON.stringify(state, null, 2));
          return;
        }
        lastError = `Vault is not ready: ${JSON.stringify(state)}`;
        if (!values.check && !reloaded) {
          await evaluate(target.webSocketDebuggerUrl, `(() => {
            const state = ${probe};
            if (!state) throw new Error('Vault changed before activation');
            localStorage.setItem('enable-plugin-' + app.appId, ${JSON.stringify(storage['enable-plugin'])});
          })()`);
          await request(target.webSocketDebuggerUrl, 'Page.reload');
          reloaded = true;
        }
      }
    } catch (error) {
      lastError = error.message;
    }
    await delay(250);
  }
  throw new Error(lastError);
}

main().catch(error => { console.error(`Error: ${error.message}`); process.exitCode = 1; });
