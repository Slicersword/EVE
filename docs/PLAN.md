# Build and maintenance plan

Use [Build guide](BUILD_GUIDE.md) for the construction sequence and
[Software setup](SETUP_GUIDE.md) for M00–M17. Every new build starts at M00.

## Release checks

1. Verify locked public defaults and regenerate the firmware header when required.
2. Regenerate the software guide from its recipes and check local links.
3. Run host tests, shell/Python checks and both Mega target compilations.
4. Build the website and validate offline links/assets/source listings.
5. Review the diff for private data, unintended hardware changes and misleading acceptance claims.
6. Publish the tested commit; Pages can regenerate the same documentation on every push.

## Builder validation

Complete power measurements, per-channel sensor tests, refusal/stop behavior,
lifted wheel tests, manual head limits and the final attended run on each robot.
Record the exact hardware and software revision privately.

Future hardware variants, full-duplex audio, battery monitoring and navigation
are separate design work. They are not implied by a complete reference-build guide.
