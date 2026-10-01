# SynBioCrow 2.3 final release handoff

Current release-packaging HEAD:
`1718a07c1d2bcb672182f302be472ee6c7ff6299`

Scientific freeze commit:
`39b3b21d8a5018001746a1ad783859cba75f9ad5`

Release-support package SHA-256:
`2be72abfd4d3fc123d22a09002dc6718c4f7f33b2d0cf4ed40884e8463fd5462`

At handoff, CI for the final three support-asset commits was still running. Do not tag until the HEAD run succeeds.

The ChatGPT GitHub connector available in this session can edit repository files and inspect CI, but it does not expose tag creation or GitHub Release creation. No Zenodo publishing connector is available. The companion release commands perform the exact GitHub tag/release steps once CI is green.
