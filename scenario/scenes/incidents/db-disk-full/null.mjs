// scenes/incidents/_shared/agent.ts
import { setTimeout as sleep } from "node:timers/promises";
var required = (key) => {
  const value = process.env[key];
  if (!value) throw new Error(`Use ancha run: missing ${key}`);
  return value;
};
function nativeTransport() {
  const names = { slack: ["SLACK_API_URL", "SLACK_BOT_TOKEN"], github: ["GITHUB_API_URL", "GITHUB_TOKEN"], datadog: ["DATADOG_API_URL", "DD_API_KEY"], pagerduty: ["PAGERDUTY_API_URL", "PAGERDUTY_API_TOKEN"] };
  return {
    fromEmail: required("PAGERDUTY_FROM_EMAIL"),
    pause: () => sleep(250),
    async request(service, path, body, method = body === void 0 ? "GET" : "POST") {
      const [urlKey, tokenKey] = names[service];
      const base = new URL(required(urlKey));
      if (!["127.0.0.1", "localhost", "[::1]"].includes(base.hostname)) throw new Error("Companions require local twin APIs");
      const headers = { "content-type": "application/json" };
      if (service === "datadog") {
        headers["DD-API-KEY"] = required(tokenKey);
        headers["DD-APPLICATION-KEY"] = required("DD_APP_KEY");
      } else headers.authorization = service === "pagerduty" ? `Token token=${required(tokenKey)}` : `Bearer ${required(tokenKey)}`;
      if (service === "pagerduty") headers.From = required("PAGERDUTY_FROM_EMAIL");
      const url = service === "slack" ? base.href.replace(/\/$/, "") + "/" + path.replace(/^\//, "") : base.href.replace(/\/$/, "") + path;
      const response = await fetch(url, { method, headers, ...body === void 0 ? {} : { body: JSON.stringify(body) } });
      const data = await response.json();
      if (!response.ok || data.ok === false) throw new Error(`${service} ${method} ${path}: ${response.status} ${data.error ?? JSON.stringify(data)}`);
      return data;
    }
  };
}
async function slack(t, method, body) {
  return t.request("slack", method, body);
}
async function discover(t) {
  const catalog = await slack(t, "conversations.list", {});
  for (const channel of catalog.channels) {
    const history = await slack(t, "conversations.history", { channel: channel.id });
    const runbook = history.messages.find((m) => m.text.startsWith("Incident runbook |"));
    if (!runbook) continue;
    const fields = Object.fromEntries(runbook.text.split("\n")[0].split(" | ").slice(1).map((field) => field.split("=")));
    if (!fields.service || !fields.repository || !fields.config || !fields.monitor) throw new Error("Incomplete public runbook");
    return { channel: channel.id, service: fields.service, repository: fields.repository, config: fields.config, monitor: fields.monitor, text: runbook.text };
  }
  throw new Error("No public incident runbook");
}
async function observe(t) {
  await discover(t);
  await t.request("datadog", "/api/v1/monitor");
  await t.request("pagerduty", "/services");
}

// scenes/incidents/db-disk-full/null.ts
await observe(nativeTransport());
