# Shot 01 — "Synapse Chamber" (9:16, 3s)

Cinematic scientific-documentary shot: a realistic human brain glowing with blue and
orange neural connections, suspended in a glass chamber in a dark futuristic laboratory.

## Deliverables

| File | Purpose | Specs |
|---|---|---|
| `brain_documentary_9x16.mp4` | delivery master | 1080×1920 (9:16), 30 fps, 3.00 s, H.264 High, CRF 18, silent, ~13 MB, `+faststart` |
| `brain_documentary_9x16.webm` | inline/browser preview | VP9, 1080×1920, 30 fps, 3.00 s, ~2 MB |
| `poster.jpg` | thumbnail / cover frame (mid push-in) | 1080×1920 |
| `storyboard_6x1.jpg` | 6 moments across the 3 s (motion check) | 6 × 272×484 tile |
| `media/brain_lab_keyframe.png` | source keyframe the shot is built from | 768×1376 (centre-cropped to exact 9:16) |
| `render_shot.py` | reproducible renderer (see below) | — |

No text, no logos, no watermarks, no UI elements anywhere in the frame.

## Shot design

* **Camera** — slow eased (smoothstep) push-in, 1.00 → 1.14 over the 3 s, with a subtle
  upward tilt (centre 0.515 → 0.480). Rendered from a 2× buffer so every output frame is a
  downscale: sub-pixel smooth and crisp at 1080×1920.
* **Neural activity** — bright filaments bleed light (screen-blended bloom) modulated by a
  traveling low-frequency light field, so blue pathways and orange pulses light up in
  different regions at different moments.
* **Electrical pulses** — 16 real bright nodes are detected in the keyframe; random flashes
  with fast attack/exponential decay and 14 Hz flicker fire on them at randomised times.
  Because they are anchored in image space, they pan and scale with the camera.
* **Grade** — exposure breathing (documentary-camera feel), S-curve contrast, teal shadows /
  warm highlights, lens vignette, slight edge chroma split, fine luma-weighted film grain,
  final unsharp pass.

## Re-render / adapt

```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install numpy pillow imageio-ffmpeg
/tmp/venv/bin/python render_shot.py
```

Useful knobs at the top of `render_shot.py`:

* `SRC` — point at any other keyframe to build the same shot from a different image.
* `DUR`, `FPS`, `OUT_W`, `OUT_H` — shot length, frame rate, resolution (e.g. 2160×3840 for 4K).
* `ZOOM_END` — push-in strength (`1.0` = locked-off, `1.25` = stronger push).
* `SEED` — different pulse/bloom choreography.

## Notes

* The file is silent by design. Add score/SFX over it, e.g.
  `ffmpeg -i brain_documentary_9x16.mp4 -i score.wav -c:v copy -c:a aac -shortest out.mp4`.
* If a shot with *generated* temporal motion is preferred over this keyframe-driven render
  (no real text-to-video model was available here), the same prompt below can be run through
  any video model — keyframe above is a ready first/last-frame reference.

## Generation prompt (keyframe)

> Cinematic scientific documentary film still, vertical 9:16 composition, centered: an
> ultra-realistic anatomical human brain suspended in a transparent glass chamber inside a
> dark futuristic laboratory. The brain glows from within with blue and orange neuron-like
> filaments — electric cyan-blue neural pathways branching across the cortex, warm amber-orange
> pulses of light threading through the synapses, small bright spark points of neural activity.
> Dramatic volumetric lighting: strong low-angle rim light, visible light shafts and haze
> cutting through darkness, teal-blue fill on one side and warm orange key on the other.
> High contrast, deep black background with subtle out-of-focus lab equipment silhouettes and
> faint bokeh instrument lights far behind. Shallow depth of field, macro lens detail on the
> brain's folds, wet glistening surface texture, ultra-detailed, photorealistic, shot on ARRI
> Alexa with anamorphic lens, film grain, moody sci-fi realism. No text, no letters, no logos,
> no watermarks, no user interface elements.
