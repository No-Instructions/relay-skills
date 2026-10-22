#!/usr/bin/env node
// Activate a prepared vault through the CLI socket of a normally running Obsidian.
import { readFile, realpath } from 'node:fs/promises';
import { createConnection } from 'node:net';
import { homedir, platform, userInfo } from 'node:os';
import { join } from 'node:path';
import { parseArgs } from 'node:util';

const defaults = new URL('../assets/defaults/', import.meta.url);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function request(endpoint, argv, cwd) {
  return new Promise((resolve, reject) => {
    const socket = createConnection(endpoint);
    let output = '';
    let settled = false;
    const finish = error => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket.destroy();
      if (error) reject(error); else resolve(output);
    };
    const timer = setTimeout(() => finish(new Error('Obsidian CLI request timed out')), 10000);
    socket.setEncoding('utf8');
    socket.on('error', finish);
    socket.on('connect', () => socket.write(JSON.stringify({ argv, cwd, tty: false }) + '\n'));
    socket.on('data', chunk => {
      output += chunk;
      if (output.length > 4 * 1024 * 1024) finish(new Error('Obsidian CLI response is too large'));
    });
    socket.on('end', () => finish());
  });
}

async function evaluate(endpoint, vault, expression) {
  const output = await request(endpoint, ['eval', `code=JSON.stringify(${expression})`], vault);
  const result = output.split('\n').filter(line => line.startsWith('=> ')).at(-1);
  if (!result) throw new Error(output.trim() || 'Obsidian CLI returned no result');
  return JSON.parse(result.slice(3));
}

function socketPaths() {
  if (platform() === 'win32') return [`\\\\.\\pipe\\obsidian-cli-${userInfo().username}`];
  if (platform() === 'darwin') return [join(homedir(), '.obsidian-cli.sock')];
  return [...new Set([
    join(process.env.XDG_RUNTIME_DIR || homedir(), '.obsidian-cli.sock'),
    join(homedir(), '.flatpak/md.obsidian.Obsidian/xdg-run/.obsidian-cli.sock'),
  ])];
}

async function main() {
  const { values } = parseArgs({ options: {
    vault: { type: 'string' }, socket: { type: 'string' },
    'plugins-file': { type: 'string' }, 'storage-file': { type: 'string' },
    timeout: { type: 'string', default: '60' }, check: { type: 'boolean', default: false },
  } });
  if (!values.vault) throw new Error('Usage: activate_plugins.mjs --vault PATH [--socket PATH] [--check]');
  const vault = await realpath(values.vault);
  const endpoints = values.socket ? [values.socket] : socketPaths();
  const timeout = Number(values.timeout);
  if (!Number.isFinite(timeout) || timeout <= 0) throw new Error('Timeout must be a positive number');
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
  let lastError = 'No running Obsidian CLI socket matches the requested vault';
  while (Date.now() < deadline) {
    let cliDisabled = false;
    let matched = false;
    for (const endpoint of endpoints) {
      try {
        const state = await evaluate(endpoint, vault, probe);
        if (!state) continue;
        matched = true;
        if (state.restricted === !enabled && Object.values(state.plugins).every(version => enabled ? Boolean(version) : !version)) {
          console.log(JSON.stringify(state, null, 2));
          return;
        }
        lastError = `Vault is not ready: ${JSON.stringify(state)}`;
        if (!values.check && !reloaded) {
          await evaluate(endpoint, vault, `(() => {
            const state = ${probe};
            if (!state) throw new Error('Vault changed before activation');
            localStorage.setItem('enable-plugin-' + app.appId, ${JSON.stringify(storage['enable-plugin'])});
            setTimeout(() => window.location.reload(), 100);
            return true;
          })()`);
          reloaded = true;
        }
      } catch (error) {
        lastError = error.message;
        cliDisabled ||= lastError.startsWith('Command line interface is not enabled');
      }
    }
    if (cliDisabled && !matched) {
      throw new Error('Obsidian CLI is disabled. Apply profile.json to the stopped profile, then reopen Obsidian normally.');
    }
    await delay(250);
  }
  throw new Error(lastError);
}

main().catch(error => { console.error(`Error: ${error.message}`); process.exitCode = 1; });
