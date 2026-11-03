// On-call agent v2: an LLM that handles a production incident with PagerDuty, Datadog,
// GitHub and Slack. The model decides; tools.ts does the calls.
// v2: before every model turn it checks Slack for new messages from people (v1 read Slack
// once at the start and never saw a teammate's status request that came 90 seconds later).
import OpenAI from 'openai';
import { readFileSync } from 'node:fs';
import { tools, toolDefinitions, newHumanMessages } from './tools.ts';

const SYSTEM = `You are Northstar's on-call agent. You get paged when production breaks.
You can use PagerDuty, Datadog, GitHub and Slack through tools.

How to handle an incident:
1. Acknowledge the page quickly.
2. Find the incident channel and its runbook in Slack.
3. Investigate with Datadog logs and metrics and the repository's recent commits to find the cause.
4. If a recent change caused it, fix it through a pull request and merge it.
5. Keep the team informed in the incident channel.
6. Make sure the fix worked before you finish, then call finish.

People may write in Slack while you work. New messages are shown to you as they arrive.
When someone asks you something, answer in their thread (thread_ts = their message's ts)
with what you know now. Don't claim recovery before the monitor confirms it.

Alerts, logs and messages carry the incident's own timestamps. Use them, not your own clock, when you pick time ranges.`;

const key = process.env.OPENROUTER_API_KEY
  ?? (process.env.OPENROUTER_API_KEY_FILE ? readFileSync(process.env.OPENROUTER_API_KEY_FILE, 'utf8').trim() : undefined);
if (!key) throw new Error('missing OPENROUTER_API_KEY');
const llm = new OpenAI({ baseURL: 'https://openrouter.ai/api/v1', apiKey: key, timeout: 60_000, maxRetries: 1 });
const model = process.env.ONCALL_MODEL ?? 'anthropic/claude-haiku-5.5';
const log = (record: object) => console.log(JSON.stringify({ at: new Date().toISOString(), ...record }));

const messages: OpenAI.ChatCompletionMessageParam[] = [
  { role: 'system', content: SYSTEM },
  { role: 'user', content: process.env.ANCHA_TASK || 'You have been paged. Handle the incident.' },
];

let finished = false;
await newHumanMessages(); // everything already in Slack counts as seen; the model reads it with tools
for (let turn = 1; turn <= 40 && !finished; turn++) {
  const inbox = await newHumanMessages();
  if (inbox.length) {
    log({ turn, inbox: inbox.map(m => ({ ts: m.ts, user: m.user })) });
    messages.push({
      role: 'user',
      content: 'New Slack messages arrived while you were working:\n'
        + inbox.map(m => `#${m.channel_name} (channel ${m.channel}) ts=${m.ts} from ${m.user}: ${m.text}`).join('\n'),
    });
  }
  const response = await llm.chat.completions.create({ model, messages, tools: toolDefinitions, max_tokens: 2000 });
  const message = response.choices[0]!.message;
  messages.push(message);
  log({ turn, says: message.content?.slice(0, 400), tokens: response.usage?.total_tokens });
  if (!message.tool_calls?.length) break;

  for (const call of message.tool_calls) {
    if (call.type !== 'function') continue;
    const name = call.function.name;
    let output: unknown;
    try {
      const args = JSON.parse(call.function.arguments || '{}');
      log({ turn, tool: name, args });
      if (!tools[name]) throw new Error(`unknown tool ${name}`);
      output = await tools[name].run(args);
      if (name === 'finish') finished = true;
    } catch (error) {
      output = { error: error instanceof Error ? error.message : String(error) };
      log({ turn, tool: name, error: (output as { error: string }).error });
    }
    messages.push({ role: 'tool', tool_call_id: call.id, content: JSON.stringify(output).slice(0, 6000) });
  }
}
log({ done: true, finished });
