#!/usr/bin/env python
"""Small local audio analyzer for SFX iteration.

Supports WAV and common compressed formats through miniaudio. The output is
plain text on purpose, so it can be pasted into notes or compared between runs.
"""

from __future__ import annotations

import argparse
import math
import wave
from dataclasses import dataclass
from pathlib import Path

import miniaudio
import numpy as np


Band = tuple[int, int]

BANDS: list[Band] = [
    (0, 60),
    (60, 120),
    (120, 250),
    (250, 500),
    (500, 1000),
    (1000, 2500),
    (2500, 5000),
    (5000, 10000),
]


@dataclass
class SegmentStats:
    start: float
    end: float
    rms_db: float
    centroid_hz: float
    rolloff85_hz: float
    flatness: float
    zcr: float
    bands: list[float]


@dataclass
class AudioStats:
    path: Path
    sample_rate: int
    channels: int
    duration: float
    peak_db: float
    rms_db: float
    active_40: tuple[float, float] | None
    active_30: tuple[float, float] | None
    active_20: tuple[float, float] | None
    side_mid_db: float | None
    peaks: list[tuple[float, float]]
    segments: list[SegmentStats]
    hints: list[str]


def db(value: float) -> float:
    return 20.0 * math.log10(max(float(value), 1e-12))


def load_audio(path: Path) -> tuple[int, np.ndarray]:
    suffix = path.suffix.lower()
    if suffix == ".wav":
        with wave.open(str(path), "rb") as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            raw = wav.readframes(wav.getnframes())
        if sample_width != 2:
            raise ValueError(f"Only 16-bit PCM WAV is supported directly: {path}")
        audio = np.frombuffer(raw, dtype="<i2").reshape(-1, channels).astype(np.float32)
        return sample_rate, audio / 32768.0

    decoded = miniaudio.decode_file(str(path), output_format=miniaudio.SampleFormat.SIGNED16)
    audio = np.frombuffer(decoded.samples, dtype=np.int16).reshape(-1, decoded.nchannels)
    return decoded.sample_rate, audio.astype(np.float32) / 32768.0


def active_range(envelope: list[float], threshold: float, hop_seconds: float) -> tuple[float, float] | None:
    active = [value > threshold for value in envelope]
    if not any(active):
        return None
    start = next(i for i, flag in enumerate(active) if flag) * hop_seconds
    end = (len(active) - 1 - next(i for i, flag in enumerate(reversed(active)) if flag)) * hop_seconds
    return start, end


def band_fractions(power: np.ndarray, freqs: np.ndarray) -> list[float]:
    totals = []
    for lo, hi in BANDS:
        totals.append(float(power[(freqs >= lo) & (freqs < hi)].sum()))
    total = sum(totals)
    if total <= 0.0:
        return [0.0 for _ in totals]
    return [value / total for value in totals]


