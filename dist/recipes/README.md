# Official Fritchii preparation recipe

`OoT v131072 (cache v54).nx2recipe` is copied unchanged from the official
[Fritchii v5.6 Windows release](https://github.com/Frizti/Fritchii/releases/tag/fritchii-v5.6).
Source tag: `696a456641ae83c9f8b6564c57ac311c7ef56799`.

- Release archive SHA256: `3266298fe6b13aa98b72fd3fb05c219475608661fbe7e4b97902e719acb4c699`
- Recipe SHA256: `85d944c8557fbeffe02af566c9c4277251ed0ab1a0f2a3ab7a626af6a877c3a1`
- Recipe size: 1,821,351 bytes.

Recipes contain pipeline state and translation facts rather than game shader code;
Fritchii assembles them using the owner's local game. See
`tools/nx2-precompile/README.md` and `src/video_core/nx2_recipe.h` for the format and
audit tool. The build and AppImage scripts place this beside the executable under
`recipes/`. Existing user shader files are not replaced. Refresh from a verified
matching official release when updating, and audit against the local game.

Verified again against the official [v5.7 release](https://github.com/Frizti/Fritchii/releases/tag/fritchii-v5.7): the recipe is byte-identical.

- v5.7 source: `52317bf0e5` (see tag for full commit).
- v5.7 Windows archive SHA256: `245489bd70075e9913d670683dd28a92b0bab286b03a190fce07dc1dc0233843`.
- No cache-format or recipe-byte change is required for this baseline update.

Verified byte-identical in official v5.8.4 (`4f5c53149b`). Release archive SHA256: `8fbe37d69665e8264bf9e92fe40846961923cff29dc165f8fdafe193605d10da`.
