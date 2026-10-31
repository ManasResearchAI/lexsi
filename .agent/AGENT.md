The idea is to check how easy would it be poison a given models and what safeguards can we prevent to solve  this challenge?
        - The activation intervention test could break these models and make them produce hate speech / racist comments etc. #MODEL Drifting
        - Then we jump in with SafeTune or something to repair it and strengthen the safeguards.
            - Ways to strengthen the safeguards:
                1. Joint Weight Perurbation
                2. Abliteration-Resistant Tuning (ART)
                3. Drift-Constrained Optimization: Optimization with these these methods or a combination of these which raise the cost beyond what the RESTA or the LOX methods in the library can produce.
        - Tiny Aya -> CuratorKit -> CircuitKit -> SafeTune -> AuditKit

## Instructions:

- For each tool that we want to use and chain together, we have the submodules setup and an agent summary in `<repo>/.agent/README.md`.
- The model that we will be using has to be : `CohereLabs/tiny-aya-global` not Qwen or any other model.
- First prepare a plan according on how we will chain these tools together and more importantly - get back with an analysis on whether it is possible to get EXACTLY the methods that we have mentioned (Joint Weight Pertubation etc.) - Also explain those methods to me in the plan so that I know we are making the right change.
- Write the plan to /home/asavari/lexsi/.agent/art-plan.md