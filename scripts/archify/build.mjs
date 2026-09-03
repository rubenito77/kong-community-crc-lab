// Generate documentation only. Never invokes oc, kubectl, Helm, npm or npx.
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const lock = JSON.parse(readFileSync(resolve(root, 'docs/archify/archify.lock.json'), 'utf8'));
const checkout = process.argv[2];
if (!checkout) {
  console.error('Usage: node scripts/archify/build.mjs <archify-checkout> [crc|http-log|opentelemetry]');
  process.exit(2);
}
const toolRoot = resolve(checkout);
function run(command, args, cwd = root) {
  const result = spawnSync(command, args, {
    cwd, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024,
    env: { ...process.env, ARCHIFY_UPDATE_CHECK_DISABLED: '1' }
  });
  if (result.error || result.status !== 0) {
    throw new Error(result.error?.message || result.stderr || result.stdout || 'Command failed');
  }
  return result.stdout;
}
if (run('git', ['rev-parse', 'HEAD'], toolRoot).trim() !== lock.revision) {
  throw new Error('Archify revision differs from docs/archify/archify.lock.json');
}
if (run('git', ['status', '--porcelain', '--', 'archify'], toolRoot).trim()) {
  throw new Error('Archify package has local changes; use a clean pinned checkout');
}
const pkg = JSON.parse(readFileSync(resolve(toolRoot, 'archify/package.json'), 'utf8'));
if (pkg.version !== lock.packageVersion) throw new Error('Unexpected Archify package version');
const cli = resolve(toolRoot, 'archify/bin/archify.mjs');
const diagram = process.argv[3] || 'crc';
if (!['crc', 'http-log', 'opentelemetry'].includes(diagram)) throw new Error('Unknown diagram');
const source = `docs/archify/${diagram}.architecture.json`;
const output = `docs/archify/${diagram}.architecture.html`;
const validation = JSON.parse(run(process.execPath,
  [cli, 'validate', 'architecture', source, '--quality', 'showcase', '--json']));
if (!validation.ok || validation.checks.length !== 9 ||
    validation.composition.summary.errors || validation.composition.summary.warnings) {
  throw new Error('Expected 9 showcase checks, zero errors and warnings');
}
const delivery = JSON.parse(run(process.execPath,
  [cli, 'deliver', 'architecture', source, output, '--quality', 'showcase', '--json']));
if (!delivery.ok) throw new Error('Delivery did not pass');
// Keep receipt paths portable and avoid publishing workstation paths.
delivery.input = source;
delivery.output = output;
delivery.archifyRevision = lock.revision;
const receipt = diagram === 'crc' ? 'delivery.json' : `${diagram}.delivery.json`;
writeFileSync(resolve(root, 'docs/archify', receipt), JSON.stringify(delivery, null, 2) + '\n');
console.log('PASS: 9/9 showcase checks; 0 errors; 0 warnings');
console.log('HTML: ' + relative(root, resolve(root, output)));
console.log('Browser inspection is separate: see docs/archify/README.md');
