# Security notes

- Never commit `backend/.env` or `frontend/.env`.
- Keep `.env.example` limited to placeholders and non-secret defaults.
- Rotate any credential that has previously appeared in an example file.
- Production startup rejects default or short Flask/JWT secrets.
- Audio, report, transcript and meeting resources require both authentication
  and ownership checks.
- Do not expose the backend container directly in production; use Nginx.
- Run `npm audit` and `python -m pip_audit -r requirements.txt` in CI.
- Add rate limiting at the reverse proxy or application layer before public use.

Report suspected vulnerabilities privately to the project maintainers. Do not
include credentials, meeting audio or transcripts in public issues.
