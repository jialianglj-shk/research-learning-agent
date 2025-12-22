# Week 3 Evaluation - Planner & Clarification Loop

This document records test scenarios demonstrating:
- intent classification
- explicit planning
- clarification loop (counded turns)
- forced-final answer with assumptions

## Scenario 1 - Casual curiosity
**User question:** I saw the word "CNN" in an online AI discussion. What is that? Just checking.

**Intent (summary):**
- Intent: casual_curiosity
- Confidence: 0.85

**Clarification (summary):**
- q1: Are you interested in a simple overview of CNNs or how they relate specifically to LLMs and GenSAT?
- a1: just simple overview

**Plan (smmuary):**
- s1: explain - what CCN (Convolutional Neural Network) is in simple terms...
- s2: explain - Brifly describe common applications of CMMs to help relate the concept to real-world uses.
- s3: finalize - Summarize the explanation concisely and confirm understanding

**Answer:**\
EXPLANATION:
CNN stands for Convolutional Neural Network. It is a type of artificial intelligence model designed to process and understand visual data like images and videos. Unlike traditional AI models that treat input data as a simple list, CNNs look at small parts of the image at a time (called "convolutions") to detect patterns such as edges, shapes, or textures. This makes CNNs especially good at recognizing objects, faces, or scenes in images.

BULLETS:
- CNNs are AI models specialized for analyzing images and videos.
- They work by scanning small sections of an image to find patterns.
- This approach helps CNNs recognize objects and features more effectively than basic models.
- Common uses include image recognition, facial recognition, and medical image analysis.

**Answer notes**
- Answer is concise
- Bullets are clear

## Scenario 2 - Guided Study
**User question:** Make me a 7-day plan to learn reinforcement learning.

**Intent (summary):**
- Intent: guided_study
- Confidence: 0.85

**Clarification (summary):**
- q1: Do you want the plan to focus on high-level concepts for beginner or include tech details?
  - a1: high-level concepts for beginner
- q2: RL theory/practical app, or how it relates to LLM and GenAI technologies?
  - a2: just foucs on the RL theory and basics
- q3: Do you prefer the plan to include practical examples or focus solely on theoretical concepts?
  - a3: only theoretical concepts
 
 **Plan (summary):**
- s1: clarify - Confirm user's familiarity with basic machine learning concepts to tailor the RL learning plan
- s2: outline - Outline the key theoretical topics in RL to cover in 7 days, including foundational concepts, key alogorithms, and applications.
- s3: study_plan - Create a detailed 7-day study plan focusing on theoretical RL concepts, with daily topics and concise explanations suitable for beginner without CS background
- s4: explain - Provide concise explanations of key RL concepts sch as agents, env, rewards, policies, value functions, and exploration vs exploitation.
- s5: finalize - Deliver the complete 7-days study plan

**Answer (notes)**
- a 7-days RL study plan is provided with different focuse on each day.
- The bullets points highly summarized the plan. Looks OK.

## Scenario 3 - Prefessional Research
**User Question:** I need a quick and concise report for a research project. Compare PPO vs DQN and when to use each.

**Intent (summary):**:
- Intent: guided_study (expect to be professional research)
- Confidence: 0.85 (it seems always to be 0.85)

**Clarification (summary):**
- Agent asked 3 (maximum allowed) clarifying questions but they seem a bit redundant. The current logic use the clarifying question from intent first, but the clarifying question from the plan seems more reasonable.

**Plan (summary):**
- s1: outline - Outline the key concepts of PPO and DQN in simple terms suitable for a beginner (the user prodile indicating I am a product manager with limited CS background)
- s2: explain - Explain the main differences between PPO and DQN, focusing on their approach, strengths, and weaknesses.
- s3: explain - Describe typical use cases where each would be preferred
- s4: finalize - Summarize the comparison in a concise report format suitable for a research project

**Answer (notes)**
- The answer explains PPO, DQN, main differences, and summary for the choice for research project
- Answer is decent.