def segment_stats(mono: np.ndarray, sample_rate: int, start: float, end: float) -> SegmentStats | None:
    lo = max(0, int(start * sample_rate))
    hi = min(len(mono), int(end * sample_rate))
    segment = mono[lo:hi]
    if len(segment) < 2048:
        return None

    nfft = 2048
    hop = 512
    window = np.hanning(nfft).astype(np.float32)
    freqs = np.fft.rfftfreq(nfft, 1.0 / sample_rate)

    centroid_values: list[float] = []
    rolloff_values: list[float] = []
    flatness_values: list[float] = []
    band_totals = np.zeros(len(BANDS), dtype=np.float64)

    frame_powers: list[float] = []
    for offset in range(0, len(segment) - nfft, hop):
        frame = segment[offset : offset + nfft] * window
        power = np.abs(np.fft.rfft(frame)) ** 2
        frame_powers.append(float(power.sum()))

    max_frame_power = max(frame_powers) if frame_powers else 0.0
    min_frame_power = max(max_frame_power * 1e-6, 1e-12)

    for offset in range(0, len(segment) - nfft, hop):
        frame = segment[offset : offset + nfft] * window
        power = np.abs(np.fft.rfft(frame)) ** 2
        total_power = float(power.sum())
        if total_power < min_frame_power:
            continue
        power_for_flatness = power + 1e-18
        centroid_values.append(float((freqs * power).sum() / total_power))
        cumulative = np.cumsum(power)
        rolloff_values.append(float(freqs[np.searchsorted(cumulative, 0.85 * total_power)]))
        flatness_values.append(
            math.exp(float(np.mean(np.log(power_for_flatness)))) / float(np.mean(power_for_flatness))
        )
        band_totals += np.array(band_fractions(power, freqs)) * total_power

    bands = (band_totals / band_totals.sum()).tolist() if band_totals.sum() > 0 else [0.0] * len(BANDS)
    zcr = float(np.mean(np.abs(np.diff(np.signbit(segment))))) if len(segment) > 1 else 0.0

    return SegmentStats(
        start=start,
        end=min(end, len(mono) / sample_rate),
        rms_db=db(math.sqrt(float(np.mean(segment * segment)))),
        centroid_hz=float(np.mean(centroid_values)) if centroid_values else 0.0,
        rolloff85_hz=float(np.mean(rolloff_values)) if rolloff_values else 0.0,
        flatness=float(np.mean(flatness_values)) if flatness_values else 0.0,
        zcr=zcr,
        bands=bands,
    )


def local_peaks(envelope: list[float], hop_seconds: float, threshold: float = 0.04) -> list[tuple[float, float]]:
    peaks: list[tuple[float, float]] = []
    for index, value in enumerate(envelope):
        prev_ok = index == 0 or value >= envelope[index - 1]
        next_ok = index == len(envelope) - 1 or value >= envelope[index + 1]
        if value > threshold and prev_ok and next_ok:
            peaks.append((index * hop_seconds, db(value)))
    return sorted(peaks, key=lambda item: item[1], reverse=True)


def make_hints(
    duration: float,
    active_40: tuple[float, float] | None,
    peaks: list[tuple[float, float]],
    side_mid_db: float | None,
    segments: list[SegmentStats],
) -> list[str]:
    hints: list[str] = []
    if active_40:
        active_len = active_40[1] - active_40[0]
        if active_len < min(0.75, duration * 0.45):
            hints.append("short event: active audio is brief, likely a single swing/hit rather than a sustained layer")
        elif active_len > duration * 0.75:
            hints.append("sustained event: active audio covers most of the file")
    if len(peaks) >= 4:
        hints.append("multiple transient peaks: may read as repeated swings, multiple hits, or rotating passes")
    elif len(peaks) == 1:
        hints.append("single dominant peak: may read as one swing or one impact")
    if side_mid_db is not None:
        if side_mid_db > -8:
            hints.append("wide stereo: strong side energy, useful for pass-by or orbit motion")
        elif side_mid_db < -25:
            hints.append("narrow stereo: weak side energy, orbit/rotation may not be audible")
    if segments:
        first = segments[0]
        low = sum(first.bands[:3])
        high = sum(first.bands[5:])
        if low > 0.75 and first.centroid_hz < 180:
            hints.append("very low-heavy: may become a rumble/drone instead of audible air movement")
        if high > 0.12 or first.centroid_hz > 1200:
            hints.append("bright/noisy: may read as sharp slash, hiss, or whistle")
    return hints


