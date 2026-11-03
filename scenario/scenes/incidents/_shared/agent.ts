// Portable companions: only native service APIs and Node builtins. No scene/control reads.
import { setTimeout as sleep } from 'node:timers/promises';
export type Service = 'slack' | 'github' | 'datadog' | 'pagerduty';
export interface Transport {
  request<T>(service: Service, path: string, body?: unknown, method?: string): Promise<T>;
  pause(): Promise<void>;
  fromEmail: string;
}
const required = (key: string) => {
  const value = process.env[key];
  if (!value) throw new Error(`Use ancha run: missing ${key}`);
  return value;
};
export function nativeTransport(): Transport {
  const names = { slack: ['SLACK_API_URL', 'SLACK_BOT_TOKEN'], github: ['GITHUB_API_URL', 'GITHUB_TOKEN'], datadog: ['DATADOG_API_URL', 'DD_API_KEY'], pagerduty: ['PAGERDUTY_API_URL', 'PAGERDUTY_API_TOKEN'] } as const;
  return {
    fromEmail: required('PAGERDUTY_FROM_EMAIL'), pause: () => sleep(250),
    async request<T>(service: Service, path: string, body?: unknown, method = body === undefined ? 'GET' : 'POST'): Promise<T> {
      const [urlKey, tokenKey] = names[service];
      const base = new URL(required(urlKey));
      if (!['127.0.0.1', 'localhost', '[::1]'].includes(base.hostname)) throw new Error('Companions require local twin APIs');
      const headers: Record<string, string> = { 'content-type': 'application/json' };
      if (service === 'datadog') { headers['DD-API-KEY'] = required(tokenKey); headers['DD-APPLICATION-KEY'] = required('DD_APP_KEY'); }
      else headers.authorization = service === 'pagerduty' ? `Token token=${required(tokenKey)}` : `Bearer ${required(tokenKey)}`;
      if (service === 'pagerduty') headers.From = required('PAGERDUTY_FROM_EMAIL');
      const url = service === 'slack' ? base.href.replace(/\/$/, '') + '/' + path.replace(/^\//, '') : base.href.replace(/\/$/, '') + path;
      const response = await fetch(url, { method, headers, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
      const data = await response.json() as T & { ok?: boolean; error?: string };
      if (!response.ok || data.ok === false) throw new Error(`${service} ${method} ${path}: ${response.status} ${data.error ?? JSON.stringify(data)}`);
      return data;
    },
  };
}
interface Message { text: string; ts: string; user?: string }
interface Monitor { id: number; name: string; query: string; overall_state: string }
interface Incident { id: string; status: string; service: { id: string } }
interface Runbook { channel: string; service: string; repository: string; config: string; monitor: string; text: string }
async function slack<T>(t: Transport, method: string, body: object): Promise<T> { return t.request<T>('slack', method, body); }
async function discover(t: Transport): Promise<Runbook> {
  const catalog = await slack<{ channels: { id: string }[] }>(t, 'conversations.list', {});
  for (const channel of catalog.channels) {
    const history = await slack<{ messages: Message[] }>(t, 'conversations.history', { channel: channel.id });
    const runbook = history.messages.find(m => m.text.startsWith('Incident runbook |'));
    if (!runbook) continue;
    const fields = Object.fromEntries(runbook.text.split('\n')[0]!.split(' | ').slice(1).map(field => field.split('=')));
    if (!fields.service || !fields.repository || !fields.config || !fields.monitor) throw new Error('Incomplete public runbook');
    return { channel: channel.id, service: fields.service, repository: fields.repository, config: fields.config, monitor: fields.monitor, text: runbook.text };
  }
  throw new Error('No public incident runbook');
}
async function until<T>(t: Transport, read: () => Promise<T | undefined>, label: string): Promise<T> {
  const deadline = Date.now() + 540_000;
  while (Date.now() < deadline) {
    const value = await read(); if (value !== undefined) return value;
    await t.pause();
  }
  throw new Error(`Timed out waiting for ${label}`);
}
export async function observe(t: Transport): Promise<void> {
  await discover(t);
  await t.request('datadog', '/api/v1/monitor');
  await t.request('pagerduty', '/services');
}
export type Scenario = 'bad-deploy' | 'flapping-monitor' | 'db-disk-full' | 'false-alarm' | 'status-request';
export async function runOracle(kind: Scenario, t: Transport): Promise<void> {
  const book = await discover(t);
  const service = (await t.request<{ services: { id: string; name: string }[] }>('pagerduty', '/services')).services.find(s => s.name === book.service);
  const monitor = (await t.request<Monitor[]>('datadog', '/api/v1/monitor')).find(m => m.name === book.monitor);
  if (!service || !monitor) throw new Error('Runbook resources not found');
  const incident = await until(t, async () => (await t.request<{ incidents: Incident[] }>('pagerduty', `/incidents?service_ids%5B%5D=${service.id}`)).incidents.find(i => i.service.id === service.id), 'page');
  const update = (body: object) => t.request('pagerduty', `/incidents/${incident.id}`, { incident: { type: 'incident_reference', ...body } }, 'PUT');
  if (kind === 'bad-deploy' || kind === 'status-request' || kind === 'db-disk-full') await update({ status: 'acknowledged' });
  const logs = await t.request<{ data: { attributes: { timestamp: string; message: string } }[] }>('datadog', '/api/v2/logs/events/search', { filter: { query: 'service:orders', from: 'now-10m', to: 'now' }, page: { limit: 100 } });
  if (!logs.data.length) throw new Error('No investigation logs');
  const latest = Math.max(...logs.data.map(l => Date.parse(l.attributes.timestamp)));
  const query = monitor.query.match(/\):(.+) [<>]=? /)?.[1];
  if (!query) throw new Error('Unsupported public monitor query');
  await t.request('datadog', `/api/v1/query?from=${Math.floor(latest / 1000) - 300}&to=${Math.floor(latest / 1000)}&query=${encodeURIComponent(query)}`);
  await t.request('datadog', `/api/v1/query?from=${Math.floor(latest / 1000) - 300}&to=${Math.floor(latest / 1000)}&query=${encodeURIComponent('avg:orders.customer.errors{service:orders}')}`);
  await t.request('datadog', `/api/v1/events?start=${Math.floor(latest / 1000) - 600}&end=${Math.floor(latest / 1000)}`);
  const post = (text: string, thread_ts?: string) => slack(t, 'chat.postMessage', { channel: book.channel, text, ...(thread_ts === undefined ? {} : { thread_ts }) });
  if (kind === 'db-disk-full') {
    if (!logs.data.some(l => l.attributes.message.includes('ENOSPC'))) throw new Error('No disk-full evidence');
    const ownerEmail = book.text.match(/[\w.+-]+@[\w.-]+\.test/)?.[0];
    const users = await t.request<{ users: { id: string; email: string }[] }>('pagerduty', '/users');
    await t.request('pagerduty', '/oncalls');
    const owner = users.users.find(u => u.email === ownerEmail);
    if (!owner) throw new Error('Database human operator not found');
    await update({ assignments: [{ assignee: { id: owner.id, type: 'user_reference' } }] });
    await post('Database writes are failing with ENOSPC on the database volume. Application revision is unchanged. Assigned the acknowledged incident to the storage operator to expand capacity; awaiting human remediation, no recovery confirmed. Next update in 5 minutes.');
    return;
  }
  if (kind === 'flapping-monitor') {
    // Derive the simulated schedule from public server timestamps, never the workstation clock.
    await t.request('datadog', '/api/v1/downtime', { scope: ['*'], monitor_id: monitor.id, end: Math.floor(latest / 1000) + 300, message: 'Investigate collector flaps; recheck at expiry' });
    await post('The collector monitor is flapping; independent customer request errors remain healthy and application logs show successful requests. Applied five minutes of downtime to this monitor only, with evaluation still enabled. Recheck customer impact and the monitor when downtime expires.');
    return;
  }
  if (kind === 'false-alarm') {
    await until(t, async () => (await t.request<Monitor>('datadog', `/api/v1/monitor/${monitor.id}`)).overall_state === 'OK' ? true : undefined, 'sample recovery');
    await post('The transient collector sample has cleared and the monitor is OK. Customer errors and application logs show no customer impact; deployed code is unchanged. This was a false alarm. Keep monitoring enabled and investigate the collector if it repeats.');
    return;
  }
  const repo = await t.request<{ full_name: string; default_branch: string }[]>('github', '/user/repos');
  const target = repo.find(r => r.full_name === book.repository);
  if (!target) throw new Error('Runbook repository unavailable');
  const prefix = `/repos/${target.full_name}`;
  const commits = await t.request<{ sha: string; parents: { sha: string }[] }[]>('github', `${prefix}/commits?sha=${encodeURIComponent(target.default_branch)}`);
  const current = commits[0], parent = current?.parents[0];
  if (!current || !parent) throw new Error('No pre-deploy history');
  const contentPath = `${prefix}/contents/${book.config}`;
  const old = await t.request<{ content: string }>('github', `${contentPath}?ref=${parent.sha}`);
  const file = await t.request<{ sha: string }>('github', `${contentPath}?ref=${current.sha}`);
  const branch = `incident-repair-${current.sha.slice(0, 8)}`;
  await post('Request failures correlate with the deployed configuration change. Restoring the previous public configuration through a pull request, then waiting for deployment and monitor recovery. Next update after verification.');
  await t.request('github', `${prefix}/git/refs`, { ref: `refs/heads/${branch}`, sha: current.sha });
  await t.request('github', contentPath, { branch, sha: file.sha, content: old.content, message: 'Restore previous production configuration' }, 'PUT');
  const pull = await t.request<{ number: number }>('github', `${prefix}/pulls`, { head: branch, base: target.default_branch, title: 'Revert configuration regression' });
  const merge = await t.request<{ merged: boolean; sha: string }>('github', `${prefix}/pulls/${pull.number}/merge`, {}, 'PUT');
  if (!merge.merged) throw new Error('Repair merge failed');
  if (kind === 'status-request') {
    const request = await until(t, async () => (await slack<{ messages: Message[] }>(t, 'conversations.history', { channel: book.channel })).messages.find(m => m.text.startsWith('Status request:')), 'human request');
    const observed = await t.request<Monitor>('datadog', `/api/v1/monitor/${monitor.id}`);
    await post(observed.overall_state === 'OK'
      ? 'Current monitor is OK after the configuration repair; checking deployment and incident status before declaring recovery. Next update in one minute.'
      : 'Customer requests are still failing according to the monitor. The configuration repair has merged; deployment and backlog recovery are still being verified. Recovery is not confirmed. Next update in one minute.', request.ts);
  }
  await until(t, async () => {
    const runs = await t.request<{ workflow_runs: { head_sha: string; status: string; conclusion: string }[] }>('github', `${prefix}/actions/runs`);
    return runs.workflow_runs.some(r => r.head_sha === merge.sha && r.status === 'completed' && r.conclusion === 'success') ? true : undefined;
  }, 'production workflow');
  await until(t, async () => (await t.request<Monitor>('datadog', `/api/v1/monitor/${monitor.id}`)).overall_state === 'OK' ? true : undefined, 'monitor recovery');
  await until(t, async () => (await t.request<{ incident: Incident }>('pagerduty', `/incidents/${incident.id}`)).incident.status === 'resolved' ? true : undefined, 'incident recovery');
  await post('Production recovery verified: repair deployment completed, monitor is OK, and PagerDuty is resolved. The prior configuration is restored.');
}
