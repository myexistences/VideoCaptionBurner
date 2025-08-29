# project/caption_builder.py
import re

def build_caption_units(data,
                        max_words_per_line=5,
                        max_words_per_caption=10,
                        continue_if_gap_ms=200,
                        separate_if_gap_ms=600):
    """
    Build caption units obeying precise pause rules.

    Rules (defaults):
      - gap < continue_if_gap_ms  => continue the same caption line
      - continue_if_gap_ms <= gap < separate_if_gap_ms => end current caption and start a new one
      - gap >= separate_if_gap_ms => end/flush current caption (caption vanishes during gap) and start a new caption

    Preserves per-word timestamps and returns captions with:
      - 'start' (float seconds)
      - 'end' (float seconds)
      - 'text_ass' (always single line, no \\N)
      - 'text_srt' (always single line, no \\n)
      - 'words' list of (word, start, end)
    """
    captions = []

    # convert thresholds to seconds
    cont_th = float(continue_if_gap_ms) / 1000.0
    sep_th = float(separate_if_gap_ms) / 1000.0

    def flush(curr):
        """Flush a current caption (list of (word, s, e))."""
        if not curr:
            return
        start = None
        end = None
        words_for_meta = []
        words = []
        for item in curr:
            # item is (word, s, e)
            w, s, e = item
            if start is None:
                start = float(s)
            end = float(e)
            words.append(w)
            words_for_meta.append((w, float(s), float(e)))

        if start is None or end is None:
            return

        captions.append({
            'start': float(start),
            'end': float(end),
            'text_ass': ' '.join(words),   # always one line
            'text_srt': ' '.join(words),   # always one line
            'words': words_for_meta
        })

    # determine if segments have per-word timestamps
    any_words = any('words' in seg and seg['words'] for seg in data.get('segments', []))
    if not any_words:
        # fallback: distribute segment timestamps evenly as older behavior
        current = []
        last_end = None
        for seg in data.get('segments', []):
            seg_text = seg.get('text', '').strip()
            if not seg_text:
                continue
            seg_start = float(seg.get('start', 0.0))
            seg_end = float(seg.get('end', seg_start))
            seg_words = [w for w in re.split(r"\s+", seg_text) if w]
            if not seg_words:
                continue
            per_word = (seg_end - seg_start) / max(1, len(seg_words))
            for i, w in enumerate(seg_words):
                s = seg_start + i * per_word
                e = s + per_word
                gap = 0 if last_end is None else s - last_end
                # flush if big gap or caption too long
                if gap >= sep_th or len(current) >= max_words_per_caption:
                    flush(current)
                    current = []
                # medium gap: also flush (instead of line break)
                elif last_end is not None and cont_th <= gap < sep_th and current:
                    flush(current)
                    current = []
                current.append((w, s, e))
                last_end = e
        flush(current)
        return captions

    # With per-word timestamps:
    current = []
    last_end = None
    words_in_current = 0
    for seg in data.get('segments', []):
        for w in seg.get('words', []):
            word_text = (w.get('word') or '').strip()
            if not word_text:
                continue
            try:
                w_start = float(w.get('start', 0.0))
                w_end = float(w.get('end', w_start))
            except Exception:
                continue

            gap = 0 if last_end is None else (w_start - last_end)

            # if gap >= separate threshold -> end current caption and start a new one
            if last_end is not None and gap >= sep_th:
                flush(current)
                current = []
                words_in_current = 0

            # if adding this word would exceed max words per caption, flush and start new
            if words_in_current >= max_words_per_caption:
                flush(current)
                current = []
                words_in_current = 0

            # moderate gaps: instead of line-break, flush caption and start new
            if last_end is not None and cont_th <= gap < sep_th and current:
                flush(current)
                current = []
                words_in_current = 0

            # add the word
            current.append((word_text, w_start, w_end))
            words_in_current += 1

            # enforce per-line maximum: instead of line-break, flush caption
            rev = list(reversed(current))
            count_since_break = 0
            for it in rev:
                count_since_break += 1
            if count_since_break >= max_words_per_line:
                if words_in_current < max_words_per_caption:
                    flush(current)
                    current = []
                    words_in_current = 0

            # strong punctuation heuristic: if the word ends a sentence, flush immediately
            if re.search(r'[\.!\?]$', word_text):
                flush(current)
                current = []
                words_in_current = 0

            last_end = w_end

    flush(current)
    return captions
