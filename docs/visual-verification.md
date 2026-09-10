# Visual State Verification Architecture

## Overview
`VisualStateVerifier` integrates screen state comparison with JARVIS's core `VerificationManager`.

## Verification Flow
1. Capture initial screen state `S1` prior to action execution.
2. Execute computer control action (e.g. click "Play").
3. Capture post-action screen state `S2`.
4. Perform `ScreenComparator.compare(S1, S2)`.
5. Evaluate expected change (e.g. text change from "Play" to "Pause" or window visibility change).

## Preventing False Success
JARVIS never declares an action successful based solely on tool invocation. Visual state comparison provides empirical proof of state transitions.
