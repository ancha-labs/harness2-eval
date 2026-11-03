// The on-call agent's hands: PagerDuty, Datadog, GitHub and Slack through their official SDKs.
// In production the URLs and tokens below point at the real services. Under Ancha, each test
// trial puts the URL and a fake token of its own twin in the same variables, so this file
// does not change between production and testing.
import { WebClient } from '@slack/web-api';
import { Octokit } from '@octokit/rest';
import { client, v1, v2 } from '@datadog/datadog-api-client';
import { api } from '@pagerduty/pdjs';
import { setTimeout as sleep } from 'node:timers/promises';

const env = process.env;
const need = (name: string) => {
  const value = env[name];
  if (!value) throw new Error(`missing ${name}`);
  return value;
};

const slack = new WebClient(need('SLACK_BOT_TOKEN'), { slackApiUrl: need('SLACK_API_URL') });
const github = new Octokit({ auth: need('GITHUB_TOKEN'), baseUrl: need('GITHUB_API_URL') });
const dd = client.createConfiguration({
  baseServer: new client.BaseServerConfiguration(need('DATADOG_API_URL'), {}),
  authMethods: { apiKeyAuth: need('DD_API_KEY'), appKeyAuth: need('DD_APP_KEY') },
});
const monitors = new v1.MonitorsApi(dd);
const metrics = new v1.MetricsApi(dd);
const logs = new v2.LogsApi(dd);
const pdBase = need('PAGERDUTY_API_URL').replace(/\/$/, '');
const pd = api({ token: need('PAGERDUTY_API_TOKEN'), headers: { From: need('PAGERDUTY_FROM_EMAIL') } });

async function pagerduty(path: string, method = 'GET', data?: object) {
  const r = await pd({ endpoint: path, url: pdBase + path, method, ...(data ? { data } : {}) });
  if (!r.ok) throw new Error(`PagerDuty ${method} ${path}: HTTP ${r.status}`);
  return r.data;
}

function splitRepo(full: string) {
  const [owner, repo] = full.split('/');
  if (!owner || !repo) throw new Error('repo must look like owner/name');
  return { owner, repo };
}

type Args = Record<string, any>;
type Tool = { description: string; params: Record<string, string>; optional?: string[]; run: (a: Args) => Promise<unknown> };

