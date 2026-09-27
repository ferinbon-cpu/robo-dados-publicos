# TASK 217C — discovery-only runtime carrier

TASK 217C materializes the runtime carrier needed to turn TASK 217B from a T0 design into an explicitly authorizable operation.

The carrier is deliberately narrower than the eventual redigest. After authorization it may only discover official Jornal Oficial edition metadata for January through 8 September 2026. It downloads no Jornal PDF and performs no Drive, serving, publication or answerability mutation.

The workflow is inert on main. It triggers only on branch `task-217c-jom-2026-discovery-runtime` when `runtime_triggers/task217c_jom_2026_discovery.run` changes. The runtime branch must descend from the exact implementation SHA named by the owner authorization, and the only files allowed to differ from that SHA are the owner authorization JSON and the trigger file.

Any partial month, pagination problem, source exception or budget breach stops the run. The result is a one-day sanitized workflow artifact containing edition/date/document-URL identities only. A successful discovery does not itself download, redigest, assign schools or promote INFRA_Q2.
