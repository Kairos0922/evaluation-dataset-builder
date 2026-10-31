# Coverage Design Guidelines

Plan coverage before generating cases. Select relevant axes:
- objectives and capabilities;
- workflow/scenario families;
- input variation and ambiguity;
- normal, boundary, exception, adversarial conditions;
- risk/impact and failure modes;
- task complexity and step count;
- tools, permissions, and environment state;
- source type and confidence.

Prioritize business importance, risk, credible frequency, known failures, capability uncertainty, diagnostic value, feasibility, and cost. Define the coverage universe and report numerator/denominator. Do not inflate coverage with redundant cases or blindly generate Cartesian products.

Create separate datasets when purpose, audience, grader, risk posture, execution setup, or release use differs materially. Shared source scenarios are acceptable if objectives differ and overlap is disclosed.
