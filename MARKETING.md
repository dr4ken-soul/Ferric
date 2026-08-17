# MARKETING.md, Ferric

## Is This Required?

No. The Ready, Spec, Ship rules require a public repository, the `.kiro` directory, a complete README, a working demo or test build, a demo video, testing instructions, and submission through the official Google Form. Posting on X is not a submission requirement and there is no social or community track in the rubric.

So this file exists for one reason only: the judging window runs from 24 August to 5 September, twelve days in which three named judges are looking at submissions. John Crickett, Angie Jones and Gregor Ojstersek all have a public presence and all three write about exactly this problem space. A post that reaches them before they open the repository costs twenty minutes and changes nothing about the build.

The rule for everything below: it is written after the submission is in, never instead of it. If day nine is tight, delete this file and submit. Nothing here is worth a single point.

---

## Posting Style

- all lowercase
- builder voice, not company voice
- one clear idea per post
- short lines with space between thoughts
- show what works, do not explain what you plan to build
- the demo video does the heavy lifting, copy supports it
- no hashtags, no thread padding, no engagement bait

---

## Post Plan

### post 1, at submission, 23 august

```
submitted ferric to the ready, spec, ship hackathon

your ai feature has no test suite because output is non deterministic and calling a live model in ci costs money and flakes

so ferric records every prompt, tool call and response into a cassette, then replays them offline with zero network and zero spend

assertions run on the shape of the interaction, tool call order, argument fields, schema validity, not the wording, so a reworded response passes and a reordered tool call fails

the whole thing was spec driven in kiro, and ferric recorded kiro's own tool calls while it was being built, those cassettes ship as the demo fixture

clone it, pip install, pytest, no api key needed

[repo] [demo video]
```

Attach the demo video directly rather than linking out. Video that plays in the timeline gets watched, a link does not.

### post 2, the drift report, 25 august

Only post this if post 1 landed. A second post into silence is worse than one post.

```
the part of ferric i did not expect to like most

run ferric drift --to a new model version and it replays your whole cassette library against it, then tells you what actually changed

not that the wording moved, that the tool call order moved, or the schema broke, or a refusal stopped firing

model upgrades stop being a leap of faith

report is a single html file with no dependencies, opens straight off your filesystem

[screenshot of the report, diverged row visible]
```

The image here is a screenshot of the report, which is allowed, because it is a social post rather than a claim about working functionality on the product page. The authenticity rules govern the site, not the timeline.

---

## Submission Notes

**Project title:** Ferric

**Tagline:** Your AI feature has no test suite.

**Category:** AI Agent and CLI Tool, open theme.

**Price:** free, MIT licensed, no account, no hosted service.

**Built with:**
- Python 3.11, pydantic, typer, pytest
- React 18, Vite, TypeScript, Tailwind CSS
- motion/react, GSAP ScrollTrigger
- Kiro: specs, steering, four hooks, and the MCP adapter recording Kiro's own tool calls

**Project description, under 200 words:**

Ferric is a flight recorder for LLM and agent traffic. Wrap your model client in one line and it captures every prompt, tool call and response into a cassette on disk. In CI, those cassettes replay offline with no network access and no API spend, so your AI tests are fast, free and deterministic.

The assertions are the point. Instead of comparing strings, which break the moment a model rewords itself, Ferric asserts on the shape of the interaction: did it call the right tools, in the right order, with the right critical arguments, did the response validate against the schema, did anything leak. A reworded answer passes. A reordered tool call fails.

`ferric promote` turns a real production interaction into a checked-in test, so your regression suite is built from reality rather than imagination. `ferric drift` replays your whole library against a new model version and reports what behaviourally changed before you upgrade.

Ferric was built spec-first in Kiro, and it recorded Kiro's own tool calls while it was being built. Those cassettes ship as the demo fixture. Clone, install, run pytest. No API key needed.

**Demo video flow, three minutes:**

1. The problem, a prompt edit that nothing catches, 20 seconds
2. Record a real interaction, replay it offline, identical output, 30 seconds
3. Change the model version, the tool order assertion fails with the divergence printed, 30 seconds
4. The Kiro trail, the day one spec session, tasks driving the build, a hook firing, 60 seconds
5. The cassettes of Kiro's own tool calls, recorded by Ferric, 20 seconds
6. Clean machine install, offline suite passing, 20 seconds
7. The drift report open in a browser, and the limitations named out loud, 15 seconds

---

## Checklist

- [ ] Submission through the official Google Form completed first, before anything below
- [ ] Repository public, `.kiro` directory committed and visible
- [ ] Demo video uploaded, unlisted is fine, link tested in a private window
- [ ] Clean machine clone tested, install and pytest pass with no API key
- [ ] Post 1 goes out only after the form is submitted
- [ ] Video attached directly to the post, not linked
- [ ] Post 2 only if post 1 landed, and only if the report screenshot is real
- [ ] Nothing in either post claims a feature that is not in the repository
