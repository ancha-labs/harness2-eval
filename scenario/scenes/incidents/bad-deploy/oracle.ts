import { runOracle, nativeTransport } from '../_shared/agent.ts';
await runOracle('bad-deploy', nativeTransport());
