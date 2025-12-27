# Day 4 Evaluation - Tool interation (web search, docs, videos)

This document records test scenarios demonstrating:
- tool use
- tool failure handling
- evidence sources citations

## Scenario 
**User query**

**Plan output** (only the research step + tool_calls is enough)

**Tool execution summary** (success count, fallback used or not)

**Final answer** (shorten)

**Sources** (the URLs produced by `AgentAnswer.sources`)

**Notes** (what worked/what to improve)

## Scenario 1
**User query**
- "Give beginner resources to learn reinforcement learning, including videos."
- Additional clarification: "I am looking for reinforcement learning fundamentals, not specifically relevant to LLM/GenAI. Focus more on theoretical rather than actual examples, with certain level of math is OK."

**Plan output** (only the research step + tool_calls is enough)
- The plan includes one research step with following key attributes:
  -  "description": "Find beginner-friendly video tutorials and concise written resources that explain reinforcement learning theory with some math, suitable for non-CS backgrounds."
  -  "query": "reinforcement learning beginner tutorial theoretical math"
  -  "tool_calls": {"tool": "video_search", "query": "reinforcement learning beginner theoretical math tutorial"}

**Tool execution summary** (success count, fallback used or not)
- The video_search tool call was succesful at 1st attempt.

**Final answer** (shorten)\
EXPLANATION:
To help you get started with reinforcement learning (RL) fundamentals from a theoretical perspective, I have outlined the key foundational topics you should understand. These include concepts like Markov Decision Processes (MDPs), value functions, policies, and basic RL algorithms such as Q-learning. Since you are comfortable with some math but do not have a computer science background, the resources I recommend balance theory with accessible explanations.

I found three beginner-friendly video tutorials that explain RL theory with some math, suitable for non-CS backgrounds. These videos cover essential RL concepts, mathematical foundations like Bellman equations, and overview of methods without diving too deep into coding or complex implementations.

