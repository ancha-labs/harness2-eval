// Experiment bridge: expose the demo's native-SDK tools over MCP stdio.
// Only the supplied loopback twins are allowed. This is not a shipped Ancha MCP twin.
import readline from 'node:readline';
import { tools, toolDefinitions } from '../scenario/tools.ts';
for (const key of ['SLACK_API_URL', 'GITHUB_API_URL', 'DATADOG_API_URL', 'PAGERDUTY_API_URL']) {
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(new URL(process.env[key]!).hostname)) {
    throw new Error(`Expected a loopback twin for ${key}`);
  }
}
const definitions = toolDefinitions.map(t => ({ name: t.function.name, description: t.function.description, inputSchema: t.function.parameters }));
for await (const line of readline.createInterface({ input: process.stdin })) {
  let req: any;
  try {
    req = JSON.parse(line);
    if (req.id === undefined) continue;
    let result: unknown;
    if (req.method === 'initialize') result = { protocolVersion: '2024-11-05', capabilities: { tools: {} }, serverInfo: { name: 'oncall-native-twins', version: '0.1.0' } };
    else if (req.method === 'ping') result = {};
    else if (req.method === 'tools/list') result = { tools: definitions };
    else if (req.method === 'tools/call') {
      const tool = tools[req.params.name];
      if (!tool) throw new Error('Unknown tool');
      const value = await tool.run(req.params.arguments ?? {});
      result = { content: [{ type: 'text', text: JSON.stringify(value) }], isError: false };
    } else throw new Error('Unknown method');
    process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id: req.id, result }) + '\n');
  } catch (error) {
    process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id: req?.id ?? null, result: { content: [{ type: 'text', text: error instanceof Error ? error.message : String(error) }], isError: true } }) + '\n');
  }
}
