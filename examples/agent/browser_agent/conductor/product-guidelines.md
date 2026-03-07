# Product Guidelines - Browser Agent Example

## Prose Style
- **Technical & Concise:** Documentation and internal comments should be precise, clear, and focused on providing necessary technical details without unnecessary filler. Prioritize accuracy and readability for developers and researchers.

## Branding & Voice
- **Innovative & Exploratory:** The project's voice should reflect a forward-thinking approach to AI and browser automation. Encourage experimentation and the adoption of modern techniques (like MCP and multimodal reward models).

## UX Principles
- **Transparency & Visibility:** Provide clear, granular feedback during browser automation. Ensure that the agent's actions, the state of the browser, and any captured data (logs, videos) are easily accessible and interpretable.
- **Safety & Predictability:** Design agent interactions to be predictable and safe. Implement safeguards to prevent unintended actions on web pages and ensure that exploration remains within defined boundaries.

## Coding Standards
- **Strongly Typed & Explicit:** Utilize Python's type hinting and explicit interface definitions for all modules. This ensures clarity, reduces bugs, and improves the developer experience.
- **Well-Documented Internal Logic:** Complex logic, especially around MCP interactions and data capture, must be thoroughly documented with inline comments and high-level summaries.
- **Extensible Architecture:** Maintain a modular design that allows for the easy addition of new browser tools, evaluation tasks, and data processing pipelines.