BULLETS:
- Key foundational RL topics to study:
  - Markov Decision Processes (MDPs)
  - Value Functions and Bellman Equations
  - Policy and Policy Evaluation
  - Dynamic Programming
  - Monte Carlo Methods
  - Temporal Difference Learning
  - Exploration vs Exploitation trade-off
  - Basic Algorithms: Q-learning, SARSA

  - Recommended beginner-friendly video tutorials:
    1. **Reinforcement Learning: Essential Concepts**\
       Explains core RL ideas and math foundations clearly.\
       [Watch here](https://www.youtube.com/watch?v=Z-T0iJEXiwM)

    2. **Reinforcement Learning from scratch**\
       A step-by-step introduction to RL theory with mathematical insights.\
       [Watch here](https://www.youtube.com/watch?v=vXtfdGphr3c)

    3. **Reinforcement Learning Series: Overview of Methods**\
       Covers different RL methods and their theoretical basis in an accessible way.\
       [Watch here](https://www.youtube.com/watch?v=i7q8bISGwMQ)

- Additional tips:
  - Focus on understanding MDPs and Bellman equations first, as they form the backbone of RL theory.
  - Use supplementary written resources like introductory RL chapters in books or online tutorials for deeper reading.
  - Don’t worry about coding initially; focus on grasping the math and concepts.

**Sources** (the URLs produced by `AgentAnswer.sources`)
- https://www.youtube.com/watch?v=Z-T0iJEXiwM
- https://www.youtube.com/watch?v=vXtfdGphr3c
- https://www.youtube.com/watch?v=i7q8bISGwMQ

**Notes** (what worked/what to improve)
- The planner only include one research step searching for videos, while the original user intent is to get learning materials "including videos", not just looking for videos. This may be something the planner can improve.

## Scenario 2
**User query**
- Explain Python asyncio and point to official docs.
- additional clarification: I prefer more detailed explanation including basic usage examples.

**Plan output** (only the research step + tool_calls is enough)
- The plan include one research step with the following attributes:
  - description: "Find the official Python documentation page for asyncio to provide an authoritative reference."
  - tool_calls : {"tool": "docs_search","query": "asyncio site:docs.python.org"}

**Tool execution summary** (success count, fallback used or not)
- A docs_search tool call was successful at 1st attempt

**Final answer** (shorten)
- Explanation: the answer first gives a concise introduction to what is asyncio library. What are keep concepts (Event Loop, Coroutines, Taks, async/await syntext). How it works and then include atwo basic code examples with explanation.
- Bullets highlight purpose of asyncio, event loop, conroutines, asyncio.run(), asyncio.create_tasks()

**Sources** (the URLs produced by `AgentAnswer.sources`)
- https://docs.python.org/3/library/asyncio.html

**Notes** (what worked/what to improve)
The agent gives a very good brief answer for asyncio and found the correct official python asyncio document webpage.

## Scenario 3
**User query**
- Give a study plan for Basel III + best videos
- Additional clarification: I am looking for the regulatory framework, not the technical implementation. I prefer detailed regulatory documentation and analysis. Target audient is professional with finance background.

**Plan output** (only the research step + tool_calls is enough)
- The plan includes 2 research steps
  - 1st research step is a docs_search
    - "description": "Find official Basel III regulatory documentation and authoritative analysis resources."
    - "tool_calls": {"tool": "docs_search", "query": "site:bis.org Basel III regulatory framework official documentation",}
    - "outputs": 
    ```json
    {
        "official_docs_link": "https://www.bis.org/bcbs/basel3.htm",
        "analysis_papers": [
          "Basel Committee on Banking Supervision publications",
          "IMF and World Bank Basel III analysis reports"
        ]
      }
    ```
  - 2nd research step is a video_search
    - "description": "Identify best professional-level video tutorials and lectures explaining Basel III framework."
    - "tool_calls": {"tool": "video_search", "query": "Basel III regulatory framework professional tutorial"}
    - "outputs":
    ```json
     {
        "video_resources": [
          "Basel III Explained - Official BIS Webinar",
          "Basel III Regulatory Framework Overview by Finance Experts",
          "Liquidity and Capital Requirements under Basel III - Detailed Analysis"
        ]
      }
    ```

**Tool execution summary** (success count, fallback used or not)
- docs_search tool call was successful at the 1st attempt
- video_search tool call was successul at the 1st attempt

**Final answer** (shorten)
EXPLANATION:\
Based on your request, I assume:
- You want a structured study plan focused on the Basel III regulatory framework, not on technical or IT implementation.
- Your background is in finance/business, so the content should be professional-level but not overly technical in computer science.
- You prefer official and authoritative documentation combined with high-quality video tutorials for better understanding.
- The goal is to gain a comprehensive understanding of Basel III’s key regulatory components relevant to finance professionals.

Following these assumptions, I have created a concise 2-week study plan that covers the essential Basel III topics, combining official Basel Committee on Banking Supervision (BCBS) documents and professional video resources. The plan emphasizes capital requirements, leverage ratio, liquidity standards, risk management, disclosure, and implementation timeline.

BULLETS include a 14-day study plan divided by 7 focused areas, stating from reading the foccial docs, and then watch professional videos, and then study liquidity to supervisory framework, disclosure requirements, impact on implementation and a final review. All make sense.

The answer additionally gives a very clear separate section for recommended offical docs and recommended videos.

**Sources** (the URLs produced by `AgentAnswer.sources`)
  1. Basel III: international regulatory framework for banks | https://www.bis.org/bcbs/basel3.htm
  2. Basel III: A global regulatory framework for more resilient ... | https://www.bis.org/publ/bcbs189.pdf
  3. Basel Framework | https://www.bis.org/basel_framework/
  4. Understanding Financial Regulation - The Origins of the Basel Accords | https://www.youtube.com/watch?v=HQCfnv7BUoc
  5. Basel iii, A global regulatory framework for more resilient banks and banking systems | https://www.youtube.com/watch?v=bGggmcDGLIY

**Notes** (what worked/what to improve)
- Overall the answer is solid. The agent did docs_search and video_search correctly following user's query.
- The answer provides a separate recommended docs and videos section which is very good. But it didn't provide links to each of the materials. When asnwer provide references to materials it should also provide the links inline.
- The "real" source evidences returned by the tool calls are:
```
Evidence you may use (URLs provided)
- [ToolType.docs_search] Basel III: international regulatory framework for banks | https://www.bis.org/bcbs/basel3.htm
- [ToolType.docs_search] Basel III: A global regulatory framework for more resilient ... | https://www.bis.org/publ/bcbs189.pdf
- [ToolType.docs_search] Basel Framework | https://www.bis.org/basel_framework/
- [ToolType.video_search] Understanding Financial Regulation - The Origins of the Basel Accords | https://www.youtube.com/watch?v=HQCfnv7BUoc
- [ToolType.video_search] Basel iii, A global regulatory framework for more resilient banks and banking systems | https://www.youtube.com/watch?v=bGggmcDGLIY
- [ToolType.video_search] Basel iii, Pillar 3, Revised Pillar 3 disclosure requirements | https://www.youtube.com/watch?v=P6zUHCwqcdM
```
But the final answer seems weighted more on the "outputs" section of the research steps generated the plan. Need to investigate how the "outputs" section was created in the plan. It was not from the tool calls. It seemed created directlly from the planner.