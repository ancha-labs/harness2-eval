import { runOracle, nativeTransport } from '../_shared/agent.ts';
await runOracle('flapping-monitor', nativeTransport());
