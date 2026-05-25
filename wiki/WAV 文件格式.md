---
title: WAV 文件格式
tags:
- audio
- wav
- riff
- pcm
- game-audio
sources:
- raw/Audio/2026-05-21-3001001-wav-riff-structure.md
- Tmp/export_wav_structure.py
- Tmp/3001001_wav_structure.json
- https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff-
- https://learn.microsoft.com/zh-cn/windows/win32/api/mmeapi/ns-mmeapi-waveformatex
- https://tech.ebu.ch/publications/tech3285
confidence: confirmed
status: published
created: 2026-05-21
updated: 2026-05-21
---

# WAV 文件格式

Status: wiki
Last verified: 2026-05-21

## Summary

WAV 通常是 `RIFF` 容器中的 `WAVE` 文件。顶层结构是：

```text
RIFF header:
  Chunk ID: "RIFF"
  Chunk Size: file_size - 8, little-endian uint32
  Format: "WAVE"

Subchunks:
  Chunk ID: 4-byte FOURCC
  Chunk Size: little-endian uint32, only valid data size
  Data: chunk payload, padded to WORD boundary when needed
```

最常见的 PCM WAV 至少要有 `fmt ` 和 `data` 两类块。`fmt ` 描述音频格式，`data` 保存音频采样数据。RIFF 允许额外块存在，例如 `bext`、`junk`、`LIST`、`fact`、`smpl` 等，所以解析器不能把 WAV 写死成 44 字节头，也不能假设 `fmt ` 后面一定紧跟 `data`。

## PCM `fmt ` 字段

PCM 的 `fmt ` 块常见大小是 16 字节，对应字段：

| 字段 | 含义 |
| --- | --- |
| `AudioFormat` | `1` 表示 PCM；非 PCM 或 extensible 会有其他标记。 |
| `NumChannels` | 声道数，单声道为 1，立体声为 2。 |
| `SampleRate` | 每秒采样帧数，例如 44100 或 48000。 |
| `ByteRate` | PCM 中应等于 `SampleRate * BlockAlign`。 |
| `BlockAlign` | 每个采样帧的字节数，PCM 中等于 `NumChannels * BitsPerSample / 8`。 |
| `BitsPerSample` | 每个单声道 sample 的位深，例如 16。 |

`BlockAlign` 是读取 PCM 的基本步长。双声道 16-bit PCM 的 `BlockAlign` 是 `2 * 16 / 8 = 4` 字节，每一帧通常按声道交错存储，例如 `[L0, R0][L1, R1]...`。16-bit PCM 的 sample 在 WAV 中按 little-endian 存储；8-bit PCM 等格式有不同取值约定，不能混用判断。

## `data` 块

`data` 块大小是音频采样字节数，不包含 chunk header 和 padding。PCM 中可以用：

```text
frame_count = data_size / block_align
duration_seconds = frame_count / sample_rate
```

如果 `data_size` 不能被 `block_align` 整除，通常说明文件损坏、解析偏移错误，或格式不是按当前 `fmt ` 字段理解的 PCM 数据。

## 3001001.WAV 实测

`D:/mmo_program_framework/3001001.WAV` 的 Python 导出结果：

```text
file_size: 692370
RIFF chunk_size: 692362
format: WAVE
chunk_order: fmt , bext, junk, data

fmt:
  audio_format: 1 (PCM)
  channels: 2
  sample_rate: 44100
  byte_rate: 176400
  block_align: 4
  bits_per_sample: 16

data:
  offset: 690
  size: 691680
  frames: 172920
  duration: 3.921088435s
```

### 3001001.WAV 具体字节结构

这个文件的真实布局不是最简 44 字节 PCM WAV 头，而是：

```text
0..11        RIFF/WAVE header
12..35       fmt  chunk
36..645      bext chunk
646..681     junk chunk
682..692369  data chunk
```

顶层 RIFF header：

| 文件偏移 | 长度 | 字节/值 | 含义 |
| --- | ---: | --- | --- |
| `0..3` | 4 | `52 49 46 46` / `RIFF` | RIFF 容器标记。 |
| `4..7` | 4 | `8A 90 0A 00` / `692362` | RIFF chunk size，等于 `file_size - 8`。 |
| `8..11` | 4 | `57 41 56 45` / `WAVE` | RIFF form type，说明这是 WAV。 |

`fmt ` chunk：

