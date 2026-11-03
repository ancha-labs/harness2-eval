import { runOracle, nativeTransport } from '../_shared/agent.ts';
await runOracle('status-request', nativeTransport());
