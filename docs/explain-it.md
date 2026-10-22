# How to explain The Unbribable Referee

## The 30-second version

> AI game masters are LLMs, and LLMs are trained to be helpful, so if a player confidently
> claims "I have a legendary sword", the narrator usually goes along with it. I built a text
> adventure where Amazon Nova on Amazon Bedrock tells the story, but every action passes a
> referee first: Strands Decider 2B, a small model that can't write text, only answer typed
> questions with probabilities. It checks two things: is the action grounded in the game's
> facts, and is the player trying to bend the rules? If not, the action is cancelled and the
> narrator has to say no in character. Bedrock generates, Decider decides.

## The 2-minute version (the story arc)

1. **Problem.** The narrator is the thing being persuaded. With the referee off, Nova gave my
   halfling the golden crown and 1,000 gold for "casting a spell" from a cookbook.
2. **The decision.** Before any game tool runs, a Strands `InterventionHandler`
   (`before_tool_call`) sends Decider the world facts, the player's message and the proposed
   tool call, and asks:
   - *grounded* (yes/no): does the action rely only on things the facts establish?
   - *manipulation* (yes/no): is the player trying to change the rules out of character?
   - *plausible* (score, impossible → certain): how likely is it to succeed?
3. **Policy, in plain Python.**
   - grounded below 0.45, or manipulation 0.5 or more → **blocked** (`Guide`: the tool is
     cancelled and the narrator gets feedback).
   - grounded 0.45–0.6 → **not sure**: the narrator asks the player to clarify.
   - otherwise → **allowed**, and the plausibility distribution sets the d20 difficulty.
4. **Measured.** 58 labelled moves + 24 held-out moves, four judges compared (numbers below).
5. **Reusable.** `GroundedClaimGuard` doesn't know about games. Give it any source of truth
   (a customer record) and the tools to gate (refunds), and it stops "support promised me a
   double refund".

## Numbers to remember

| | |
|---|---|
| Fresh cheats caught: rules / Decider / Nova judge | 58% / 92% / 92% |
| Honest moves wrongly blocked on fresh moves: rules / Decider | 33% / 8% (and that one gets a clarifying question, not a refusal) |
| Disguised cheats ("my dagger is secretly legendary") | rules 0 of 7, Decider 7 of 7 |
| Cost per 1,000 decisions | Decider $0 (local), Nova judge $0.19 |
| Latency | Decider ~14 s on my 2019 laptop CPU (~115 ms on a GPU per Strands Labs); Nova judge ~750 ms |
| Thresholds | blocked < 0.45, unsure 0.45–0.6, manipulation ≥ 0.5 |

## Words to use precisely

- **Strands Decider 2B**: a ~1.9B-parameter open decision model from AWS Strands Labs.
  Built on Qwen3.5-2B with the text head replaced by a small "pointer head". Returns
  probabilities, never text.
- **Calibrated**: when it says 0.9, it's right about 90% of the time (upstream reports ≥0.9
  answers are right ~95% of the time on unseen tasks).
- **Grounded**: supported by the facts we actually hold, not just claimed by the user.
- **Guide vs Deny**: `Deny` just refuses; `Guide` cancels the step *and* hands the model
  feedback so it corrects course. We use Guide so the story keeps flowing.
- **Held-out set**: test cases written after the thresholds were picked, so the results
  aren't tuned to the test.

## Questions you'll likely get, and good answers

**Why not just check the inventory in code?**
We do. Exact checks live in the tools and are perfect. But "my rusty dagger is secretly
legendary" passes every exact check because the dagger is real. Code can't parse the claim;
Decider can. Code and Decider together caught every cheat in the main set.

**Why not ask an LLM to judge instead?**
Honestly, a *separate* LLM judge call worked well too: Nova 2 Lite was as accurate as Decider
on my sets and faster on my laptop. What fails is the *narrator* judging its own story.
Decider's advantages are $0 per decision instead of $190 per million, nothing leaves the
machine, a calibrated number instead of parsed text, and ~115 ms on a GPU.

**Can Decider be prompt-injected?**
It can be wrong, but it can't be argued into *writing* "you succeed": it only outputs
probabilities, and my code owns the threshold. In the main set it flagged 7 of 8
out-of-character tricks on its own; the code layer caught the remaining one.

**Why those thresholds?**
Picked on the 58-case set (honest moves never scored below 0.70 on grounded), then checked on
24 new cases written afterwards. The sets are small, so I treat the numbers as evidence, not
proof.

**Why is it 14 seconds?**
My laptop has no usable GPU, so Decider runs on CPU in fp32 (about 9 GB of RAM). For a
turn-based game that's tolerable. The repo includes a free Colab GPU notebook.

**What happens when Decider is unsure?**
Between 0.45 and 0.6 on grounded, the agent asks the player a clarifying question instead of
refusing. On the held-out set, the one honest player Decider doubted landed in that band.

**How do the dice work?**
The plausibility answer is a probability distribution over five levels. I fold it into one
success chance, convert that to a d20 difficulty (DC), and roll. So the dice are loaded with
the model's actual confidence.

**What would you do next?**
Serve Decider on a GPU, grow the evaluation set, tune thresholds per tool, and try the guard
in a non-game agent (refunds or IT helpdesk) with real traffic.

**What did you learn?**
Hand-written rules overfit quietly; a held-out set exposed it. Decision models shine on fuzzy
claims code can't parse. And the generator shouldn't judge its own output.
