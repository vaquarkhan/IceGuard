# Research background

Spark-on-AWS-Lambda saves cost but introduces a **commit-durability gap**: data files may land on S3 without metadata commit when Lambda receives `SIGKILL`.

**Paper:** [*Characterizing and Fixing Silent Data Loss in Spark-on-AWS-Lambda with Open Table Formats*](https://arxiv.org/abs/2604.20081) (arXiv:2604.20081).

IceGuard addresses the gap with:

- Proactive rollback before hard kill (watchdog)
- Resumable checkpoints (idempotent retries)
- Orphan detection (storage hygiene)
- Visible errors (`IceGuardRollbackError`) instead of silent success

See [architecture.md](architecture.md) for how components map to these goals.
