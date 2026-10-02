# Discovery Lens

A tool for teachers. Paste an explanation written by an AI (or a textbook), choose the grade, subject and standards, and Discovery Lens:

1. **Flags the wording to watch**: analogies, figurative language, technical words, overgeneralizations, missing conditions.
2. **Rebuilds the explanation as a discovery version**: students get observations and clues first; the model or definition comes only at the end.
3. **Proposes three ways in** to the same idea (safety rule: no heat in students' hands below grade 9).
4. **Places it in a lesson sequence**, aligned with the standards the teacher names, with what to teach before and after.
5. **Collects the teacher's verdict** and exports everything as JSON.

No student data is entered or stored.

- Live version (AI analysis): https://claude.ai/artifact/X99SRuquEomuXZ2gw2gHGR
- Offline copy (pre-loaded examples only): [`index.html`](index.html)

It is an application of the same natural-logic analysis as the [Grize–Charconnet analyzer](../analyseur-grize.html): an analogy that slides from *is like* to *is* is exactly the kind of wording that plants misconceptions in a classroom.

Jean Charconnet, 2026

## Pilot

Three pilot runs, 29–30 September 2026, by a teacher, on an AI-generated French text about the states of matter (grades 5–6, Utah standards). Files in [`pilote/`](pilote/):

| Run | Teacher verdict | What changed afterwards |
|---|---|---|
| [1](pilote/essai1_2026-09-29.json) | "Yes, after editing": wants *a sequence with different activities* | Added a lesson sequence |
| [2](pilote/essai2_2026-09-29.json) | "Yes, after editing": wants *what to do before and after* | Added curriculum placement and the lessons before/after; grade and subject made required |
| [3](pilote/essai3_2026-09-30.json) | "Yes, as is": every part rated *Very useful* | — |

The source text is in [`etats_matiere_pour_analyseur.json`](pilote/etats_matiere_pour_analyseur.json).
