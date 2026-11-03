import { runOracle, nativeTransport } from '../_shared/agent.ts';
await runOracle('db-disk-full', nativeTransport());