def analyze(path: Path, segments: list[tuple[float, float]]) -> AudioStats:
    sample_rate, audio = load_audio(path)
    mono = audio.mean(axis=1)
    duration = len(mono) / sample_rate

    peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
    rms = math.sqrt(float(np.mean(mono * mono))) if len(mono) else 0.0

    hop_seconds = 0.01
    win = max(1, int(sample_rate * hop_seconds))
    envelope: list[float] = []
    for offset in range(0, len(mono), win):
        chunk = mono[offset : offset + win]
        envelope.append(math.sqrt(float(np.mean(chunk * chunk))) if len(chunk) else 0.0)

    side_mid_db = None
    if audio.shape[1] == 2:
        mid = (audio[:, 0] + audio[:, 1]) / 2.0
        side = (audio[:, 0] - audio[:, 1]) / 2.0
        mid_rms = math.sqrt(float(np.mean(mid * mid)))
        side_rms = math.sqrt(float(np.mean(side * side)))
        side_mid_db = db(side_rms / max(mid_rms, 1e-12))

    stats_segments = [item for item in (segment_stats(mono, sample_rate, s, e) for s, e in segments) if item]
    peaks = local_peaks(envelope, hop_seconds)[:12]
    hints = make_hints(
        duration,
        active_range(envelope, 0.01, hop_seconds),
        peaks,
        side_mid_db,
        stats_segments,
    )

    return AudioStats(
        path=path,
        sample_rate=sample_rate,
        channels=audio.shape[1],
        duration=duration,
        peak_db=db(peak),
        rms_db=db(rms),
        active_40=active_range(envelope, 0.01, hop_seconds),
        active_30=active_range(envelope, 0.03, hop_seconds),
        active_20=active_range(envelope, 0.10, hop_seconds),
        side_mid_db=side_mid_db,
        peaks=peaks,
        segments=stats_segments,
        hints=hints,
    )


def fmt_range(value: tuple[float, float] | None) -> str:
    if value is None:
        return "none"
    return f"{value[0]:.2f}-{value[1]:.2f}s"


def print_stats(stats: AudioStats) -> None:
    print(f"\n=== {stats.path} ===")
    print(f"sample_rate: {stats.sample_rate} Hz")
    print(f"channels: {stats.channels}")
    print(f"duration: {stats.duration:.3f}s")
    print(f"peak_dbfs: {stats.peak_db:.1f}")
    print(f"rms_dbfs: {stats.rms_db:.1f}")
    print(f"active_gt_-40dbfs: {fmt_range(stats.active_40)}")
    print(f"active_gt_-30dbfs: {fmt_range(stats.active_30)}")
    print(f"active_gt_-20dbfs: {fmt_range(stats.active_20)}")
    if stats.side_mid_db is not None:
        print(f"side_to_mid_db: {stats.side_mid_db:.1f}")
    if stats.peaks:
        print("top_peaks: " + ", ".join(f"{time:.2f}s:{level:.1f}dB" for time, level in stats.peaks))
    if stats.hints:
        print("hints:")
        for hint in stats.hints:
            print(f"- {hint}")
    print("segments:")
    for segment in stats.segments:
        bands = ", ".join(
            f"{lo}-{hi}:{fraction:.2f}" for (lo, hi), fraction in zip(BANDS, segment.bands)
        )
        print(
            f"- {segment.start:.2f}-{segment.end:.2f}s "
            f"rms={segment.rms_db:.1f}dB centroid={segment.centroid_hz:.1f}Hz "
            f"roll85={segment.rolloff85_hz:.1f}Hz flat={segment.flatness:.4f} zcr={segment.zcr:.3f}"
        )
        print(f"  bands {bands}")


def parse_segment(value: str) -> tuple[float, float]:
    try:
        start, end = value.split(":", 1)
        return float(start), float(end)
    except Exception as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError("segments must look like START:END, for example 0:0.5") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze SFX audio files with lightweight local features.")
    parser.add_argument("paths", nargs="+", type=Path, help="Audio files to analyze")
    parser.add_argument(
        "--segment",
        action="append",
        type=parse_segment,
        help="Segment to analyze, as START:END seconds. Can be repeated.",
    )
    args = parser.parse_args()

    segments = args.segment or [(0.0, 0.5), (0.0, 1.0), (0.5, 1.0), (1.0, 1.5)]
    for path in args.paths:
        print_stats(analyze(path, segments))


if __name__ == "__main__":
    main()