export const tools: Record<string, Tool> = {
  slack_list_channels: {
    description: 'List the Slack channels the bot can see.',
    params: {},
    run: async () => (await slack.conversations.list({})).channels?.map(c => ({ id: c.id, name: c.name })),
  },
  slack_read_channel: {
    description: 'Read recent messages of a Slack channel, newest first. Each message has ts, user and text.',
    params: { channel: 'string' },
    run: async a => (await slack.conversations.history({ channel: a.channel, limit: 30 })).messages?.map(m => ({
      ts: m.ts, user: m.user ?? m.bot_id, text: m.text, thread_ts: m.thread_ts, reply_count: m.reply_count,
    })),
  },
  slack_post: {
    description: 'Post a message to a Slack channel. Pass thread_ts to reply inside the thread of that message.',
    params: { channel: 'string', text: 'string', thread_ts: 'string' },
    optional: ['thread_ts'],
    run: async a => {
      const r = await slack.chat.postMessage({ channel: a.channel, text: a.text, ...(a.thread_ts ? { thread_ts: a.thread_ts } : {}) });
      return { ok: r.ok, ts: r.ts };
    },
  },
  pagerduty_list_incidents: {
    description: 'List PagerDuty incidents with their status and service.',
    params: {},
    run: async () => ((await pagerduty('/incidents')) as any).incidents.map((i: any) => ({
      id: i.id, title: i.title, status: i.status, service: i.service?.summary, created_at: i.created_at,
    })),
  },
  pagerduty_update_incident: {
    description: 'Set a PagerDuty incident status to "acknowledged" or "resolved".',
    params: { incident_id: 'string', status: 'string' },
    run: async a => {
      const r = (await pagerduty(`/incidents/${a.incident_id}`, 'PUT', { incident: { type: 'incident_reference', status: a.status } })) as any;
      return { id: r.incident.id, status: r.incident.status };
    },
  },
  datadog_list_monitors: {
    description: 'List Datadog monitors with their query and current state (OK, Warn, Alert...).',
    params: {},
    run: async () => (await monitors.listMonitors()).map(m => ({ id: m.id, name: m.name, query: m.query, state: m.overallState })),
  },
  datadog_search_logs: {
    description: 'Search Datadog logs from the last N minutes, newest first. Query uses Datadog syntax, e.g. "service:orders status:error".',
    params: { query: 'string', minutes: 'number' },
    run: async a => (await logs.listLogs({ body: { filter: { query: a.query, from: `now-${a.minutes}m`, to: 'now' }, page: { limit: 30 } } })).data
      ?.map(l => ({ time: l.attributes?.timestamp, status: l.attributes?.status, message: l.attributes?.message })),
  },
  datadog_query_metric: {
    description: 'Query a Datadog metric between two ISO times, e.g. "avg:orders.errors{service:orders}". Returns [time, value] points.',
    params: { query: 'string', from: 'string', to: 'string' },
    run: async a => {
      const r = await metrics.queryMetrics({ query: a.query, from: Date.parse(a.from) / 1000, to: Date.parse(a.to) / 1000 });
      return (r.series ?? []).map(s => ({ metric: s.metric, points: s.pointlist?.slice(-20).map(p => [new Date(p[0]!).toISOString(), p[1]]) }));
    },
  },
  github_list_commits: {
    description: 'List recent commits on the default branch of a repository ("owner/name"), newest first.',
    params: { repo: 'string' },
    run: async a => (await github.repos.listCommits({ ...splitRepo(a.repo), per_page: 10 })).data.map(c => ({
      sha: c.sha, message: c.commit.message, author: c.commit.author?.name, date: c.commit.author?.date,
    })),
  },
  github_get_file: {
    description: 'Read a file of a repository at a branch or commit sha.',
    params: { repo: 'string', path: 'string', ref: 'string' },
    run: async a => {
      const r = (await github.repos.getContent({ ...splitRepo(a.repo), path: a.path, ref: a.ref })).data as any;
      return { path: r.path, sha: r.sha, content: Buffer.from(r.content, 'base64').toString('utf8') };
    },
  },
  github_open_fix_pr: {
    description: 'Open a pull request that replaces one file on the default branch with new content. Returns the PR number.',
    params: { repo: 'string', path: 'string', new_content: 'string', title: 'string' },
    run: async a => {
      const r = splitRepo(a.repo);
      const repo = (await github.repos.get(r)).data;
      const head = (await github.repos.listCommits({ ...r, sha: repo.default_branch, per_page: 1 })).data[0]!;
      const branch = `oncall-fix-${head.sha.slice(0, 7)}`;
      await github.git.createRef({ ...r, ref: `refs/heads/${branch}`, sha: head.sha });
      const file = (await github.repos.getContent({ ...r, path: a.path, ref: branch })).data as any;
      await github.repos.createOrUpdateFileContents({
        ...r, path: a.path, branch, sha: file.sha, message: a.title, content: Buffer.from(a.new_content).toString('base64'),
      });
      const pr = (await github.pulls.create({ ...r, head: branch, base: repo.default_branch, title: a.title })).data;
      return { number: pr.number, branch };
    },
  },
  github_merge_pr: {
    description: 'Merge a pull request. Merging to the default branch starts the deploy pipeline.',
    params: { repo: 'string', number: 'number' },
    run: async a => {
      const r = (await github.pulls.merge({ ...splitRepo(a.repo), pull_number: a.number })).data;
      return { merged: r.merged, sha: r.sha };
    },
  },
  github_list_deploys: {
    description: 'List recent deploy pipeline runs (GitHub Actions) of a repository with their status.',
    params: { repo: 'string' },
    run: async a => (await github.actions.listWorkflowRunsForRepo({ ...splitRepo(a.repo), per_page: 5 })).data.workflow_runs.map(w => ({
      name: w.name, head_sha: w.head_sha, status: w.status, conclusion: w.conclusion,
    })),
  },
  wait: {
    description: 'Wait some seconds (at most 60) before checking again, e.g. for a deploy or a monitor to recover.',
    params: { seconds: 'number' },
    run: async a => {
      await sleep(Math.min(Math.max(a.seconds, 1), 60) * 1000);
      return { waited: Math.min(Math.max(a.seconds, 1), 60) };
    },
  },
  finish: {
    description: 'Call when the incident is handled. Give a one-paragraph summary.',
    params: { summary: 'string' },
    run: async a => ({ finished: true, summary: a.summary }),
  },
};

// The tool list in the format the model API expects.
export const toolDefinitions = Object.entries(tools).map(([name, t]) => ({
  type: 'function' as const,
  function: {
    name,
    description: t.description,
    parameters: {
      type: 'object',
      properties: Object.fromEntries(Object.entries(t.params).map(([k, type]) => [k, { type }])),
      required: Object.keys(t.params).filter(k => !t.optional?.includes(k)),
    },
  },
}));