| 文件偏移 | 长度 | 字节/值 | 含义 |
| --- | ---: | --- | --- |
| `12..15` | 4 | `66 6D 74 20` / `fmt ` | 格式块 ID，末尾有一个空格。 |
| `16..19` | 4 | `10 00 00 00` / `16` | PCM `fmt ` payload 长度。 |
| `20..21` | 2 | `01 00` / `1` | `AudioFormat = PCM`。 |
| `22..23` | 2 | `02 00` / `2` | 双声道。 |
| `24..27` | 4 | `44 AC 00 00` / `44100` | 采样率。 |
| `28..31` | 4 | `10 B1 02 00` / `176400` | byte rate，`44100 * 4`。 |
| `32..33` | 2 | `04 00` / `4` | block align，`2 * 16 / 8`。 |
| `34..35` | 2 | `10 00` / `16` | 每声道 16 bit。 |

额外块：

| 文件偏移 | 长度 | 值 | 含义 |
| --- | ---: | --- | --- |
| `36..39` | 4 | `bext` | Broadcast Wave metadata 块。 |
| `40..43` | 4 | `602` | `bext` payload 长度；payload 位于 `44..645`。 |
| `646..649` | 4 | `junk` | 填充或预留块。 |
| `650..653` | 4 | `28` | `junk` payload 长度；payload 位于 `654..681`。 |

`data` chunk：

| 文件偏移 | 长度 | 字节/值 | 含义 |
| --- | ---: | --- | --- |
| `682..685` | 4 | `64 61 74 61` / `data` | 音频采样数据块 ID。 |
| `686..689` | 4 | `E0 8D 0A 00` / `691680` | PCM 数据字节数。 |
| `690..692369` | 691680 | PCM payload | 双声道 16-bit little-endian 交错采样。 |

计算校验：

```text
file_size = 692370
riff_size + 8 = 692362 + 8 = 692370
block_align = channels * bits_per_sample / 8 = 2 * 16 / 8 = 4
byte_rate = sample_rate * block_align = 44100 * 4 = 176400
frame_count = data_size / block_align = 691680 / 4 = 172920
duration = frame_count / sample_rate = 172920 / 44100 = 3.921088435s
```

PCM 数据预览：

```text
data first 32 bytes:
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00

first non-zero frame:
frame_index = 7450
absolute_file_offset = 690 + 7450 * 4 = 30490
time = 7450 / 44100 = 0.168934s
first frames as [left, right]:
[0, 1], [0, 1], [0, 0], [0, 1], [0, 1], [0, 1], [0, 0], [0, 0]
```

结论：它和常见图示一样是 RIFF/WAVE + PCM `fmt ` + PCM `data`，但不是最简 `fmt -> data` 结构。它中间有 `bext` Broadcast Wave 元数据块和 `junk` 填充块，因此 `data` 从偏移 690 开始，而不是最简 PCM WAV 常见的偏移 44。

## How To Use

检查 WAV 时先按 chunk 扫描，不要固定偏移：

```powershell
python Tmp\export_wav_structure.py "D:\mmo_program_framework\3001001.WAV" --out Tmp\3001001_wav_structure.json
```

判断 PCM WAV 的最小检查点：

- 顶层 `Chunk ID` 是 `RIFF`，`Format` 是 `WAVE`。
- `riff_chunk_size + 8 == file_size`。
- 存在 `fmt ` 和 `data`，且 `fmt ` 在 `data` 前面更利于流式解析。
- `AudioFormat == 1` 时，`BlockAlign == NumChannels * BitsPerSample / 8`。
- `AudioFormat == 1` 时，`ByteRate == SampleRate * BlockAlign`。
- `data_size % block_align == 0`。

遇到 `bext` 时可把它理解为 Broadcast Wave 元数据，不影响基本 PCM 采样读取；遇到 `junk` 时通常按填充或预留空间处理。两者都不应被误判为音频采样数据。

## Verification

2026-05-21 用 `Tmp/export_wav_structure.py` 解析 `D:/mmo_program_framework/3001001.WAV`，并用 Python 标准库 `wave` 模块交叉验证了声道数、采样率、帧数、sample width、未压缩标记和时长。通用 RIFF chunk 规则参考 Microsoft Learn RIFF 文档；`WAVEFORMATEX` 字段公式参考 Microsoft Learn；`bext` 的 Broadcast Wave 背景参考 EBU Tech 3285。
