## Just an outline of what each tool does and brainstorming all the possible ways in which we can use them to chain up an idea or attack..

https://github.com/Lexsi-Labs/aligntune - Aligntune :  Aligns/Post-trains an LLM for a given task, with all the methods exposed behind one library/API.

https://github.com/Lexsi-Labs/CuratorKIT - CuratorKit: Dataset Curation Tool

https://github.com/Lexsi-Labs/AuditKIT - AuditKit: Evaluation suite with a collection of benchmarks, metrics and diagnosis

https://github.com/Lexsi-Labs/SafeTune - Safetune: Auditing and repairing safety drift in Fine-Tuned LLMs

https://github.com/Lexsi-Labs/CircuitKIT - CircuitKit: A mech interp framework for discovering, evaluating and intervening on circuits inside transformer models.

https://github.com/Lexsi-Labs/AgentTune - AgentTune: This is what the Gemma task was about, training agents specifically for better and accurate tool calls etc.



These are the above tools that we have to use as part of an AI safety Hackathon. You build Nov 1 to 14 (online), submit by end of day Nov 14, and Demo Day is Nov 22. Registration closes Nov 5 and kickoff is Oct 31.

You have to chain at least 2 of the track’s repos into one pipeline, and 3 or more is preferred. The track repos are CuratorKIT (data curation), SafeTune (safety repair), CircuitKIT (interpretability) and AuditKIT (evaluation).
You have to use Cohere’s open-weights models: Tiny Aya (Global, Fire, Water, Earth) or Aya Expanse 8B/32B.
Judges expect before/after numbers on more than one metric, a Hugging Face write-up explaining your choices, and every artifact hosted on HF. A cost comparison against a closed model is optional but earns credit.
They haven’t published sample problem statements yet.

So this isn’t a pure jailbreak contest. What they want is “find a safety problem, fix it, prove the fix with numbers.” The natural pipeline is AuditKIT to measure → CuratorKIT to build data → SafeTune to repair → AuditKIT to measure again, with CircuitKIT as a bonus, but we can change that.



## TODONOW

[ ] Currently I am deciding the format in which the description of each repo should be written down in their respective local clones (<repo>/.agent/README.md) - which an agent will refer to to decide which problems are the most tractable and worth solving in the given period of time.
